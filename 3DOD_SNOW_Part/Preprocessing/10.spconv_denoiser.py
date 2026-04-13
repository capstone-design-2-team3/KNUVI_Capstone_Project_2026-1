import os
import glob
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import spconv.pytorch as spconv
from scipy.spatial import cKDTree
from tqdm import tqdm
import torch.nn.functional as F

class FocalLoss(nn.Module):
    def __init__(self, alpha=0.75, gamma=2.0): # alpha: Foreground 가중치 높임
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, inputs, targets):
        bce_loss = F.binary_cross_entropy_with_logits(inputs, targets, reduction='none')
        pt = torch.exp(-bce_loss)
        focal_loss = self.alpha * (1-pt)**self.gamma * bce_loss
        return focal_loss.mean()
    
# =========================================================
# 1. Dataset & Auto-Labeling (Snow vs Clean)
# =========================================================
class SnowKITTIDataset(Dataset):
    def __init__(self, snow_dir, clean_dir, mode='train'):
        self.snow_files = sorted(glob.glob(os.path.join(snow_dir, '*.bin')))
        self.clean_dir = clean_dir
        self.mode = mode
        
        # KITTI Voxelization Range & Size (VoxelRCNN과 동일하게 맞추는 것이 좋습니다)
        self.pc_range = np.array([0, -40, -3, 70.4, 40, 1])
        self.voxel_size = np.array([0.05, 0.05, 0.1])
        self.grid_size = np.round((self.pc_range[3:] - self.pc_range[:3]) / self.voxel_size).astype(np.int32)

    def __len__(self):
        return len(self.snow_files)

    def generate_labels(self, snow_pts, clean_pts):
        """
        cKDTree를 사용하여 Snow 포인트 클라우드에서 Clean에 없는 포인트를 눈송이(노이즈)로 라벨링
        0: Background/Noise (눈송이) / 1: Foreground (유효 포인트)
        """
        tree = cKDTree(clean_pts[:, :3])
        # k=1 최단거리 검색, distance_upper_bound로 임계값(예: 5cm) 설정
        distances, _ = tree.query(snow_pts[:, :3], k=1, distance_upper_bound=0.05)
        
        labels = np.ones(snow_pts.shape[0], dtype=np.int64)
        labels[distances == np.inf] = 0 # 임계값 밖의 포인트는 노이즈
        return labels

    def __getitem__(self, idx):
        snow_path = self.snow_files[idx]
        file_name = os.path.basename(snow_path)
        clean_path = os.path.join(self.clean_dir, file_name)

        snow_scan = np.fromfile(snow_path, dtype=np.float32).reshape(-1, 4)
        
        # Point to Voxel 변환 로직
        # 1. 범위를 벗어나는 포인트 제거
        mask = (snow_scan[:, 0] >= self.pc_range[0]) & (snow_scan[:, 0] <= self.pc_range[3]) & \
               (snow_scan[:, 1] >= self.pc_range[1]) & (snow_scan[:, 1] <= self.pc_range[4]) & \
               (snow_scan[:, 2] >= self.pc_range[2]) & (snow_scan[:, 2] <= self.pc_range[5])
        
        snow_pts = snow_scan[mask]
        
        # 2. Voxel Index 계산
        coords = np.floor((snow_pts[:, :3] - self.pc_range[:3]) / self.voxel_size).astype(np.int32)
        # spconv는 (Z, Y, X) 순서의 coords를 선호함
        coords = coords[:, [2, 1, 0]]
        
        # 학습 시에는 라벨 생성
        if self.mode == 'train':
            clean_scan = np.fromfile(clean_path, dtype=np.float32).reshape(-1, 4)
            labels = self.generate_labels(snow_pts, clean_scan)
        else:
            labels = np.zeros(snow_pts.shape[0]) # Inference 땐 더미 라벨

        # Unique Voxel 및 Point-to-Voxel 매핑
        unique_coords, inverse_indices = np.unique(coords, axis=0, return_inverse=True)
        
        # Voxel별 Feature (평균 계산 대신 간단히 첫 포인트 feature 사용 혹은 평균화)
        # 이 예시에서는 단순화를 위해 Voxel 좌표 자체를 초기 Feature로 사용
        # 1. 배열 초기화 (Voxel 개수 x 3채널)
        voxel_features_np = np.zeros((len(unique_coords), 3), dtype=np.float32)
        
        # Channel 0: Z_coord (높이 정보)
        voxel_features_np[:, 0] = unique_coords[:, 0] 
        
        # 각 Voxel에 속한 포인트 개수 계산 (bincount 활용)
        counts = np.bincount(inverse_indices)
        
        # Channel 2: Density (밀도 정규화)
        voxel_features_np[:, 2] = counts / 50.0 
        
        # Channel 1: Mean_Intensity (반사율 합계를 개수로 나눔)
        sum_intensity = np.bincount(inverse_indices, weights=snow_pts[:, 3])
        # 0으로 나누는 에러 방지를 위해 np.maximum 사용
        voxel_features_np[:, 1] = sum_intensity / np.maximum(counts, 1) 
        
        voxel_features = torch.tensor(voxel_features_np, dtype=torch.float32)
        voxel_coords = torch.tensor(unique_coords, dtype=torch.int32)
        
        # 배치 처리를 위한 Batch Index (여기선 0 고정, DataLoader collate_fn에서 수정)
        voxel_coords = torch.cat([torch.zeros((voxel_coords.shape[0], 1), dtype=torch.int32), voxel_coords], dim=1)

        return {
            'file_name': file_name,
            'original_scan': snow_scan,
            'valid_mask': mask,
            'voxel_features': voxel_features,
            'voxel_coords': voxel_coords,
            'inverse_indices': torch.tensor(inverse_indices, dtype=torch.long),
            'point_labels': torch.tensor(labels, dtype=torch.float32)
        }

# =========================================================
# 2. 3D Sparse U-Net Model (spconv)
# =========================================================
class SparseDenoiseUNet(nn.Module):
    def __init__(self, spatial_shape):
        super().__init__()
        self.sparse_shape = spatial_shape
        
        # Encoder
        self.conv1 = spconv.SparseSequential(
            spconv.SubMConv3d(3, 16, 3, padding=1, bias=False, indice_key="subm1"),
            nn.BatchNorm1d(16), nn.ReLU()
        )
        # Downsample: 여기서 압축되는 Voxel들의 인덱스 매핑을 "spconv_down1"이라는 키로 저장합니다.
        self.down1 = spconv.SparseSequential(
            spconv.SparseConv3d(16, 32, 3, stride=2, padding=1, bias=False, indice_key="spconv_down1"),
            nn.BatchNorm1d(32), nn.ReLU()
        )
        
        # Decoder
        # Upsample: "spconv_down1" 키를 불러와서, 다운샘플링 되었던 과정을 완벽하게 역추적하여 복원합니다.
        self.up1 = spconv.SparseSequential(
            spconv.SparseInverseConv3d(32, 16, 3, bias=False, indice_key="spconv_down1"),
            nn.BatchNorm1d(16), nn.ReLU()
        )
        
        # Output classification (Voxel 단위)
        self.out_conv = spconv.SubMConv3d(16, 1, 1, indice_key="subm_out")

    def forward(self, voxel_features, voxel_coords, batch_size=1):
        x = spconv.SparseConvTensor(voxel_features, voxel_coords, self.sparse_shape, batch_size)
        
        x1 = self.conv1(x)
        x_down = self.down1(x1)
        x_up = self.up1(x_down)
        
        # Voxelwise Logits
        out = self.out_conv(x_up)
        return out.features
    
# =========================================================
# 3. Training & Inference Process
# =========================================================
def run_denoising_pipeline(snow_dir, clean_dir, out_dir, mode='inference', weights_path='denoiser.pth'):
    os.makedirs(out_dir, exist_ok=True)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    dataset = SnowKITTIDataset(snow_dir, clean_dir, mode=mode)
    
    # Grid Size (Z, Y, X)
    spatial_shape = dataset.grid_size[[2, 1, 0]].tolist()
    model = SparseDenoiseUNet(spatial_shape).to(device)
    
    if mode == 'train':
        model.train()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = FocalLoss(alpha=0.75, gamma=2.0)
        
        print("🚀 모델 학습을 시작합니다...")
        for epoch in range(5): # 예시 에폭
            for data in tqdm(dataset):
                v_feat = data['voxel_features'].to(device)
                v_coord = data['voxel_coords'].to(device)
                p_labels = data['point_labels'].to(device)
                inv_idx = data['inverse_indices'].to(device)
                
                optimizer.zero_grad()
                voxel_logits = model(v_feat, v_coord)
                
                # Voxel의 예측값을 원래 Point 단위로 복원 (Broadcasting)
                point_logits = voxel_logits[inv_idx].squeeze()
                
                loss = criterion(point_logits, p_labels)
                loss.backward()
                optimizer.step()
                
            print(f"Epoch {epoch+1} Loss: {loss.item():.4f}")
        torch.save(model.state_dict(), weights_path)
        print("✅ 학습 완료 및 가중치 저장됨.")

    elif mode == 'inference':
        model.load_state_dict(torch.load(weights_path))
        model.eval()
        
        print("🚀 Denoising 추론 및 .bin 저장을 시작합니다...")
        with torch.no_grad():
            for data in tqdm(dataset):
                v_feat = data['voxel_features'].to(device)
                v_coord = data['voxel_coords'].to(device)
                inv_idx = data['inverse_indices'].to(device)
                original_scan = data['original_scan']
                valid_mask = data['valid_mask']
                
                voxel_logits = model(v_feat, v_coord)
                point_logits = voxel_logits[inv_idx].squeeze()
                
                # Sigmoid를 거쳐 확률이 0.5 이상인 포인트(객체/배경)만 살림
                point_probs = torch.sigmoid(point_logits)
                keep_idx = point_probs > 0.5
                
                # 원본 scan에서 Range 밖이거나 노이즈로 판별된 것 제외
                denoised_scan = original_scan[valid_mask][keep_idx.cpu().numpy()]
                
                out_path = os.path.join(out_dir, data['file_name'])
                denoised_scan.tofile(out_path)

if __name__ == '__main__':
    SNOW_DIR = './training/velodyne'
    CLEAN_DIR = '../kitti/training/velodyne'
    OUT_DIR = './denoised_velodyne'
    
    # 1. 학습할 때 주석 해제
    # run_denoising_pipeline(SNOW_DIR, CLEAN_DIR, OUT_DIR, mode='train')
    
    # 2. 추론하여 Denoised Point Cloud 추출할 때
    run_denoising_pipeline(SNOW_DIR, CLEAN_DIR, OUT_DIR, mode='inference')