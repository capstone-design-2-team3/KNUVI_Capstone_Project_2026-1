import os
import cv2
import numpy as np
import torch
import torch.nn as nn
from ultralytics import YOLO
from sklearn.cluster import DBSCAN

# ==========================================
# 1. 가벼운 CNN 기반 Depth Completion 모델 (Car, Pedestrian 용)
# ==========================================
class LightweightDepthNet(nn.Module):
    def __init__(self):
        super(LightweightDepthNet, self).__init__()
        self.enc1 = nn.Sequential(nn.Conv2d(4, 32, 3, padding=1), nn.ReLU(), nn.Conv2d(32, 32, 3, padding=1), nn.ReLU())
        self.pool1 = nn.MaxPool2d(2)
        self.enc2 = nn.Sequential(nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.Conv2d(64, 64, 3, padding=1), nn.ReLU())
        self.bottleneck = nn.Sequential(nn.MaxPool2d(2), nn.Conv2d(64, 128, 3, padding=1), nn.ReLU())
        self.up1 = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        self.dec1 = nn.Sequential(nn.Conv2d(128 + 64, 64, 3, padding=1), nn.ReLU())
        self.up2 = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
        self.dec2 = nn.Sequential(nn.Conv2d(64 + 32, 32, 3, padding=1), nn.ReLU(), nn.Conv2d(32, 1, 3, padding=1))

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool1(e1))
        b = self.bottleneck(e2)
        d1 = self.dec1(torch.cat([self.up1(b), e2], dim=1))
        d2 = self.dec2(torch.cat([self.up2(d1), e1], dim=1))
        return torch.relu(d2)

# ==========================================
# 2. 캘리브레이션 및 투영/역투영 유틸리티
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

# ==========================================
# 3. 메인 프로세스 (Hybrid Branching)
# ==========================================
def process_pipeline(base_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    img_dir = os.path.join(base_dir, 'image_2')
    lidar_dir = os.path.join(base_dir, 'velodyne')
    calib_dir = os.path.join(base_dir, 'calib')

    # YOLO 모델 로드 (Box Detection)
    yolo_model = YOLO('yolov8x.pt')
    target_classes = [0, 1, 2] # 0: Pedestrian, 1: Cyclist(Bicycle), 2: Car
    
    # CNN Depth 모델 로드
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    depth_net = LightweightDepthNet().to(device)
    
    # [선택] 학습된 Depth CNN 가중치가 있다면 여기서 로드
    # weight_path = './depth_net_weights.pth'
    # if os.path.exists(weight_path):
    #     depth_net.load_state_dict(torch.load(weight_path, map_location=device))
    depth_net.eval()

    frames = sorted([f.split('.')[0] for f in os.listdir(lidar_dir) if f.endswith('.bin')])
    print(f"🚀 하이브리드 파이프라인 시작 (Device: {device})")

    for i, frame in enumerate(frames):
        img_path = os.path.join(img_dir, f"{frame}.png")
        lidar_path = os.path.join(lidar_dir, f"{frame}.bin")
        calib_path = os.path.join(calib_dir, f"{frame}.txt")
        out_path = os.path.join(out_dir, f"{frame}.bin")

        if not (os.path.exists(img_path) and os.path.exists(calib_path)):
            continue

        img = cv2.imread(img_path)
        h, w = img.shape[:2]
        
        # --- [Step 1] YOLO Bounding Box & Class 추출 ---
        results = yolo_model(img, classes=target_classes, conf=0.3, verbose=False)[0]
        
        scan = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
        pts_3d = scan[:, :3]
        
        P2, R0_rect, Tr_velo_to_cam = load_kitti_calib(calib_path)
        pts_3d_hom = np.hstack((pts_3d, np.ones((pts_3d.shape[0], 1))))
        pts_img_hom = (P2 @ R0_rect @ Tr_velo_to_cam @ pts_3d_hom.T).T
        
        depth = pts_img_hom[:, 2]
        front_idx = depth > 0

        u = np.round(pts_img_hom[front_idx, 0] / depth[front_idx]).astype(np.int32)
        v = np.round(pts_img_hom[front_idx, 1] / depth[front_idx]).astype(np.int32)
        d_front = depth[front_idx]
        
        front_pts_3d = pts_3d[front_idx]
        front_scan = scan[front_idx]

        valid_img_idx = (u >= 0) & (u < w) & (v >= 0) & (v < h)
        u_valid, v_valid, d_valid = u[valid_img_idx], v[valid_img_idx], d_front[valid_img_idx]

        sparse_depth_map = np.zeros((h, w), dtype=np.float32)
        sparse_depth_map[v_valid, u_valid] = d_valid
        
        augmented_points_list = []

        # --- [Step 2] Class별 분기 처리 (Routing) ---
        if results.boxes is not None:
            boxes = results.boxes.xyxy.cpu().numpy().astype(int)
            cls_ids = results.boxes.cls.cpu().numpy().astype(int)
            
            for box, cls_id in zip(boxes, cls_ids):
                x1, y1, x2, y2 = max(0, box[0]), max(0, box[1]), min(w, box[2]), min(h, box[3])
                
                # --------------------------------------------------
                # 브랜치 A: Cyclist (클래스 1) -> Frustum + DBSCAN
                # --------------------------------------------------
                if cls_id == 1:
                    in_box_idx = (u >= x1) & (u <= x2) & (v >= y1) & (v <= y2)
                    frustum_pts = front_pts_3d[in_box_idx]
                    frustum_scan = front_scan[in_box_idx]
                    
                    if len(frustum_pts) < 15: continue
                    not_ground_idx = frustum_pts[:, 2] > -1.5
                    filtered_pts = frustum_pts[not_ground_idx]
                    filtered_scan = frustum_scan[not_ground_idx]

                    if len(filtered_pts) < 10: continue

                    clustering = DBSCAN(eps=0.6, min_samples=5).fit(filtered_pts)
                    labels = clustering.labels_
                    unique_labels, counts = np.unique(labels[labels != -1], return_counts=True)
                    if len(unique_labels) == 0: continue
                        
                    main_cluster_label = unique_labels[np.argmax(counts)]
                    object_points = filtered_scan[labels == main_cluster_label]
                    
                    # Jittering Augmentation
                    augmented_pts = np.copy(object_points)
                    noise = np.random.normal(0, 0.05, size=(augmented_pts.shape[0], 3))
                    augmented_pts[:, :3] += noise
                    augmented_points_list.append(augmented_pts)

                # --------------------------------------------------
                # 브랜치 B: Pedestrian (0), Car (2) -> CNN Depth Completion
                # --------------------------------------------------
                elif cls_id in [0, 2]:
                    if x2 - x1 < 10 or y2 - y1 < 10: continue
                    
                    rgb_crop = img[y1:y2, x1:x2]
                    depth_crop = sparse_depth_map[y1:y2, x1:x2]
                    
                    rgb_resized = cv2.resize(rgb_crop, (64, 64)) / 255.0
                    depth_resized = cv2.resize(depth_crop, (64, 64), interpolation=cv2.INTER_NEAREST)
                    
                    rgb_tensor = torch.tensor(rgb_resized, dtype=torch.float32).permute(2, 0, 1)
                    depth_tensor = torch.tensor(depth_resized, dtype=torch.float32).unsqueeze(0)
                    input_tensor = torch.cat([rgb_tensor, depth_tensor], dim=0).unsqueeze(0).to(device)
                    
                    with torch.no_grad():
                        pred_depth_resized = depth_net(input_tensor).squeeze().cpu().numpy()
                    
                    pred_depth = cv2.resize(pred_depth_resized, (x2 - x1, y2 - y1))
                    
                    yy, xx = np.where(pred_depth > 0)
                    if len(yy) == 0: continue
                    
                    global_u, global_v, global_z = xx + x1, yy + y1, pred_depth[yy, xx]
                    obj_3d_pts = unproject_to_3d(global_u, global_v, global_z, P2, R0_rect, Tr_velo_to_cam)
                    
                    intensities = np.full((obj_3d_pts.shape[0], 1), 0.5, dtype=np.float32)
                    augmented_points_list.append(np.hstack((obj_3d_pts, intensities)))

        # --- [Step 3] 원본 포인트와 병합 및 저장 ---
        if augmented_points_list:
            all_augmented = np.vstack(augmented_points_list)
            final_scan = np.vstack((scan, all_augmented))
        else:
            final_scan = scan
            
        final_scan.astype(np.float32).tofile(out_path)
        if (i + 1) % 100 == 0 or (i + 1) == len(frames):
            print(f"[{i+1}/{len(frames)}] 처리 완료 -> {out_path}")

if __name__ == "__main__":
    DATASET_BASE_DIR = './training'
    OUTPUT_VELODYNE_DIR = './augmented_velodyne_hybrid'
    process_pipeline(DATASET_BASE_DIR, OUTPUT_VELODYNE_DIR)