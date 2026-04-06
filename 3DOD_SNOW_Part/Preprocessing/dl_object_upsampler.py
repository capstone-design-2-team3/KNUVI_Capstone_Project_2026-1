import os
import cv2
import numpy as np
import torch
import torch.nn as nn
from ultralytics import YOLO

# ==========================================
# 1. 딥러닝 기반 Point Cloud Upsampling 모델
# ==========================================
class MiniPointUpsampler(nn.Module):
    """
    PU-GAN의 뼈대가 되는 PointNet 기반의 가벼운 업샘플링 모델입니다.
    입력된 N개의 점을 r배(기본 4배)로 증폭시킵니다.
    """
    def __init__(self, up_ratio=4):
        super(MiniPointUpsampler, self).__init__()
        self.r = up_ratio
        # PointNet Feature Extractor
        self.mlp1 = nn.Sequential(
            nn.Conv1d(3, 64, 1), nn.ReLU(),
            nn.Conv1d(64, 128, 1), nn.ReLU(),
            nn.Conv1d(128, 256, 1)
        )
        # Feature Expansion
        self.mlp2 = nn.Sequential(
            nn.Conv1d(256 + 3, 256, 1), nn.ReLU(),
            nn.Conv1d(256, 3 * up_ratio, 1)
        )

    def forward(self, x):
        # x shape: (Batch, 3, N)
        B, C, N = x.size()
        
        # 글로벌 특징 추출
        global_feat = torch.max(self.mlp1(x), dim=2, keepdim=True)[0] # (B, 256, 1)
        global_feat = global_feat.expand(-1, -1, N)                   # (B, 256, N)
        
        # 로컬 특징(원본 좌표)과 글로벌 특징 결합
        concat_feat = torch.cat([x, global_feat], dim=1)              # (B, 256+3, N)
        
        # 포인트 수 증폭
        out = self.mlp2(concat_feat)                                  # (B, 3*r, N)
        
        # (B, 3, r*N) 형태로 재배열
        out = out.view(B, 3, N * self.r)
        return out

# ==========================================
# 2. 캘리브레이션 및 투영 유틸리티
# ==========================================
def load_kitti_calib(calib_path):
    with open(calib_path, 'r') as f:
        lines = f.readlines()
    calib = {}
    for line in lines:
        if not line.strip(): continue
        key, value = line.split(':', 1)
        calib[key] = np.array([float(x) for x in value.split()]).reshape(-1)

    P2 = calib['P2'].reshape(3, 4)
    R0_rect = np.eye(4)
    R0_rect[:3, :3] = calib['R0_rect'].reshape(3, 3)
    Tr_velo_to_cam = np.eye(4)
    Tr_velo_to_cam[:3, :4] = calib['Tr_velo_to_cam'].reshape(3, 4)
    return P2, R0_rect, Tr_velo_to_cam

# ==========================================
# 3. 메인 프로세스
# ==========================================
def process_pipeline(base_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    img_dir = os.path.join(base_dir, 'image_2')
    lidar_dir = os.path.join(base_dir, 'velodyne')
    calib_dir = os.path.join(base_dir, 'calib')

    # YOLOv8 모델 로드 (GPU가 있으면 자동 할당됨)
    yolo_model = YOLO('yolov8x-seg.pt')
    target_classes = [0, 1, 2] # 0: person, 1: bicycle, 2: car
    
    # 딥러닝 업샘플러 로드 (4배 업샘플링)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    upsampler = MiniPointUpsampler(up_ratio=4).to(device)
    weight_path = './mini_upsampler_weights.pth' # 학습 스크립트에서 저장한 파일 경로
    if os.path.exists(weight_path):
        upsampler.load_state_dict(torch.load(weight_path, map_location=device))
        print(f"✅ 성공: 학습된 가중치를 불러왔습니다. ({weight_path})")
    else:
        print(f"⚠️ 경고: 가중치 파일을 찾을 수 없습니다. 무작위 초기화 상태로 진행합니다. ({weight_path})")
    upsampler.eval() # 추론 모드

    # 데이터셋 순회
    frames = sorted([f.split('.')[0] for f in os.listdir(lidar_dir) if f.endswith('.bin')])
    print(f"🚀 총 {len(frames)}개의 프레임에 대해 딥러닝 기반 파이프라인 처리를 시작합니다 (Device: {device})")

    for i, frame in enumerate(frames):
        img_path = os.path.join(img_dir, f"{frame}.png")
        lidar_path = os.path.join(lidar_dir, f"{frame}.bin")
        calib_path = os.path.join(calib_dir, f"{frame}.txt")
        out_path = os.path.join(out_dir, f"{frame}.bin")

        if not (os.path.exists(img_path) and os.path.exists(calib_path)):
            continue

        # --- [Step 1] YOLOv8로 이미지 마스크 추출 ---
        img = cv2.imread(img_path)
        h, w = img.shape[:2]
        results = yolo_model(img, classes=target_classes, conf=0.3, verbose=False)[0]
        
        mask_canvas = np.zeros((h, w), dtype=np.uint8)
        if results.masks is not None:
            for poly in results.masks.xy:
                cv2.fillPoly(mask_canvas, [np.array(poly, dtype=np.int32)], 1)

        # --- [Step 2] 3D LiDAR 포인트 로드 및 투영 필터링 ---
        scan = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
        pts_3d = scan[:, :3]
        
        P2, R0_rect, Tr_velo_to_cam = load_kitti_calib(calib_path)
        pts_3d_hom = np.hstack((pts_3d, np.ones((pts_3d.shape[0], 1))))
        pts_img_hom = (P2 @ R0_rect @ Tr_velo_to_cam @ pts_3d_hom.T).T
        
        depth = pts_img_hom[:, 2]
        front_idx = depth > 0

        u = np.round(pts_img_hom[front_idx, 0] / depth[front_idx]).astype(np.int32)
        v = np.round(pts_img_hom[front_idx, 1] / depth[front_idx]).astype(np.int32)

        valid_img_idx = (u >= 0) & (u < w) & (v >= 0) & (v < h)
        u_valid = u[valid_img_idx]
        v_valid = v[valid_img_idx]

        obj_mask_idx = mask_canvas[v_valid, u_valid] > 0

        final_front_idx = np.where(front_idx)[0]
        final_valid_idx = final_front_idx[valid_img_idx]
        final_obj_idx = final_valid_idx[obj_mask_idx]

        object_points = pts_3d[final_obj_idx]
        
        # --- [Step 3] 딥러닝 기반 포인트 보강 (Upsampling) ---
        augmented_scan = scan.copy()
        
        if object_points.shape[0] > 10:  # 노이즈 방지를 위해 점이 10개 이상인 경우만 처리
            # 배치 처리를 위해 데이터 형태 변환: (1, 3, N)
            # 주의: 실제 학습 시에는 N을 고정(예: 512)해야 하지만, 추론 시에는 유동적으로 처리 가능
            obj_tensor = torch.tensor(object_points, dtype=torch.float32).unsqueeze(0).transpose(1, 2).to(device)
            
            with torch.no_grad():
                # 모델 통과 (N -> r*N)
                upsampled_tensor = upsampler(obj_tensor)
            
            # (1, 3, r*N) -> (r*N, 3)으로 다시 변환
            upsampled_points = upsampled_tensor.transpose(1, 2).squeeze(0).cpu().numpy()
            
            # Intensity 채널 추가 (원본의 평균 강도나 임의값 0.5 할당)
            intensities = np.full((upsampled_points.shape[0], 1), 0.5, dtype=np.float32)
            upsampled_points_with_i = np.hstack((upsampled_points, intensities))
            
            # --- [Step 4] 원본에 병합 ---
            augmented_scan = np.vstack((scan, upsampled_points_with_i))
            
        # 저장
        augmented_scan.astype(np.float32).tofile(out_path)
        
        if (i + 1) % 100 == 0 or (i + 1) == len(frames):
            print(f"[{i+1}/{len(frames)}] 처리 완료 -> {out_path}")

if __name__ == "__main__":
    # 사용자 환경에 맞게 입력/출력 경로를 설정하세요.
    DATASET_BASE_DIR = './training'
    OUTPUT_VELODYNE_DIR = './augmented_velodyne_dl'
    
    process_pipeline(DATASET_BASE_DIR, OUTPUT_VELODYNE_DIR)