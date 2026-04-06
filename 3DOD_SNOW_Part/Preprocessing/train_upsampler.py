import os
import glob
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

# ==========================================
# 1. 딥러닝 기반 Point Cloud Upsampling 모델
# ==========================================
class MiniPointUpsampler(nn.Module):
    def __init__(self, up_ratio=4):
        super(MiniPointUpsampler, self).__init__()
        self.r = up_ratio
        
        self.mlp1 = nn.Sequential(
            nn.Conv1d(3, 64, 1), nn.ReLU(),
            nn.Conv1d(64, 128, 1), nn.ReLU(),
            nn.Conv1d(128, 256, 1)
        )
        self.mlp2 = nn.Sequential(
            nn.Conv1d(256 + 3, 256, 1), nn.ReLU(),
            nn.Conv1d(256, 3 * up_ratio, 1)
        )

    def forward(self, x):
        B, C, N = x.size()
        global_feat = torch.max(self.mlp1(x), dim=2, keepdim=True)[0]
        global_feat = global_feat.expand(-1, -1, N)
        concat_feat = torch.cat([x, global_feat], dim=1)
        
        out = self.mlp2(concat_feat)
        out = out.view(B, 3, N * self.r)
        return out

# ==========================================
# 2. 손실 함수: Chamfer Distance (순수 PyTorch 버전)
# ==========================================
def chamfer_distance(p1, p2):
    """
    p1: (B, 3, N), p2: (B, 3, M)
    두 포인트 클라우드 간의 기하학적 유사도를 측정합니다.
    """
    p1 = p1.transpose(1, 2) # (B, N, 3)
    p2 = p2.transpose(1, 2) # (B, M, 3)
    
    # 메모리 효율을 위해 브로드캐스팅 사용
    # (B, N, 1, 3) - (B, 1, M, 3) -> (B, N, M, 3) -> (B, N, M)
    p1_exp = p1.unsqueeze(2)
    p2_exp = p2.unsqueeze(1)
    
    dist = torch.sum((p1_exp - p2_exp) ** 2, dim=-1)
    
    min_dist_1_to_2 = torch.min(dist, dim=2)[0] # (B, N)
    min_dist_2_to_1 = torch.min(dist, dim=1)[0] # (B, M)
    
    loss = torch.mean(min_dist_1_to_2) + torch.mean(min_dist_2_to_1)
    return loss

# ==========================================
# 3. 데이터셋 클래스 (고정된 개수의 포인트 샘플링)
# ==========================================
class PairedObjectDataset(Dataset):
    def __init__(self, snow_dir, clean_dir, num_input=256, up_ratio=4):
        """
        snow_dir: 눈 시뮬레이션이 적용된 잘린 객체(.bin) 폴더
        clean_dir: 원본(정답) 잘린 객체(.bin) 폴더
        """
        self.snow_files = sorted(glob.glob(os.path.join(snow_dir, '*.bin')))
        self.clean_dir = clean_dir
        self.num_input = num_input
        self.num_target = num_input * up_ratio
        
    def __len__(self):
        return len(self.snow_files)
    
    def _sample_points(self, pts, num_samples):
        # 포인트 수가 부족하면 반복해서 채우고, 많으면 랜덤 샘플링
        num_pts = pts.shape[0]
        if num_pts == 0:
            return np.zeros((num_samples, 3), dtype=np.float32)
            
        if num_pts < num_samples:
            indices = np.random.choice(num_pts, num_samples, replace=True)
        else:
            indices = np.random.choice(num_pts, num_samples, replace=False)
        return pts[indices]

    def __getitem__(self, idx):
        snow_path = self.snow_files[idx]
        filename = os.path.basename(snow_path)
        clean_path = os.path.join(self.clean_dir, filename)
        
        # 포인트 클라우드 로드 (x, y, z 부분만 사용)
        snow_pts = np.fromfile(snow_path, dtype=np.float32).reshape(-1, 4)[:, :3]
        clean_pts = np.fromfile(clean_path, dtype=np.float32).reshape(-1, 4)[:, :3]
        
        # 고정된 크기 $N$과 $r \times N$으로 샘플링
        snow_sampled = self._sample_points(snow_pts, self.num_input)
        clean_sampled = self._sample_points(clean_pts, self.num_target)
        
        # (3, N) 형태로 변환 (PyTorch Conv1d 입력 규격)
        snow_tensor = torch.tensor(snow_sampled, dtype=torch.float32).transpose(0, 1)
        clean_tensor = torch.tensor(clean_sampled, dtype=torch.float32).transpose(0, 1)
        
        return snow_tensor, clean_tensor

# ==========================================
# 4. 학습 루프 (Training Loop)
# ==========================================
def train():
    # ⚠️ 이곳의 경로를 실제 학습 데이터 경로로 변경하세요.
    SNOW_DIR = './training/velodyne'
    CLEAN_DIR = '../kitti/training/velodyne'
    
    # 하이퍼파라미터
    BATCH_SIZE = 32
    EPOCHS = 50
    LR = 0.001
    UP_RATIO = 4
    NUM_INPUT_PTS = 256  # $N=256$
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"🔥 학습을 시작합니다. Device: {device}")
    
    dataset = PairedObjectDataset(SNOW_DIR, CLEAN_DIR, num_input=NUM_INPUT_PTS, up_ratio=UP_RATIO)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, drop_last=True)
    
    model = MiniPointUpsampler(up_ratio=UP_RATIO).to(device)
    optimizer = optim.Adam(model.parameters(), lr=LR)
    
    model.train()
    for epoch in range(EPOCHS):
        total_loss = 0.0
        
        for batch_idx, (snow_pts, clean_pts) in enumerate(dataloader):
            snow_pts = snow_pts.to(device)
            clean_pts = clean_pts.to(device)
            
            optimizer.zero_grad()
            
            # Forward pass
            pred_pts = model(snow_pts)  # (B, 3, r*N)
            
            # Loss 계산 및 Backward pass
            loss = chamfer_distance(pred_pts, clean_pts)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        avg_loss = total_loss / len(dataloader)
        print(f"Epoch [{epoch+1}/{EPOCHS}] | Average Chamfer Loss: {avg_loss:.4f}")
        
    # 가중치 저장
    save_path = './mini_upsampler_weights.pth'
    torch.save(model.state_dict(), save_path)
    print(f"✅ 학습 완료! 가중치가 저장되었습니다 -> {save_path}")

if __name__ == '__main__':
    train()