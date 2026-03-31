import os
import cv2
import argparse
import numpy as np

from pcdet.config import cfg, cfg_from_yaml_file
from pcdet.utils import calibration_kitti as calib_kitti
from pcdet.utils import object3d_kitti, common_utils

def draw_projected_box3d(image, corners3d_img, color=(0, 255, 0), thickness=2):
    corners3d_img = corners3d_img.astype(np.int32)
    for i in range(4):
        # 밑면, 윗면, 기둥 그리기
        cv2.line(image, tuple(corners3d_img[i]), tuple(corners3d_img[(i+1)%4]), color, thickness)
        cv2.line(image, tuple(corners3d_img[i+4]), tuple(corners3d_img[((i+1)%4)+4]), color, thickness)
        cv2.line(image, tuple(corners3d_img[i]), tuple(corners3d_img[i+4]), color, thickness)
    return image

def parse_config():
    parser = argparse.ArgumentParser(description='arg parser')
    parser.add_argument('--cfg_file', type=str, default='cfgs/dataset_configs/kitti_dataset.yaml')
    parser.add_argument('--scene', type=str, required=True, help='시각화할 scene 번호 (예: 000001)')
    parser.add_argument('--out_dir', type=str, default='../cloudcompare/gt_images', help='결과 저장 경로')
    args = parser.parse_args()
    return args

def main():
    args = parse_config()
    os.makedirs(args.out_dir, exist_ok=True)

    # 경로 설정 (GT는 training 폴더에 있음)
    data_root = '../data/kitti/training'
    img_path = os.path.join(data_root, 'image_2', f'{args.scene}.png')
    label_path = os.path.join(data_root, 'label_2', f'{args.scene}.txt')
    calib_path = os.path.join(data_root, 'calib', f'{args.scene}.txt')

    # 파일 존재 확인
    if not os.path.exists(label_path):
        print(f"Error: 라벨 파일을 찾을 수 없습니다: {label_path}")
        return

    # 이미지 및 캘리브레이션 로드
    img = cv2.imread(img_path)
    calib = calib_kitti.Calibration(calib_path)
    
    # GT 객체 로드
    obj_list = object3d_kitti.get_objects_from_label(label_path)

    # 클래스별 색상 (BGR 포맷)
    COLOR_MAP = {
        'Car': (0, 0, 255),        # Red
        'Pedestrian': (255, 0, 255), # Magenta
        'Cyclist': (0, 127, 255)     # Orange
    }

    for obj in obj_list:
        if obj.cls_type not in COLOR_MAP:
            continue

        # 1. 카메라 좌표계 기준 3D Box 꼭짓점 계산
        # KITTI 데이터셋의 dimensions은 [h, w, l] 순서임
        h, w, l = obj.h, obj.w, obj.l
        x_corners = [l/2, l/2, -l/2, -l/2, l/2, l/2, -l/2, -l/2]
        y_corners = [0, 0, 0, 0, -h, -h, -h, -h]
        z_corners = [w/2, -w/2, -w/2, w/2, w/2, -w/2, -w/2, w/2]
        
        # 회전 행렬 적용 (y축 기준 회전)
        R = np.array([
            [np.cos(obj.ry), 0, np.sin(obj.ry)],
            [0, 1, 0],
            [-np.sin(obj.ry), 0, np.cos(obj.ry)]
        ])
        corners_3d = np.dot(R, np.vstack([x_corners, y_corners, z_corners]))
        
        # 위치(Location) 이동
        corners_3d[0, :] += obj.loc[0]
        corners_3d[1, :] += obj.loc[1]
        corners_3d[2, :] += obj.loc[2]
        
        # 2. 이미지 평면으로 투영 (P2 매트릭스 사용)
        pts_img, _ = calib.rect_to_img(corners_3d.T)
        
        # 3. 그리기
        color = COLOR_MAP[obj.cls_type]
        img = draw_projected_box3d(img, pts_img, color=color)

    out_path = os.path.join(args.out_dir, f"{args.scene}_gt.png")
    cv2.imwrite(out_path, img)
    print(f"GT 시각화 완료: {out_path}")

if __name__ == '__main__':
    main()