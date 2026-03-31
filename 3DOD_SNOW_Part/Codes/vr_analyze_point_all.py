import os
import argparse
import numpy as np
import torch
from tqdm import tqdm

from pcdet.utils import box_utils, calibration_kitti, object3d_kitti
from pcdet.ops.roiaware_pool3d import roiaware_pool3d_utils

def parse_args():
    parser = argparse.ArgumentParser(description='Analyze point density drop in GT boxes')
    parser.add_argument('--split_file', type=str, default='../data/kitti/ImageSets/val.txt', help='분석할 데이터 split 파일')
    parser.add_argument('--label_dir', type=str, default='../data/kitti/training/label_2')
    parser.add_argument('--calib_dir', type=str, default='../data/kitti/training/calib')
    # 원본 LiDAR 폴더와 눈 LiDAR 폴더 경로를 지정
    parser.add_argument('--clean_lidar_dir', type=str, default='../data/kitti/training/velodyne')
    parser.add_argument('--snow_lidar_dir', type=str, default='../data/kitti/velodyne_snow')
    return parser.parse_args()

def main():
    args = parse_args()
    
    with open(args.split_file, 'r') as f:
        sample_ids = [x.strip() for x in f.readlines()]
        
    # 클래스별 통계 저장을 위한 딕셔너리
    stats = {
        'Car': {'clean_pts': [], 'snow_pts': []},
        'Pedestrian': {'clean_pts': [], 'snow_pts': []},
        'Cyclist': {'clean_pts': [], 'snow_pts': []}
    }
    
    print(f"[*] 총 {len(sample_ids)}개의 샘플에 대해 포인트 유실률 분석을 시작합니다...")
    
    for sample_id in tqdm(sample_ids):
        calib_file = os.path.join(args.calib_dir, f'{sample_id}.txt')
        label_file = os.path.join(args.label_dir, f'{sample_id}.txt')
        clean_file = os.path.join(args.clean_lidar_dir, f'{sample_id}.bin')
        snow_file = os.path.join(args.snow_lidar_dir, f'{sample_id}.bin')
        
        if not all(os.path.exists(f) for f in [calib_file, label_file, clean_file, snow_file]):
            continue
            
        # 1. Calibration 및 Ground Truth 로드
        calib = calibration_kitti.Calibration(calib_file)
        obj_list = object3d_kitti.get_objects_from_label(label_file)
        
        # 분석 대상 클래스만 필터링
        valid_objs = [obj for obj in obj_list if obj.cls_type in stats.keys()]
        if len(valid_objs) == 0:
            continue
            
        # 카메라 좌표계의 3D Box를 LiDAR 좌표계로 변환 (lhw -> hwl)
        loc = np.concatenate([obj.loc.reshape(1, 3) for obj in valid_objs], axis=0)
        dims = np.array([[obj.l, obj.h, obj.w] for obj in valid_objs])
        rots = np.array([obj.ry for obj in valid_objs])
        gt_names = [obj.cls_type for obj in valid_objs]
        
        gt_boxes_camera = np.concatenate([loc, dims, rots[..., np.newaxis]], axis=1).astype(np.float32)
        gt_boxes_lidar = box_utils.boxes3d_kitti_camera_to_lidar(gt_boxes_camera, calib)
        
        # 2. 포인트 클라우드 로드
        points_clean = np.fromfile(clean_file, dtype=np.float32).reshape(-1, 4)
        points_snow = np.fromfile(snow_file, dtype=np.float32).reshape(-1, 4)
        
        # 3. GT Box 내부의 포인트 개수 카운트 (roiaware_pool3d 사용)
        # points_in_boxes_cpu 반환값 형태: (num_boxes, num_points)의 mask 배열
        pts_indices_clean = roiaware_pool3d_utils.points_in_boxes_cpu(
            torch.from_numpy(points_clean[:, 0:3]), torch.from_numpy(gt_boxes_lidar)
        ).numpy()
        pts_indices_snow = roiaware_pool3d_utils.points_in_boxes_cpu(
            torch.from_numpy(points_snow[:, 0:3]), torch.from_numpy(gt_boxes_lidar)
        ).numpy()
        
        num_pts_clean = pts_indices_clean.sum(axis=1)
        num_pts_snow = pts_indices_snow.sum(axis=1)
        
        # 4. 통계 누적
        for i, name in enumerate(gt_names):
            stats[name]['clean_pts'].append(num_pts_clean[i])
            stats[name]['snow_pts'].append(num_pts_snow[i])

    # 5. 최종 결과 수치화 및 출력
    print("\n================ [ Class-wise Point Density Analysis ] ================")
    for cls_name, data in stats.items():
        clean_arr = np.array(data['clean_pts'])
        snow_arr = np.array(data['snow_pts'])
        
        # 원본 데이터에 포인트가 0개 찍힌 객체(Occlusion 등으로 인해)는 비율 계산에서 제외
        valid_mask = clean_arr > 0
        clean_arr = clean_arr[valid_mask]
        snow_arr = snow_arr[valid_mask]
        
        if len(clean_arr) == 0:
            continue
            
        avg_clean = clean_arr.mean()
        avg_snow = snow_arr.mean()
        
        # 유실률 계산 (개별 박스의 유실률의 평균)
        drop_rates = (1.0 - (snow_arr / clean_arr)) * 100
        avg_drop_rate = drop_rates.mean()
        
        print(f"[{cls_name}] (총 {len(clean_arr)}개 유효 객체)")
        print(f"  - 원본 평균 포인트 수 : {avg_clean:.2f} pts")
        print(f"  - 눈(Snow) 평균 포인트 수: {avg_snow:.2f} pts")
        print(f"  - 평균 포인트 유실률  : {avg_drop_rate:.2f} %")
        print("---------------------------------------------------------------------")

if __name__ == '__main__':
    main()