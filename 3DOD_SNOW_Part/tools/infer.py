import os
import numpy as np
import torch
import spconv.pytorch as spconv
import open3d as o3d
from tqdm import tqdm
from multiprocessing import Pool, set_start_method
import warnings
warnings.filterwarnings("ignore")

from train import SparseUNetMultiPoint

# ==========================================
global_model = None
global_device = None
global_pc_range = None
global_grid_size = None
global_voxel_size = None
global_num_points = 3 # default N=3

def init_worker(model_path):
    global global_model, global_device, global_pc_range, global_grid_size, global_voxel_size, global_num_points
    
    global_device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    global_grid_size = [40, 800, 704]
    
    global_model = SparseUNetMultiPoint(spatial_shape=global_grid_size, in_channels=4, num_points_per_voxel=global_num_points).to(global_device)
    global_model.load_state_dict(torch.load(model_path, map_location=global_device))
    global_model.eval()
    
    global_voxel_size = 0.1
    global_pc_range = [0, -40, -3, 70.4, 40, 1]

def process_frame(args):
    frame, snow_dir, out_dir = args
    snow_path = os.path.join(snow_dir, frame)
    out_path = os.path.join(out_dir, frame)

    try:
        pts = np.fromfile(snow_path, dtype=np.float32).reshape(-1, 4)
        
        mask = (pts[:, 0] >= global_pc_range[0]) & (pts[:, 0] < global_pc_range[3]) & \
               (pts[:, 1] >= global_pc_range[1]) & (pts[:, 1] < global_pc_range[4]) & \
               (pts[:, 2] >= global_pc_range[2]) & (pts[:, 2] < global_pc_range[5])
        pts_filtered = pts[mask]

        # preparing data
        coords = np.floor((pts_filtered[:, :3] - global_pc_range[:3]) / global_voxel_size).astype(np.int32)
        max_indices = np.array(global_grid_size, dtype=np.int32)[::-1] - 1
        coords = np.clip(coords, a_min=0, a_max=max_indices)
        
        unique_coords, inverse_indices, counts = np.unique(coords, axis=0, return_inverse=True, return_counts=True)
        
        dists = np.linalg.norm(pts_filtered[:, :3], axis=1)
        mean_dist = (np.bincount(inverse_indices, weights=dists) / counts) / 70.0
        
        features_np = np.stack([
            np.clip(counts / 20.0, 0, 1.0),
            np.bincount(inverse_indices, weights=pts_filtered[:, 3]) / counts,
            (np.bincount(inverse_indices, weights=pts_filtered[:, 2]) / counts - global_pc_range[2]) / (global_pc_range[5] - global_pc_range[2]),
            mean_dist
        ], axis=1).astype(np.float32)

        # infer Multi-point 
        with torch.no_grad():
            features = torch.from_numpy(features_np).to(global_device)
            unique_coords = unique_coords[:, [2, 1, 0]]
            b_idx = torch.zeros((unique_coords.shape[0], 1), dtype=torch.int32)
            coords_tensor = torch.cat([b_idx, torch.from_numpy(unique_coords.astype(np.int32))], dim=1).to(torch.int32).to(global_device)
            
            pred_sparse = global_model(features, coords_tensor, batch_size=1)
            
            probs_occ = torch.sigmoid(pred_sparse.features[:, 0])
            valid_mask = probs_occ > 0.4 
            valid_indices = pred_sparse.indices[valid_mask] 

            if len(valid_indices) == 0:
                pts_filtered.astype(np.float32).tofile(out_path)
                return True

            valid_features = pred_sparse.features[valid_mask, 1:].view(-1, global_num_points, 4)
            pred_offsets = torch.tanh(valid_features[:, :, :3]).cpu().numpy() * 0.5
            pred_intensities = np.clip(valid_features[:, :, 3].cpu().numpy(), 0.0, 1.0)

        # Broadcasting
        z_idx = valid_indices[:, 1].float().cpu().numpy()
        y_idx = valid_indices[:, 2].float().cpu().numpy()
        x_idx = valid_indices[:, 3].float().cpu().numpy()

        base_coords = np.stack([x_idx + 0.5, y_idx + 0.5, z_idx + 0.5], axis=-1)[:, None, :]
        gen_coords = (base_coords + pred_offsets) * global_voxel_size + np.array(global_pc_range[:3])
        generated_pts = gen_coords.reshape(-1, 3)
        pred_intensities = pred_intensities.reshape(-1)

        # 4. post processing : HPR and filtering
        pcd_gen = o3d.geometry.PointCloud()
        pcd_gen.points = o3d.utility.Vector3dVector(generated_pts)
        _, pt_map = pcd_gen.hidden_point_removal([0, 0, 0], 1000.0)
        generated_pts, pred_intensities = generated_pts[pt_map], pred_intensities[pt_map]

        topology_mask = (generated_pts[:, 2] > -1.65) & (generated_pts[:, 2] < 3.0)
        valid_generated_pts = generated_pts[topology_mask]
        valid_intensities = pred_intensities[topology_mask]

        # save
        if len(valid_generated_pts) > 0:
            gen_full = np.hstack((valid_generated_pts, valid_intensities[:, None]))
            augmented_pts_3d = np.vstack((pts_filtered, gen_full))
        else:
            augmented_pts_3d = pts_filtered

        np.unique(augmented_pts_3d, axis=0).astype(np.float32).tofile(out_path)
        return True
    
    except Exception as e:
        print(f"\n[error - {frame}] {e}")
        return False

def generate_augmented_point_cloud_mp(model_path, snow_dir, out_dir, num_workers=12):
    os.makedirs(out_dir, exist_ok=True)
    frames = sorted([f for f in os.listdir(snow_dir) if f.endswith('.bin')])
    
    try:
        set_start_method('spawn', force=True)
    except RuntimeError:
        pass
        
    print(f"🚀 Inference (Multi-processing: {num_workers} workers)")
    args_list = [(frame, snow_dir, out_dir) for frame in frames]

    with Pool(processes=num_workers, initializer=init_worker, initargs=(model_path,)) as pool:
        list(tqdm(pool.imap_unordered(process_frame, args_list), total=len(frames), desc="Augmenting", unit="frame"))
        
    print("\n🎉 complete!")

if __name__ == "__main__":
    model_path = './checkpoints/best_model.pth'
    generate_augmented_point_cloud_mp(model_path, './training/snow_velodyne', './infer_velodyne', num_workers=12)