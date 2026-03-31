import os
import argparse
import numpy as np
import torch

from pcdet.utils import box_utils, calibration_kitti, object3d_kitti
from pcdet.ops.roiaware_pool3d import roiaware_pool3d_utils

def parse_args():
    parser = argparse.ArgumentParser(description='Analyze point density drop in a specific scene')
    parser.add_argument('--scene', type=str, required=True, help='분석할 scene 번호 (예: 000008)')
    parser.add_argument('--label_dir', type=str, default='../data/kitti/training/label_2')
    parser.add_argument('--calib_dir', type=str, default='../data/kitti/training/calib')
    parser.add_argument('--clean_lidar_dir', type=str, default='../data/kitti/training/velodyne')
    parser.add_argument('--snow_lidar_dir', type=str, default='../data/kitti/velodyne_snow')
    return parser.parse_args()

def main():
    args = parse_args()
    
    calib_file = os.path.join(args.calib_dir, f'{args.scene}.txt')
    label_file = os.path.join(args.label_dir, f'{args.scene}.txt')
    clean_file = os.path.join(args.clean_lidar_dir, f'{args.scene}.bin')
    snow_file = os.path.join(args.snow_lidar_dir, f'{args.scene}.bin')
    
    # 파일 존재 여부 확인
    for f_path in [calib_file, label_file, clean_file, snow_file]:
        if not os.path.exists(f_path):
            print(f"Error: 파일을 찾을 수 없습니다 -> {f_path}")
            return
            
    print(f"[*] Scene '{args.scene}' 데이터 로드 및 분석 시작...\n")
            
    # 1. Calibration 및 Ground Truth 로드
    calib = calibration_kitti.Calibration(calib_file)
    obj_list = object3d_kitti.get_objects_from_label(label_file)
    
    target_classes = ['Car', 'Pedestrian', 'Cyclist']
    valid_objs = [obj for obj in obj_list if obj.cls_type in target_classes]
    
    if len(valid_objs) == 0:
        print(f"Scene '{args.scene}' 에는 분석할 대상(Car, Pedestrian, Cyclist)이 없습니다.")
        return
        
    # 카메라 좌표계의 3D Box를 LiDAR 좌표계로 변환
    loc = np.concatenate([obj.loc.reshape(1, 3) for obj in valid_objs], axis=0)
    dims = np.array([[obj.l, obj.h, obj.w] for obj in valid_objs])
    rots = np.array([obj.ry for obj in valid_objs])
    gt_names = [obj.cls_type for obj in valid_objs]
    
    gt_boxes_camera = np.concatenate([loc, dims, rots[..., np.newaxis]], axis=1).astype(np.float32)
    gt_boxes_lidar = box_utils.boxes3d_kitti_camera_to_lidar(gt_boxes_camera, calib)
    
    # 2. 원본 및 눈 시뮬레이션 포인트 클라우드 로드
    points_clean = np.fromfile(clean_file, dtype=np.float32).reshape(-1, 4)
    points_snow = np.fromfile(snow_file, dtype=np.float32).reshape(-1, 4)
    
    # 3. GT Box 내부의 포인트 개수 카운트
    pts_indices_clean = roiaware_pool3d_utils.points_in_boxes_cpu(
        torch.from_numpy(points_clean[:, 0:3]), torch.from_numpy(gt_boxes_lidar)
    ).numpy()
    pts_indices_snow = roiaware_pool3d_utils.points_in_boxes_cpu(
        torch.from_numpy(points_snow[:, 0:3]), torch.from_numpy(gt_boxes_lidar)
    ).numpy()
    
    num_pts_clean = pts_indices_clean.sum(axis=1)
    num_pts_snow = pts_indices_snow.sum(axis=1)
    
    # 4. 개별 객체별 결과 출력
    print(f"================ [ Scene {args.scene} 개별 객체 분석 ] ================")
    for i, name in enumerate(gt_names):
        clean_count = num_pts_clean[i]
        snow_count = num_pts_snow[i]
        
        if clean_count == 0:
            print(f"Obj {i+1:02d} [{name:10s}] : 원본 포인트 0개 (분석 제외, Occlusion/거리 문제 예상)")
            continue
            
        drop_rate = (1.0 - (snow_count / clean_count)) * 100
        
        print(f"Obj {i+1:02d} [{name:10s}] : 원본 {clean_count:4d}개 -> 눈 적용 {snow_count:4d}개 | 유실률: {drop_rate:5.1f}%")
    print("===================================================================")

if __name__ == '__main__':
    main()