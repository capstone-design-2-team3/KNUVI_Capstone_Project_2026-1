import os
import cv2
import numpy as np
from ultralytics import YOLO
from sklearn.cluster import DBSCAN

# ==========================================
# 1. 캘리브레이션 및 투영 유틸리티
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
# 2. 메인 프로세스
# ==========================================
def process_pipeline(base_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    img_dir = os.path.join(base_dir, 'image_2')
    lidar_dir = os.path.join(base_dir, 'velodyne')
    calib_dir = os.path.join(base_dir, 'calib')

    # Mask가 아닌 일반 2D Bounding Box 모델 사용 (속도 및 강건성 확보)
    yolo_model = YOLO('yolov8x.pt') 
    target_classes = [0, 1, 2] # 0: person, 1: bicycle, 2: car

    frames = sorted([f.split('.')[0] for f in os.listdir(lidar_dir) if f.endswith('.bin')])
    print(f"🚀 총 {len(frames)}개의 프레임에 대해 Frustum + DBSCAN 파이프라인을 시작합니다.")

    for i, frame in enumerate(frames):
        img_path = os.path.join(img_dir, f"{frame}.png")
        lidar_path = os.path.join(lidar_dir, f"{frame}.bin")
        calib_path = os.path.join(calib_dir, f"{frame}.txt")
        out_path = os.path.join(out_dir, f"{frame}.bin")

        if not (os.path.exists(img_path) and os.path.exists(calib_path)):
            continue

        # --- [Step 1] YOLOv8로 2D Bounding Box 추출 ---
        img = cv2.imread(img_path)
        h, w = img.shape[:2]
        results = yolo_model(img, classes=target_classes, conf=0.3, verbose=False)[0]
        
        boxes = results.boxes.xyxy.cpu().numpy() # [x1, y1, x2, y2]
        
        # --- [Step 2] 3D LiDAR 포인트 로드 및 투영 ---
        scan = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
        pts_3d = scan[:, :3]
        
        P2, R0_rect, Tr_velo_to_cam = load_kitti_calib(calib_path)
        pts_3d_hom = np.hstack((pts_3d, np.ones((pts_3d.shape[0], 1))))
        pts_img_hom = (P2 @ R0_rect @ Tr_velo_to_cam @ pts_3d_hom.T).T
        
        depth = pts_img_hom[:, 2]
        front_idx = depth > 0

        u = np.round(pts_img_hom[front_idx, 0] / depth[front_idx]).astype(np.int32)
        v = np.round(pts_img_hom[front_idx, 1] / depth[front_idx]).astype(np.int32)

        # 카메라 전방에 있는 원본 포인트들
        front_pts_3d = pts_3d[front_idx]
        front_scan = scan[front_idx]
        
        augmented_points_list = []

        # --- [Step 3] Frustum 추출 및 DBSCAN 클러스터링 ---
        for box in boxes:
            x1, y1, x2, y2 = box
            
            # 2D BBox 내부에 들어오는 포인트 인덱스 추출 (Frustum)
            in_box_idx = (u >= x1) & (u <= x2) & (v >= y1) & (v <= y2)
            frustum_pts = front_pts_3d[in_box_idx]
            frustum_scan = front_scan[in_box_idx]
            
            if len(frustum_pts) < 15: # 너무 적은 포인트는 무시
                continue

            # 지면(Ground) 포인트 제거를 위한 휴리스틱 (LiDAR 센서 기준 Z축(위아래) 필터링)
            # KITTI 기준 센서는 차량 지붕에 있으므로, 바닥(약 -1.5m 이하)은 제외
            not_ground_idx = frustum_pts[:, 2] > -1.5
            filtered_pts = frustum_pts[not_ground_idx]
            filtered_scan = frustum_scan[not_ground_idx]

            if len(filtered_pts) < 10:
                continue

            # DBSCAN으로 메인 객체(차량/보행자) 군집화
            # eps: 이웃 반경 (0.5m~0.8m 가 적당), min_samples: 최소 점 개수
            clustering = DBSCAN(eps=0.6, min_samples=5).fit(filtered_pts)
            labels = clustering.labels_
            
            # 노이즈(-1)를 제외한 가장 큰 군집 찾기
            unique_labels, counts = np.unique(labels[labels != -1], return_counts=True)
            if len(unique_labels) == 0:
                continue
                
            main_cluster_label = unique_labels[np.argmax(counts)]
            main_cluster_idx = (labels == main_cluster_label)
            
            object_points = filtered_scan[main_cluster_idx]
            
            # --- [Step 4] 객체 포인트 증강 (Jittering) ---
            # 마스크 잘림 현상이 없으므로, 이제 Jittering이 차량 전체 형태를 예쁘게 덮어줍니다.
            augmented_pts = np.copy(object_points)
            noise = np.random.normal(0, 0.05, size=(augmented_pts.shape[0], 3))
            augmented_pts[:, :3] += noise
            
            augmented_points_list.append(augmented_pts)

        # --- [Step 5] 원본과 병합 및 저장 ---
        if augmented_points_list:
            all_augmented = np.vstack(augmented_points_list)
            final_scan = np.vstack((scan, all_augmented))
        else:
            final_scan = scan
            
        final_scan.astype(np.float32).tofile(out_path)
        
        if (i + 1) % 100 == 0 or (i + 1) == len(frames):
            print(f"[{i+1}/{len(frames)}] 처리 완료 -> {out_path}")

if __name__ == "__main__":
    # 사용자 환경에 맞게 폴더 경로를 지정하세요
    DATASET_BASE_DIR = './training'
    OUTPUT_VELODYNE_DIR = './augmented_velodyne_dbscan'
    
    process_pipeline(DATASET_BASE_DIR, OUTPUT_VELODYNE_DIR)