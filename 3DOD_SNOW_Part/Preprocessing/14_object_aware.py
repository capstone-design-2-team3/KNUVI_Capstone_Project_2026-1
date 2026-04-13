import os
import cv2
import numpy as np
import torch
import torch.nn as nn
from ultralytics import YOLO
from scipy.spatial import cKDTree

class SpatialAttention(nn.Module):
    """
    입력 피처맵에서 객체의 경계선 및 중요 구조(예: 자전거 프레임)를 
    강조하기 위한 Spatial Attention 모듈
    """
    def __init__(self, kernel_size=7):
        super(SpatialAttention, self).__init__()
        # 평균 풀링과 최대 풀링 결과를 채널 방향으로 합친 후 1채널로 압축
        self.conv = nn.Conv2d(2, 1, kernel_size, padding=kernel_size//2, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        avg_out = torch.mean(x, dim=1, keepdim=True)
        max_out, _ = torch.max(x, dim=1, keepdim=True)
        scale = torch.cat([avg_out, max_out], dim=1)
        scale = self.conv(scale)
        return x * self.sigmoid(scale)
    
class AttentionDepthNet(nn.Module):
    def __init__(self):
        super(AttentionDepthNet, self).__init__()
        # Encoder
        self.enc1 = nn.Sequential(nn.Conv2d(4, 32, 3, padding=1), nn.ReLU(), nn.Conv2d(32, 32, 3, padding=1), nn.ReLU())
        self.pool1 = nn.MaxPool2d(2)
        
        self.enc2 = nn.Sequential(nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.Conv2d(64, 64, 3, padding=1), nn.ReLU())
        
        # Bottleneck + Attention
        self.bottleneck = nn.Sequential(nn.MaxPool2d(2), nn.Conv2d(64, 128, 3, padding=1), nn.ReLU())
        self.attention = SpatialAttention() # 핵심 경계선 강조
        
        # Decoder
        self.up1 = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        self.dec1 = nn.Sequential(nn.Conv2d(128 + 64, 64, 3, padding=1), nn.ReLU())
        
        self.up2 = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        self.dec2 = nn.Sequential(nn.Conv2d(64 + 32, 32, 3, padding=1), nn.ReLU(), nn.Conv2d(32, 1, 3, padding=1))

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool1(e1))
        
        b = self.bottleneck(e2)
        b = self.attention(b) # Attention 적용
        
        d1 = self.dec1(torch.cat([self.up1(b), e2], dim=1))
        d2 = self.dec2(torch.cat([self.up2(d1), e1], dim=1))
        return torch.relu(d2)
    
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

def unproject_to_3d(u, v, z, P2, R0_rect, Tr_velo_to_cam):
    fx, fy = P2[0, 0], P2[1, 1]
    cx, cy = P2[0, 2], P2[1, 2]
    
    x_c = (u - cx) * z / fx
    y_c = (v - cy) * z / fy
    z_c = z
    
    num_pts = len(z)
    P_cam = np.vstack((x_c, y_c, z_c, np.ones(num_pts))).T
    
    R0_inv = np.linalg.inv(R0_rect)
    Tr_inv = np.linalg.inv(Tr_velo_to_cam)
    P_velo = (Tr_inv @ R0_inv @ P_cam.T).T
    return P_velo[:, :3]

# ===================================

def remove_ground(pts_3d, height_threshold=-1.5):
    """지면 포인트 제거 (센서 높이에 따라 조정 필요)"""
    return pts_3d[pts_3d[:, 2] > height_threshold]

def process_pedestrian_v2(pts_3d):
    """
    보행자: 인위적 생성 없이, 지면 및 극단적인 아웃라이어만 제거
    """
    pts = remove_ground(pts_3d)
    if len(pts) < 5: return None
    # 보행자의 형태를 그대로 유지하기 위해 반사율만 일정하게 부여 (원본 포인트 사용 권장)
    intensities = np.full((pts.shape[0], 1), 0.5, dtype=np.float32)
    return np.hstack((pts, intensities))

def process_cyclist_symmetry(pts_3d):
    """
    자전거: 형태적 대칭성(Symmetry)을 이용한 보강
    객체의 중앙(Centroid)을 구한 후, 특정 축을 기준으로 기존 포인트를 대칭 복사
    """
    pts = remove_ground(pts_3d)
    if len(pts) < 5: return None

    # Z축(높이)과 Y축을 유지하면서 X축 방향으로 미세하게 대칭 (LiDAR 좌표계 고려)
    centroid = np.mean(pts, axis=0)
    
    mirrored_pts = np.copy(pts)
    # X축 기준으로 객체 중심에 대해 대칭 이동
    mirrored_pts[:, 0] = 2 * centroid[0] - mirrored_pts[:, 0]
    
    # 너무 멀리 떨어진 아웃라이어 대칭 방지
    distances = np.linalg.norm(mirrored_pts - centroid, axis=1)
    valid_mirrored = mirrored_pts[distances < 1.5] # 반경 1.5m 이내만 수용
    
    if len(valid_mirrored) == 0: return None
    
    intensities = np.full((valid_mirrored.shape[0], 1), 0.6, dtype=np.float32)
    return np.hstack((valid_mirrored, intensities))

def process_car_kdtree_cnn(pts_3d, cnn_generated_pts):
    """
    자동차: CNN이 생성한 포인트를 그대로 쓰지 않고, 
    실제 원본 LiDAR 포인트 주변(예: 15cm 이내)에 있는 것만 살려서 Hole-filling 수행
    """
    pts = remove_ground(pts_3d)
    if len(pts) < 10 or len(cnn_generated_pts) == 0: return None
    
    # 원본 포인트로 KD-Tree 구성
    tree = cKDTree(pts)
    
    # CNN이 예측한 포인트가 원본 포인트와 얼마나 가까운지 검사 (반경 0.15m)
    distances, _ = tree.query(cnn_generated_pts, k=1, distance_upper_bound=0.15)
    
    # distance_upper_bound를 벗어나면 무한대(inf) 값이 반환됨
    valid_mask = distances != np.inf
    valid_cnn_pts = cnn_generated_pts[valid_mask]
    
    if len(valid_cnn_pts) == 0: return None
    
    intensities = np.full((valid_cnn_pts.shape[0], 1), 0.5, dtype=np.float32)
    return np.hstack((valid_cnn_pts, intensities))


def process_pipeline_v2(base_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    img_dir = os.path.join(base_dir, 'image_2')
    lidar_dir = os.path.join(base_dir, 'velodyne')
    calib_dir = os.path.join(base_dir, 'calib')

    yolo_model = YOLO('yolov8x.pt')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    depth_net = AttentionDepthNet().to(device)
    depth_net.eval()

    frames = sorted([f.split('.')[0] for f in os.listdir(lidar_dir) if f.endswith('.bin')])
    print("🚀 V2 Pipeline: Geometry-Preserving & KD-Tree Filter 적용 시작")

    for i, frame in enumerate(frames):
        img_path = os.path.join(img_dir, f"{frame}.png")
        lidar_path = os.path.join(lidar_dir, f"{frame}.bin")
        calib_path = os.path.join(calib_dir, f"{frame}.txt")
        out_path = os.path.join(out_dir, f"{frame}.bin")

        if not (os.path.exists(img_path) and os.path.exists(calib_path)): continue

        img = cv2.imread(img_path)
        h, w = img.shape[:2]
        results = yolo_model(img, classes=[0, 1, 2], conf=0.4, verbose=False)[0] # Confidence 상향
        
        scan = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
        pts_3d = scan[:, :3]
        
        P2, R0_rect, Tr_velo_to_cam = load_kitti_calib(calib_path)
        pts_3d_hom = np.hstack((pts_3d, np.ones((pts_3d.shape[0], 1))))
        pts_img_hom = (P2 @ R0_rect @ Tr_velo_to_cam @ pts_3d_hom.T).T
        
        depth = pts_img_hom[:, 2]
        front_idx = depth > 0
        u = np.round(pts_img_hom[front_idx, 0] / depth[front_idx]).astype(np.int32)
        v = np.round(pts_img_hom[front_idx, 1] / depth[front_idx]).astype(np.int32)
        
        front_pts_3d = pts_3d[front_idx]
        valid_img_idx = (u >= 0) & (u < w) & (v >= 0) & (v < h)
        
        sparse_depth_map = np.zeros((h, w), dtype=np.float32)
        sparse_depth_map[v[valid_img_idx], u[valid_img_idx]] = depth[front_idx][valid_img_idx]
        
        augmented_points_list = []

        if results.boxes is not None:
            boxes = results.boxes.xyxy.cpu().numpy().astype(int)
            cls_ids = results.boxes.cls.cpu().numpy().astype(int)
            
            for box, cls_id in zip(boxes, cls_ids):
                x1, y1, x2, y2 = max(0, box[0]), max(0, box[1]), min(w, box[2]), min(h, box[3])
                
                in_box_idx = (u[valid_img_idx] >= x1) & (u[valid_img_idx] <= x2) & \
                             (v[valid_img_idx] >= y1) & (v[valid_img_idx] <= y2)
                box_pts_3d = front_pts_3d[valid_img_idx][in_box_idx]

                # 1. Pedestrian
                if cls_id == 0:
                    pass # 보행자는 가짜 포인트 생성 아예 중단 (원본 유지 + YOLO 필터)
                    
                # 2. Cyclist (대칭 복사)
                elif cls_id == 1:
                    aug_pts = process_cyclist_symmetry(box_pts_3d)
                    if aug_pts is not None: augmented_points_list.append(aug_pts)

                # 3. Car (CNN + KDTree 필터링)
                elif cls_id == 2:
                    if x2 - x1 < 20 or y2 - y1 < 20: continue
                    
                    rgb_crop = img[y1:y2, x1:x2]
                    depth_crop = sparse_depth_map[y1:y2, x1:x2]
                    
                    rgb_tensor = torch.tensor(cv2.resize(rgb_crop, (64, 64)) / 255.0, dtype=torch.float32).permute(2, 0, 1)
                    depth_tensor = torch.tensor(cv2.resize(depth_crop, (64, 64), interpolation=cv2.INTER_NEAREST), dtype=torch.float32).unsqueeze(0)
                    input_tensor = torch.cat([rgb_tensor, depth_tensor], dim=0).unsqueeze(0).to(device)
                    
                    with torch.no_grad():
                        pred_depth_resized = depth_net(input_tensor).squeeze().cpu().numpy()
                    pred_depth = cv2.resize(pred_depth_resized, (x2 - x1, y2 - y1))
                    
                    yy, xx = np.where(pred_depth > 0)
                    if len(yy) == 0: continue
                    
                    cnn_3d_pts = unproject_to_3d(xx + x1, yy + y1, pred_depth[yy, xx], P2, R0_rect, Tr_velo_to_cam)
                    
                    # 핵심: CNN 생성 포인트를 KD-Tree로 검열
                    aug_pts = process_car_kdtree_cnn(box_pts_3d, cnn_3d_pts)
                    if aug_pts is not None: augmented_points_list.append(aug_pts)

        final_scan = np.vstack([scan] + augmented_points_list) if augmented_points_list else scan
        final_scan.astype(np.float32).tofile(out_path)

        if (i + 1) % 50 == 0:
            print(f"[{i+1}/{len(frames)}] 처리 완료")

if __name__ == "__main__":
    process_pipeline_v2('./training', './14_geometry_velodyne')