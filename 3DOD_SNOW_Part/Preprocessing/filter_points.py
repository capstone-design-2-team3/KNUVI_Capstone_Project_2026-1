import os
import numpy as np

def load_kitti_calib(calib_path):
    """KITTI calib.txt 파일을 읽어 투영에 필요한 행렬을 반환합니다."""
    with open(calib_path, 'r') as f:
        lines = f.readlines()

    calib = {}
    for line in lines:
        if not line.strip():
            continue
        key, value = line.split(':', 1)
        calib[key] = np.array([float(x) for x in value.split()]).reshape(-1)

    P2 = calib['P2'].reshape(3, 4)
    
    R0_rect = np.eye(4)
    R0_rect[:3, :3] = calib['R0_rect'].reshape(3, 3)
    
    Tr_velo_to_cam = np.eye(4)
    Tr_velo_to_cam[:3, :4] = calib['Tr_velo_to_cam'].reshape(3, 4)

    return P2, R0_rect, Tr_velo_to_cam

def process_single_frame(lidar_path, calib_path, mask_path, output_path):
    """단일 프레임에 대해 투영, 필터링, 증강 및 병합을 수행합니다."""
    # 1. 데이터 로드
    scan = np.fromfile(lidar_path, dtype=np.float32).reshape(-1, 4)
    pts_3d = scan[:, :3]
    
    mask_data = np.load(mask_path)
    mask = mask_data['mask']
    img_h, img_w = mask.shape

    P2, R0_rect, Tr_velo_to_cam = load_kitti_calib(calib_path)

    # 2. LiDAR to Image 투영
    num_pts = pts_3d.shape[0]
    pts_3d_hom = np.hstack((pts_3d, np.ones((num_pts, 1))))
    proj_matrix = P2 @ R0_rect @ Tr_velo_to_cam
    pts_img_hom = (proj_matrix @ pts_3d_hom.T).T

    depth = pts_img_hom[:, 2]
    front_idx = depth > 0

    u = np.round(pts_img_hom[front_idx, 0] / depth[front_idx]).astype(np.int32)
    v = np.round(pts_img_hom[front_idx, 1] / depth[front_idx]).astype(np.int32)

    valid_img_idx = (u >= 0) & (u < img_w) & (v >= 0) & (v < img_h)
    u_valid = u[valid_img_idx]
    v_valid = v[valid_img_idx]

    # 3. 객체 마스크 내부에 있는 포인트 인덱스 찾기
    obj_mask_idx = mask[v_valid, u_valid] > 0

    final_front_idx = np.where(front_idx)[0]
    final_valid_idx = final_front_idx[valid_img_idx]
    final_obj_idx = final_valid_idx[obj_mask_idx]

    # 원본 객체 포인트 추출
    object_points = scan[final_obj_idx]

    # 4. 객체 포인트 증강 (가우시안 노이즈 기반 Jittering)
    if object_points.shape[0] > 0:
        augmented_points = np.copy(object_points)
        
        # x, y, z 좌표에 가우시안 노이즈 추가 (표준편차 0.05m)
        noise = np.random.normal(0, 0.05, size=(augmented_points.shape[0], 3))
        augmented_points[:, :3] += noise
        
        # 5. 병합 (Merge)
        final_scan = np.vstack((scan, augmented_points))
        added_count = object_points.shape[0]
    else:
        final_scan = scan
        added_count = 0

    # 결과 저장
    final_scan.astype(np.float32).tofile(output_path)
    return num_pts, final_scan.shape[0], added_count


def process_entire_dataset(base_dir):
    """데이터셋 폴더를 순회하며 모든 프레임을 처리합니다."""
    lidar_dir = os.path.join(base_dir, 'training/velodyne')
    calib_dir = os.path.join(base_dir, 'training/calib')
    mask_dir = os.path.join(base_dir, 'instance_masks')
    
    out_dir = os.path.join(base_dir, 'augmented_velodyne')
    os.makedirs(out_dir, exist_ok=True)

    # .bin 파일 목록 가져오기 및 정렬
    lidar_files = sorted([f for f in os.listdir(lidar_dir) if f.endswith('.bin')])
    total_files = len(lidar_files)
    
    print(f"총 {total_files}개의 프레임 처리를 시작합니다...")
    print("-" * 50)

    total_added_points = 0

    for i, lidar_filename in enumerate(lidar_files):
        # 파일명에서 확장자를 제외한 ID 추출 (예: '000000')
        file_id = os.path.splitext(lidar_filename)[0]

        lidar_path = os.path.join(lidar_dir, f"{file_id}.bin")
        calib_path = os.path.join(calib_dir, f"{file_id}.txt")
        mask_path = os.path.join(mask_dir, f"{file_id}.npz")
        output_path = os.path.join(out_dir, f"{file_id}.bin")

        # 필수 파일 존재 여부 확인
        if not os.path.exists(calib_path):
            print(f"[경고] 캘리브레이션 파일 누락으로 건너뜁니다: {file_id}.txt")
            continue
        if not os.path.exists(mask_path):
            print(f"[경고] 마스크 파일 누락으로 건너뜁니다: {file_id}.npz")
            continue

        try:
            # 단일 프레임 처리
            orig_count, final_count, added_count = process_single_frame(
                lidar_path, calib_path, mask_path, output_path
            )
            total_added_points += added_count
            
            # 진행 상황 출력 (100 프레임마다 또는 마지막 프레임일 때)
            if (i + 1) % 100 == 0 or (i + 1) == total_files:
                print(f"[{i + 1}/{total_files}] 처리 완료 (마지막 파일: {file_id}.bin) | 누적 추가 포인트: {total_added_points:,}개")
                
        except Exception as e:
            print(f"[에러] {file_id} 프레임 처리 중 문제 발생: {e}")

    print("-" * 50)
    print("모든 데이터셋 처리가 완료되었습니다.")

if __name__ == "__main__":
    # 데이터셋 최상위 경로 설정
    BASE_DIR = './'  # 경로를 실제 환경에 맞게 조정하세요
    
    process_entire_dataset(BASE_DIR)