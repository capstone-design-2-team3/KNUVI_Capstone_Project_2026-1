import argparse
import numpy as np
import os
import torch
from tqdm import tqdm

from pointpillars.utils import keep_bbox_from_lidar_range, read_points
from pointpillars.model import PointPillars

def save_bboxes_to_ply(bboxes, labels, out_path):
    if len(bboxes) == 0:
        return
        
    with open(out_path, 'w') as f:
        f.write("ply\nformat ascii 1.0\n")
        f.write(f"element vertex {len(bboxes) * 8}\n")
        f.write("property float x\nproperty float y\nproperty float z\n")
        f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        # Edge 대신 Face(면) 요소를 사용하여 완벽한 3D 정육면체로 렌더링되게 강제
        f.write(f"element face {len(bboxes) * 6}\n")
        f.write("property list uchar int vertex_index\n")
        f.write("end_header\n")
        
        # 예측(PRED) 박스 색상: Pedestrian (Magenta), Cyclist (Orange), Car (Red)
        COLORS = {
            0: (255, 0, 255), 
            1: (255, 127, 0),  
            2: (255, 0, 0)
        }
        
        for i, bbox in enumerate(bboxes):
            # 모델 출력 형식: x, y, z, w(너비), l(길이), h(높이), yaw
            x, y, z, w, l, h, yaw = bbox
            c = COLORS.get(labels[i], (255, 255, 255))
            
            x_corners = [l/2, l/2, -l/2, -l/2, l/2, l/2, -l/2, -l/2]
            y_corners = [w/2, -w/2, -w/2, w/2, w/2, -w/2, -w/2, w/2]
            z_corners = [-h/2, -h/2, -h/2, -h/2, h/2, h/2, h/2, h/2] 
            
            corners_3d = np.vstack([x_corners, y_corners, z_corners])
            
            R = np.array([
                [np.cos(yaw), -np.sin(yaw), 0],
                [np.sin(yaw),  np.cos(yaw), 0],
                [0,            0,           1]
            ])
            corners_3d = np.dot(R, corners_3d).T + np.array([x, y, z])
            
            for corner in corners_3d:
                f.write(f"{corner[0]:.4f} {corner[1]:.4f} {corner[2]:.4f} {c[0]} {c[1]} {c[2]}\n")
                
        # 4개의 꼭짓점을 연결하여 6개의 폴리곤 면(Face) 생성
        for i in range(len(bboxes)):
            base = i * 8
            f.write(f"4 {base+0} {base+1} {base+2} {base+3}\n") # 밑면
            f.write(f"4 {base+4} {base+5} {base+6} {base+7}\n") # 윗면
            f.write(f"4 {base+0} {base+1} {base+5} {base+4}\n") # 앞면
            f.write(f"4 {base+1} {base+2} {base+6} {base+5}\n") # 우측면
            f.write(f"4 {base+2} {base+3} {base+7} {base+6}\n") # 뒷면
            f.write(f"4 {base+3} {base+0} {base+4} {base+7}\n") # 좌측면

def main(args):
    CLASSES = {'Pedestrian': 0, 'Cyclist': 1, 'Car': 2}
    pcd_limit_range = np.array([0, -40, -3, 70.4, 40, 0.0], dtype=np.float32)

    if not args.no_cuda:
        model = PointPillars(nclasses=len(CLASSES)).cuda()
        model.load_state_dict(torch.load(args.ckpt))
    else:
        model = PointPillars(nclasses=len(CLASSES))
        model.load_state_dict(torch.load(args.ckpt, map_location=torch.device('cpu')))
    
    model.eval()
    os.makedirs(args.output_dir, exist_ok=True)

    with open(args.split_file, 'r') as f:
        val_ids = [line.strip() for line in f.readlines()]
    
    print(f"val 세트 총 {len(val_ids)}개의 BBox PLY 변환을 시작합니다 (포인트 클라우드 생략)...")

    for file_id in tqdm(val_ids):
        pc_path = os.path.join(args.data_root, 'velodyne', f'{file_id}.bin')
        
        if not os.path.exists(pc_path):
            continue
            
        # 모델에 넣기 위해 포인트 클라우드를 읽지만, PLY 저장은 하지 않음
        pc = read_points(pc_path)
        
        # Point 필터링 로직 직접 구현 (test.py 참고)
        point_range = [0, -39.68, -3, 69.12, 39.68, 1]
        flag_x_low = pc[:, 0] > point_range[0]
        flag_y_low = pc[:, 1] > point_range[1]
        flag_z_low = pc[:, 2] > point_range[2]
        flag_x_high = pc[:, 0] < point_range[3]
        flag_y_high = pc[:, 1] < point_range[4]
        flag_z_high = pc[:, 2] < point_range[5]
        keep_mask = flag_x_low & flag_y_low & flag_z_low & flag_x_high & flag_y_high & flag_z_high
        pc_filtered = pc[keep_mask]
        
        pc_torch = torch.from_numpy(pc_filtered)
        
        with torch.no_grad():
            if not args.no_cuda:
                pc_torch = pc_torch.cuda()
            result_filter = model(batched_pts=[pc_torch], mode='test')[0]

        result_filter = keep_bbox_from_lidar_range(result_filter, pcd_limit_range)
        lidar_bboxes = result_filter['lidar_bboxes']
        labels = result_filter['labels']
        
        if len(lidar_bboxes) > 0:
            save_bboxes_to_ply(lidar_bboxes, labels, os.path.join(args.output_dir, f'{file_id}_pred_bbox.ply'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ckpt', default='pretrained/epoch_160.pth')
    parser.add_argument('--data_root', default='data/kitti_snow_sev5/training') 
    parser.add_argument('--split_file', default='pointpillars/dataset/ImageSets/val.txt') 
    parser.add_argument('--output_dir', default='outputs/data_val')
    parser.add_argument('--no_cuda', action='store_true')
    args = parser.parse_args()

    main(args)