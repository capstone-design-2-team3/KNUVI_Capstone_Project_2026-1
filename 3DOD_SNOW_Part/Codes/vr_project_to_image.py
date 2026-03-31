import os
import cv2
import argparse
import numpy as np
import torch

from pcdet.config import cfg, cfg_from_yaml_file
from pcdet.datasets import build_dataloader
from pcdet.models import build_network, load_data_to_gpu
from pcdet.utils import common_utils, box_utils
from pcdet.utils import calibration_kitti as calib_kitti

def draw_projected_box3d(image, corners3d_img, color=(0, 255, 0), thickness=2):
    """
    8개의 2D 투영 꼭짓점을 연결하여 이미지에 3D Bounding Box를 그립니다.
    """
    corners3d_img = corners3d_img.astype(np.int32)
    
    # 0~3: 밑면(Bottom), 4~7: 윗면(Top)
    for i in range(4):
        # 밑면 그리기
        cv2.line(image, tuple(corners3d_img[i]), tuple(corners3d_img[(i+1)%4]), color, thickness)
        # 윗면 그리기
        cv2.line(image, tuple(corners3d_img[i+4]), tuple(corners3d_img[((i+1)%4)+4]), color, thickness)
        # 기둥(Pillars) 그리기
        cv2.line(image, tuple(corners3d_img[i]), tuple(corners3d_img[i+4]), color, thickness)
        
    # 차량의 전면부(Heading)를 표시하기 위해 앞면(0, 1, 4, 5)에 'X' 표시를 추가
    cv2.line(image, tuple(corners3d_img[0]), tuple(corners3d_img[5]), color, thickness=1)
    cv2.line(image, tuple(corners3d_img[1]), tuple(corners3d_img[4]), color, thickness=1)
        
    return image

def parse_config():
    parser = argparse.ArgumentParser(description='arg parser')
    parser.add_argument('--cfg_file', type=str, default='cfgs/voxel_rcnn/voxel_rcnn_3classes.yaml')
    parser.add_argument('--ckpt', type=str, default='../output/voxel_rcnn/voxel_rcnn_3classes/default/ckpt/checkpoint_epoch_80.pth')
    parser.add_argument('--scene', type=str, required=True, help='검증할 scene 번호 (예: 000008)')
    parser.add_argument('--out_dir', type=str, default='../cloudcompare/images', help='투영된 이미지가 저장될 경로')
    parser.add_argument('--score_thresh', type=float, default=0.5, help='score threshold')
    args = parser.parse_args()
    cfg_from_yaml_file(args.cfg_file, cfg)
    return args, cfg

def main():
    args, cfg = parse_config()
    os.makedirs(args.out_dir, exist_ok=True)
    
    logger = common_utils.create_logger()
    
    # 데이터셋 불러오기 (특정 씬을 찾기 위함)
    test_set, test_loader, sampler = build_dataloader(
        dataset_cfg=cfg.DATA_CONFIG,
        class_names=cfg.CLASS_NAMES,
        batch_size=1,
        dist=False, workers=4, logger=logger, training=False
    )
    
    # 입력한 scene 번호에 해당하는 데이터 인덱스 탐색
    target_idx = -1
    for i, info in enumerate(test_set.kitti_infos):
        if info['point_cloud']['lidar_idx'] == args.scene:
            target_idx = i
            break
            
    if target_idx == -1:
        logger.error(f"데이터셋에서 Scene '{args.scene}'를 찾을 수 없습니다.")
        return
        
    logger.info(f"Scene '{args.scene}' 데이터를 로드하여 투영을 시작합니다.")
    
    # 선택한 데이터 로드 및 GPU 할당
    data_dict = test_set[target_idx]
    batch_dict = test_set.collate_batch([data_dict])
    load_data_to_gpu(batch_dict)
    
    # 모델 빌드 및 가중치 로드
    model = build_network(model_cfg=cfg.MODEL, num_class=len(cfg.CLASS_NAMES), dataset=test_set)
    model.load_params_from_file(filename=args.ckpt, logger=logger, to_cpu=False)
    model.cuda()
    model.eval()

    # OpenCV BGR 색상 포맷에 맞춘 매핑
    COLOR_MAP = {
        1: (0, 0, 255),    # Car: Red
        2: (255, 0, 255),  # Pedestrian: Magenta
        3: (0, 127, 255)   # Cyclist: Orange
    }

    with torch.no_grad():
        pred_dicts, _ = model.forward(batch_dict)
        pred = pred_dicts[0]
        
        mask = pred['pred_scores'] >= args.score_thresh
        pred_boxes = pred['pred_boxes'][mask].cpu().numpy()
        pred_labels = pred['pred_labels'][mask].cpu().numpy()
        
        # 이미지 및 캘리브레이션 행렬 로드
        img_path = os.path.join(cfg.DATA_CONFIG.DATA_PATH, 'training', 'image_2', f'{args.scene}.png')
        calib_path = os.path.join(cfg.DATA_CONFIG.DATA_PATH, 'training', 'calib', f'{args.scene}.txt')
        
        img = cv2.imread(img_path)
        if img is None:
            logger.error(f"이미지 파일을 읽을 수 없습니다: {img_path}")
            return
            
        calib = calib_kitti.Calibration(calib_path)
        
        if len(pred_boxes) > 0:
            corners3d_lidar = box_utils.boxes_to_corners_3d(pred_boxes) # (N, 8, 3)
            
            for i in range(len(pred_boxes)):
                corners = corners3d_lidar[i] 
                
                # LiDAR 좌표계의 3D 꼭짓점을 2D 이미지 평면으로 투영
                pts_img, pts_depth = calib.lidar_to_img(corners)
                
                # 카메라 뒤쪽에 있는 박스(depth < 0)는 화면을 왜곡시키므로 제외
                if np.any(pts_depth < 0.1):
                    continue
                    
                label = int(pred_labels[i])
                color = COLOR_MAP.get(label, (255, 255, 255))
                
                # 이미지에 Bounding Box 그리기
                img = draw_projected_box3d(img, pts_img, color=color, thickness=2)
                
        out_path = os.path.join(args.out_dir, f"{args.scene}_projected.png")
        cv2.imwrite(out_path, img)
        logger.info(f"투영 완료! 결과물이 저장되었습니다: {out_path}")

if __name__ == '__main__':
    main()