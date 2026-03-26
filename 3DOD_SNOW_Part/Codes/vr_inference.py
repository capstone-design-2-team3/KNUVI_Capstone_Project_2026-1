import os
import argparse
import numpy as np
import torch
import open3d as o3d
from tqdm import tqdm

from pcdet.config import cfg, cfg_from_yaml_file
from pcdet.datasets import build_dataloader
from pcdet.models import build_network, load_data_to_gpu
from pcdet.utils import common_utils, box_utils

def parse_config():
    parser = argparse.ArgumentParser(description='arg parser')
    parser.add_argument('--cfg_file', type=str, default='cfgs/voxel_rcnn/voxel_rcnn_3classes.yaml')
    parser.add_argument('--ckpt', type=str, default='../output/voxel_rcnn/voxel_rcnn_3classes/default/ckpt/checkpoint_epoch_80.pth')
    parser.add_argument('--out_dir', type=str, default='../cloudcompare', help='output directory for ply files')
    parser.add_argument('--score_thresh', type=float, default=0.5, help='score threshold to filter predictions')
    args = parser.parse_args()
    cfg_from_yaml_file(args.cfg_file, cfg)
    return args, cfg

def main():
    args, cfg = parse_config()
    
    # 출력 폴더 생성
    os.makedirs(args.out_dir, exist_ok=True)
    
    logger = common_utils.create_logger()
    logger.info('----------------- Start Inference & Export BBox to PLY -----------------')
    
    # DataLoader 세팅
    test_set, test_loader, sampler = build_dataloader(
        dataset_cfg=cfg.DATA_CONFIG,
        class_names=cfg.CLASS_NAMES,
        batch_size=8,
        dist=False, workers=4, logger=logger, training=False
    )
    
    # 모델 빌드 및 가중치 로드
    model = build_network(model_cfg=cfg.MODEL, num_class=len(cfg.CLASS_NAMES), dataset=test_set)
    model.load_params_from_file(filename=args.ckpt, logger=logger, to_cpu=False)
    model.cuda()
    model.eval()

    # 8개의 꼭짓점을 12개의 삼각형(Triangle) 면으로 구성하기 위한 인덱스
    faces_indices = [
        [0, 1, 2], [0, 2, 3], # 밑면
        [4, 5, 6], [4, 6, 7], # 윗면
        [0, 1, 5], [0, 5, 4], # 앞면
        [1, 2, 6], [1, 6, 5], # 우측면
        [2, 3, 7], [2, 7, 6], # 뒷면
        [3, 0, 4], [3, 4, 7]  # 좌측면
    ]

    with torch.no_grad():
        for i, batch_dict in enumerate(tqdm(test_loader, desc="Predicting & Saving BBox to PLY")):
            
            load_data_to_gpu(batch_dict)
            pred_dicts, _ = model.forward(batch_dict)
            
            for batch_idx in range(len(pred_dicts)):
                frame_id = batch_dict['frame_id'][batch_idx]
                
                pred = pred_dicts[batch_idx]
                mask = pred['pred_scores'] >= args.score_thresh
                pred_boxes = pred['pred_boxes'][mask].cpu().numpy()
                pred_labels = pred['pred_labels'][mask].cpu().numpy()
                
                if len(pred_boxes) == 0:
                    continue
                    
                corners3d = box_utils.boxes_to_corners_3d(pred_boxes) 
                
                all_vertices = []
                all_triangles = []
                all_colors = []
                
                vertex_offset = 0
                for box_idx in range(len(pred_boxes)):
                    all_vertices.append(corners3d[box_idx])
                    
                    box_triangles = np.array(faces_indices) + vertex_offset
                    all_triangles.append(box_triangles)
                    
                    # 명시적으로 파이썬 기본 int형으로 변환하여 흰색 오류 해결
                    label = int(pred_labels[box_idx])
                    
                    # OpenPCDet 라벨 순서에 맞춰 직관적인 조건문으로 색상 할당
                    if label == 1:
                        color = [1.0, 0.0, 0.0]     # Red (Car)
                    elif label == 2:
                        color = [1.0, 0.0, 1.0]     # Magenta (Pedestrian)
                    elif label == 3:
                        color = [1.0, 0.5, 0.0]     # Orange (Cyclist)
                    else:
                        color = [1.0, 1.0, 1.0]     # White (Unknown)
                        
                    all_colors.extend([color for _ in range(8)]) 
                    vertex_offset += 8
                    
                all_vertices = np.vstack(all_vertices)
                all_triangles = np.vstack(all_triangles)
                all_colors = np.vstack(all_colors)
                
                mesh = o3d.geometry.TriangleMesh()
                mesh.vertices = o3d.utility.Vector3dVector(all_vertices)
                mesh.triangles = o3d.utility.Vector3iVector(all_triangles)
                mesh.vertex_colors = o3d.utility.Vector3dVector(all_colors)
                
                o3d.io.write_triangle_mesh(os.path.join(args.out_dir, f"{frame_id}_bbox.ply"), mesh)

if __name__ == '__main__':
    main()