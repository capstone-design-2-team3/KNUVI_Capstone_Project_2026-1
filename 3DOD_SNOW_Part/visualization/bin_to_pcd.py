import os
import glob
import argparse
import numpy as np
import open3d as o3d
from tqdm import tqdm
from pcdet import calibration_kitti

def get_fov_flag(pts_rect, img_shape, calib):
    """
    포인트가 카메라 시야각(FOV) 내부에 있는지 검사하는 함수
    """
    pts_img, pts_rect_depth = calib.rect_to_img(pts_rect)
    val_flag_1 = np.logical_and(pts_img[:, 0] >= 0, pts_img[:, 0] < img_shape[1])
    val_flag_2 = np.logical_and(pts_img[:, 1] >= 0, pts_img[:, 1] < img_shape[0])
    val_flag_merge = np.logical_and(val_flag_1, val_flag_2)
    # 이미지 픽셀 범위 내부이면서, 카메라 전방(depth >= 0)인 포인트만 True 반환
    pts_valid_flag = np.logical_and(val_flag_merge, pts_rect_depth >= 0)
    return pts_valid_flag

def bin_to_pcd_cropped(bin_path, pcd_path, calib_path):
    try:
        points = np.fromfile(bin_path, dtype=np.float32).reshape(-1, 4)
    except Exception as e:
        return False

    # 1. Calibration 로드
    if not os.path.exists(calib_path):
        return False
    calib = calibration_kitti.Calibration(calib_path)

    # 2. LiDAR 좌표를 카메라 좌표(Rectified)로 변환
    pts_rect = calib.lidar_to_rect(points[:, 0:3])

    # 3. FOV 필터링 적용 (KITTI 기본 해상도 375x1242 기준)
    img_shape = (375, 1242)
    fov_flag = get_fov_flag(pts_rect, img_shape, calib)
    
    # 4. 시야각 내부의 포인트만 남김 (부채꼴 크롭)
    cropped_points = points[fov_flag]

    # 5. Point Cloud Range 추가 크롭 (선택사항, Voxel-R-CNN 기준 [0, -40, -3, 70.4, 40, 1])
    mask_x = (cropped_points[:, 0] >= 0) & (cropped_points[:, 0] <= 70.4)
    mask_y = (cropped_points[:, 1] >= -40) & (cropped_points[:, 1] <= 40)
    mask_z = (cropped_points[:, 2] >= -3) & (cropped_points[:, 2] <= 1)
    final_mask = mask_x & mask_y & mask_z
    cropped_points = cropped_points[final_mask]

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(cropped_points[:, 0:3])

    try:
        o3d.io.write_point_cloud(pcd_path, pcd)
        return True
    except Exception as e:
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--in_dir', type=str, default='./dev_11_velodyne', help='입력 .bin 폴더')
    parser.add_argument('--calib_dir', type=str, default='./training/calib', help='캘리브레이션 .txt 폴더')
    parser.add_argument('--out_dir', type=str, default='./output', help='저장할 .pcd 폴더')
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    bin_files = glob.glob(os.path.join(args.in_dir, '*.bin'))

    success_count = 0
    for bin_file in tqdm(bin_files, desc="FOV Cropping & Converting"):
        base_name = os.path.basename(bin_file)
        file_id = os.path.splitext(base_name)[0] 
        
        calib_file = os.path.join(args.calib_dir, f"{file_id}.txt")
        pcd_file = os.path.join(args.out_dir, f"{file_id}.pcd")

        if bin_to_pcd_cropped(bin_file, pcd_file, calib_file):
            success_count += 1

    print(f"[*] 변환 완료! (성공: {success_count}/{len(bin_files)})")

if __name__ == '__main__':
    main()