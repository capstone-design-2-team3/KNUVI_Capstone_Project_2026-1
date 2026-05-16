import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, random_split
import spconv.pytorch as spconv
from tqdm import tqdm

# ==========================================
# 0. KITTI Calib & Label Helper
# ==========================================
def load_kitti_calib(calib_path):
    with open(calib_path, 'r') as f:
        lines = f.readlines()
    calib = {}
    for line in lines:
        if not line.strip(): continue
        key, value = line.split(':', 1)
        calib[key] = np.array([float(x) for x in value.split()]).reshape(-1)
    R0_rect = np.eye(4)
    R0_rect[:3, :3] = calib['R0_rect'].reshape(3, 3)
    Tr_velo_to_cam = np.eye(4)
    Tr_velo_to_cam[:3, :4] = calib['Tr_velo_to_cam'].reshape(3, 4)
    return R0_rect, Tr_velo_to_cam

def get_velo_box_corners(x, y, z, h, w, l, ry, R0_rect, Tr_velo_to_cam):
    R = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
    corners_3d = np.dot(R, np.vstack([
        [l/2, l/2, -l/2, -l/2, l/2, l/2, -l/2, -l/2],
        [0, 0, 0, 0, -h, -h, -h, -h],
        [w/2, -w/2, -w/2, w/2, w/2, -w/2, -w/2, w/2]
    ])).T + np.array([x, y, z])
    corners_hom = np.hstack((corners_3d, np.ones((8, 1))))
    R0_inv = np.linalg.inv(R0_rect)
    Tr_inv = np.linalg.inv(Tr_velo_to_cam)
    corners_velo = (Tr_inv @ R0_inv @ corners_hom.T).T
    return corners_velo[:, :3]

# ==========================================
# 1. Dataset (GT Multi-point Padding)
# ==========================================
class KittiSnowCompletionDataset(Dataset):
    def __init__(self, raw_dir, snow_dir, label_dir, calib_dir, voxel_size=0.1, point_cloud_range=[0, -40, -3, 70.4, 40, 1], max_pts_per_voxel=5):
        self.raw_dir, self.snow_dir, self.label_dir, self.calib_dir = raw_dir, snow_dir, label_dir, calib_dir
        self.voxel_size = np.array([voxel_size]*3, dtype=np.float32)
        self.pc_range = np.array(point_cloud_range, dtype=np.float32)
        self.max_pts = max_pts_per_voxel
        self.frames = sorted([f for f in os.listdir(snow_dir) if f.endswith('.bin')])
        self.grid_size = np.round((self.pc_range[3:] - self.pc_range[:3]) / self.voxel_size).astype(np.int32)[::-1]

    def __len__(self): return len(self.frames)

    def extract_features(self, points):
        mask = (points[:, 0] >= self.pc_range[0]) & (points[:, 0] < self.pc_range[3]) & \
               (points[:, 1] >= self.pc_range[1]) & (points[:, 1] < self.pc_range[4]) & \
               (points[:, 2] >= self.pc_range[2]) & (points[:, 2] < self.pc_range[5])
        points = points[mask]
        coords = np.floor((points[:, :3] - self.pc_range[:3]) / self.voxel_size).astype(np.int32)
        unique_coords, inv, counts = np.unique(coords, axis=0, return_inverse=True, return_counts=True)
        
        feats = np.stack([
            np.clip(counts/20.0, 0, 1),
            np.bincount(inv, weights=points[:, 3]) / counts,
            (np.bincount(inv, weights=points[:, 2]) / counts - self.pc_range[2]) / (self.pc_range[5]-self.pc_range[2]),
            (np.bincount(inv, weights=np.linalg.norm(points[:,:3], axis=1)) / counts) / 70.0
        ], axis=1).astype(np.float32)
        return unique_coords[:, [2, 1, 0]], feats

    def __getitem__(self, idx):
        frame = self.frames[idx]
        frame_id = frame.split('.')[0]
        snow_pts = np.fromfile(os.path.join(self.snow_dir, frame), dtype=np.float32).reshape(-1, 4)
        raw_pts = np.fromfile(os.path.join(self.raw_dir, frame), dtype=np.float32).reshape(-1, 4)
        
        snow_coords, snow_feats = self.extract_features(snow_pts)
        
        mask = (raw_pts[:, 0] >= self.pc_range[0]) & (raw_pts[:, 0] < self.pc_range[3]) & \
               (raw_pts[:, 1] >= self.pc_range[1]) & (raw_pts[:, 1] < self.pc_range[4]) & \
               (raw_pts[:, 2] >= self.pc_range[2]) & (raw_pts[:, 2] < self.pc_range[5])
        raw_pts_f = raw_pts[mask]
        raw_coords_float = (raw_pts_f[:, :3] - self.pc_range[:3]) / self.voxel_size
        raw_coords_int = np.floor(raw_coords_float).astype(np.int32)
        
        unique_raw, inv = np.unique(raw_coords_int, axis=0, return_inverse=True)
        
        gt_offsets = np.zeros((len(unique_raw), self.max_pts, 3), dtype=np.float32)
        gt_intensities = np.zeros((len(unique_raw), self.max_pts), dtype=np.float32)
        gt_mask = np.zeros((len(unique_raw), self.max_pts), dtype=bool)
        
        counts = np.zeros(len(unique_raw), dtype=np.int32)
        offsets_f = raw_coords_float - (raw_coords_int + 0.5)
        
        for i, u_idx in enumerate(inv):
            c = counts[u_idx]
            if c < self.max_pts:
                gt_offsets[u_idx, c] = offsets_f[i]
                gt_intensities[u_idx, c] = raw_pts_f[i, 3]
                gt_mask[u_idx, c] = True
                counts[u_idx] += 1
        
        # Class-aware Weighting
        fg_weight = np.ones(self.grid_size, dtype=np.float32)
        class_weights = {'Car': 1.0, 'Pedestrian': 2.0, 'Cyclist': 5.0}
        
        calib_path = os.path.join(self.calib_dir, f"{frame_id}.txt")
        label_path = os.path.join(self.label_dir, f"{frame_id}.txt")
        if os.path.exists(calib_path) and os.path.exists(label_path):
            R0, Tr = load_kitti_calib(calib_path)
            with open(label_path, 'r') as f:
                for line in f.readlines():
                    p = line.split()
                    cls = p[0]
                    if cls not in class_weights: continue
                    weight = class_weights[cls]
                    corners = get_velo_box_corners(float(p[11]), float(p[12]), float(p[13]), 
                                                   float(p[8]), float(p[9]), float(p[10]), float(p[14]), R0, Tr)
                    c_vox = np.floor((corners - self.pc_range[:3]) / self.voxel_size).astype(np.int32)
                    min_v = np.clip(np.min(c_vox, axis=0), 0, self.grid_size[::-1]-1)
                    max_v = np.clip(np.max(c_vox, axis=0), 0, self.grid_size[::-1]-1)
                    fg_weight[min_v[2]:max_v[2]+1, min_v[1]:max_v[1]+1, min_v[0]:max_v[0]+1] = np.maximum(
                        fg_weight[min_v[2]:max_v[2]+1, min_v[1]:max_v[1]+1, min_v[0]:max_v[0]+1], weight
                    )

        return {
            'snow_coords': torch.from_numpy(snow_coords), 'snow_features': torch.from_numpy(snow_feats),
            'raw_coords': torch.from_numpy(unique_raw[:, [2,1,0]]), 
            'gt_offsets': torch.from_numpy(gt_offsets), 
            'gt_intensities': torch.from_numpy(gt_intensities),
            'gt_mask': torch.from_numpy(gt_mask),
            'fg_weight': torch.from_numpy(fg_weight)
        }

def sparse_collate_fn(batch):
    res = {'snow_coords': [], 'snow_features': [], 'raw_coords': [], 'gt_offsets': [], 'gt_intensities': [], 'gt_mask': [], 'fg_weight': []}
    for i, item in enumerate(batch):
        for k in ['snow_coords', 'raw_coords']:
            res[k].append(torch.cat([torch.full((item[k].shape[0], 1), i, dtype=torch.int32), item[k]], dim=1))
        for k in ['snow_features', 'gt_offsets', 'gt_intensities', 'gt_mask']: res[k].append(item[k])
        res['fg_weight'].append(item['fg_weight'])
    return {k: (torch.cat(v) if k != 'fg_weight' else torch.stack(v)) for k, v in res.items()} | {'batch_size': len(batch)}

# ==========================================
# 2. Sparse UNet (Multi-point Output)
# ==========================================
class SparseUNetMultiPoint(nn.Module):
    def __init__(self, spatial_shape, in_channels=4, num_points_per_voxel=3):
        super().__init__()
        self.spatial_shape = spatial_shape
        self.num_points = num_points_per_voxel
        # Occupancy(1) + N * (X, Y, Z, Intensity)
        out_channels = 1 + (self.num_points * 4) 
        
        self.enc0 = spconv.SparseSequential(spconv.SubMConv3d(in_channels, 16, 3, padding=1, indice_key="subm0"), nn.BatchNorm1d(16), nn.ReLU())
        self.down1 = spconv.SparseSequential(spconv.SparseConv3d(16, 32, 3, 2, 1, indice_key="spconv1"), nn.BatchNorm1d(32), nn.ReLU())
        self.enc1 = spconv.SparseSequential(spconv.SubMConv3d(32, 32, 3, padding=1, indice_key="subm1"), nn.BatchNorm1d(32), nn.ReLU())
        self.down2 = spconv.SparseSequential(spconv.SparseConv3d(32, 64, 3, 2, 1, indice_key="spconv2"), nn.BatchNorm1d(64), nn.ReLU())
        self.enc2 = spconv.SparseSequential(spconv.SubMConv3d(64, 64, 3, padding=1, indice_key="subm2"), nn.BatchNorm1d(64), nn.ReLU())
        
        self.up1 = spconv.SparseSequential(spconv.SparseInverseConv3d(64, 32, 3, indice_key="spconv2"), nn.BatchNorm1d(32), nn.ReLU())
        self.up_conv1 = spconv.SparseSequential(spconv.SubMConv3d(64, 32, 3, padding=1, indice_key="subm1"), nn.BatchNorm1d(32), nn.ReLU())
        self.up2 = spconv.SparseSequential(spconv.SparseInverseConv3d(32, 16, 3, indice_key="spconv1"), nn.BatchNorm1d(16), nn.ReLU())
        self.up_conv2 = spconv.SparseSequential(spconv.SubMConv3d(32, 16, 3, padding=1, indice_key="subm0"), nn.BatchNorm1d(16), nn.ReLU())
        self.final = spconv.SparseConv3d(16, out_channels, 3, padding=1)

    def forward(self, feats, coords, batch_size):
        x = spconv.SparseConvTensor(feats, coords, self.spatial_shape, batch_size)
        x0 = self.enc0(x)
        x1 = self.enc1(self.down1(x0))
        x2 = self.enc2(self.down2(x1))
        
        u1 = self.up1(x2)
        u1_cat = u1.replace_feature(torch.cat([u1.features, x1.features], dim=1))
        u1_out = self.up_conv1(u1_cat)
        u2 = self.up2(u1_out)
        u2_cat = u2.replace_feature(torch.cat([u2.features, x0.features], dim=1))
        u2_out = self.up_conv2(u2_cat)
        return self.final(u2_out)

# ==========================================
# 3. Truncated Chamfer Distance Loss
# ==========================================
def compute_multi_point_loss(pred_sparse, gt_coords, gt_off, gt_int, gt_mask, fg_weights, num_points=3, tau=0.2):
    pred_feats = pred_sparse.features
    pred_coords = pred_sparse.indices
    S = pred_sparse.spatial_shape

    def encode(c):
        c = c.long()
        return c[:,0]*S[0]*S[1]*S[2] + c[:,1]*S[1]*S[2] + c[:,2]*S[2] + c[:,3]

    p_idx = encode(pred_coords)
    g_idx = encode(gt_coords)

    is_gt = torch.isin(p_idx, g_idx)
    p_occ = pred_feats[:, 0]
    t_occ = is_gt.float()
    
    b, z, y, x = pred_coords[:, 0].long(), pred_coords[:, 1].long(), pred_coords[:, 2].long(), pred_coords[:, 3].long()
    per_voxel_weight = fg_weights[b, z, y, x]
    
    bce = F.binary_cross_entropy_with_logits(p_occ, t_occ, reduction='none')
    loss_occ = (per_voxel_weight * (1 - torch.exp(-bce))**2 * bce).mean()

    if not is_gt.any(): return loss_occ

    sort_g = torch.argsort(g_idx)
    g_idx_s, gt_off_s, gt_int_s, gt_mask_s = g_idx[sort_g], gt_off[sort_g], gt_int[sort_g], gt_mask[sort_g]
    
    pos = torch.searchsorted(g_idx_s, p_idx[is_gt]).clamp(max=g_idx_s.shape[0]-1)
    valid = (g_idx_s[pos] == p_idx[is_gt])
    if not valid.any(): return loss_occ

    reg_weight = per_voxel_weight[is_gt][valid]
    
    pred_valid_feats = pred_feats[is_gt][valid, 1:].view(-1, num_points, 4)
    pred_off = torch.tanh(pred_valid_feats[:, :, :3]) * 0.5  # (V, N, 3)
    pred_i = pred_valid_feats[:, :, 3]                       # (V, N)
    
    gt_off_m = gt_off_s[pos[valid]]     # (V, M, 3)
    gt_i_m = gt_int_s[pos[valid]]       # (V, M)
    mask_m = gt_mask_s[pos[valid]]      # (V, M) boolean

    # --- Truncated Chamfer Distance ---
    # pred_off: (V, N, 3) / gt_off_m: (V, M, 3)
    dist_matrix = torch.cdist(pred_off, gt_off_m, p=2) ** 2 # (V, N, M)
    dist_matrix = torch.clamp(dist_matrix, max=tau)         # Truncation
    
    dist_matrix_masked = dist_matrix.clone()
    dist_matrix_masked[~mask_m.unsqueeze(1).expand(-1, num_points, -1)] = 1e6
    min_dist_pred_to_gt, matched_gt_indices = torch.min(dist_matrix_masked, dim=2) # (V, N)
    min_dist_gt_to_pred, _ = torch.min(dist_matrix, dim=1) # (V, M)
    
    loss_cd_p2g = (min_dist_pred_to_gt.mean(dim=1) * reg_weight).mean()
    valid_gt_counts = mask_m.sum(dim=1).clamp(min=1) 
    loss_cd_g2p = (((min_dist_gt_to_pred * mask_m).sum(dim=1) / valid_gt_counts) * reg_weight).mean()
    
    loss_cd = loss_cd_p2g + loss_cd_g2p
    
    # --- Intensity Loss ---
    matched_gt_i = torch.gather(gt_i_m, 1, matched_gt_indices) # (V, N)
    loss_int = (reg_weight.unsqueeze(1) * F.smooth_l1_loss(pred_i, matched_gt_i, reduction='none')).mean()

    return loss_occ + loss_cd + loss_int

# ==========================================
# 4. Training
# ==========================================
def train():
    device = torch.device('cuda')
    os.makedirs("./checkpoints", exist_ok=True)
    
    full_dataset = KittiSnowCompletionDataset(
        "./training/velodyne", # raw kitti velodyne
        "./training/snow_velodyne", 
        "./training/label_2", 
        "./training/calib",
        max_pts_per_voxel=5
    )
    
    train_size = int(0.8 * len(full_dataset))
    train_ds, val_ds = random_split(full_dataset, [train_size, len(full_dataset) - train_size])
    train_loader = DataLoader(train_ds, batch_size=4, shuffle=True, collate_fn=sparse_collate_fn, num_workers=4)
    val_loader = DataLoader(val_ds, batch_size=4, shuffle=False, collate_fn=sparse_collate_fn, num_workers=4)

    model = SparseUNetMultiPoint(full_dataset.grid_size, num_points_per_voxel=3).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=50, eta_min=1e-5)
    
    best_val_loss = float('inf')

    for epoch in range(10):
        # epoch default = 50
        
        model.train()
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/50")
        for batch in pbar:
            optimizer.zero_grad()
            pred = model(batch['snow_features'].to(device), batch['snow_coords'].to(device), batch['batch_size'])
            loss = compute_multi_point_loss(pred, batch['raw_coords'].to(device), batch['gt_offsets'].to(device), 
                                            batch['gt_intensities'].to(device), batch['gt_mask'].to(device), batch['fg_weight'].to(device))
            loss.backward()
            optimizer.step()
            pbar.set_postfix(loss=f"{loss.item():.4f}")

        model.eval()
        val_loss = 0
        with torch.no_grad():
            for batch in val_loader:
                pred = model(batch['snow_features'].to(device), batch['snow_coords'].to(device), batch['batch_size'])
                val_loss += compute_multi_point_loss(pred, batch['raw_coords'].to(device), batch['gt_offsets'].to(device), 
                                                     batch['gt_intensities'].to(device), batch['gt_mask'].to(device), batch['fg_weight'].to(device)).item()
        
        avg_val_loss = val_loss / len(val_loader)
        print(f"Val Loss: {avg_val_loss:.4f}")
        
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            torch.save(model.state_dict(), "./checkpoints/best_model.pth")
            print(f"✨ New best model saved (Epoch {epoch+1})")
        
        scheduler.step()

if __name__ == "__main__":
    train()
