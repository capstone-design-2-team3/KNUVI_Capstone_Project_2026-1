import os
import yaml
import argparse
import numpy as np
import open3d as o3d
o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Error)

from tqdm import tqdm
from data.kitti_dataset import KITTIDataset

# ---  컬러 매핑 (Color Mapping) 설정 ---
# RGB 값을 [0~1] 사이로 설정
COLOR_MAP = {
    'GT': {
        'Car': [0.0, 1.0, 0.0],         # 초록색
        'Pedestrian': [0.0, 1.0, 1.0],  # 청록색 (Cyan)
        'Cyclist': [1.0, 1.0, 0.0]      # 노란색
    },
    'PRED': {
        'Car': [1.0, 0.0, 0.0],         # 빨간색
        'Pedestrian': [1.0, 0.0, 1.0],  # 자주/보라색 (Magenta)
        'Cyclist': [1.0, 0.5, 0.0]      # 주황색
    }
}
DEFAULT_COLOR = [0.5, 0.5, 0.5] # 매핑되지 않은 클래스는 회색

def parse_config():
    parser = argparse.ArgumentParser(description='Export GT and Pred pairs to CloudCompare')
    parser.add_argument('--cfg_file', type=str, default='data/configs/ResNet_VFE.yaml')
    parser.add_argument('--split', type=str, default='val')
    parser.add_argument('--pred_dir', type=str, default='outputs/data')
    parser.add_argument('--out_dir', type=str, default='outputs/cloudcompare')
    return parser.parse_args()

def create_box_mesh(boxes, class_names, box_type='GT'):
    all_boxes = o3d.geometry.TriangleMesh()
    for box, cls_name in zip(boxes, class_names):
        center = box[0:3]
        extent = box[3:6]
        angle = box[6]
        
        # 설정된 컬러맵에서 색상 가져오기
        color = COLOR_MAP[box_type].get(cls_name, DEFAULT_COLOR)
        
        rot_mat = o3d.geometry.get_rotation_matrix_from_xyz((0, 0, angle))
        obb = o3d.geometry.OrientedBoundingBox(center, rot_mat, extent)
        obb_mesh = o3d.geometry.TriangleMesh.create_from_oriented_bounding_box(obb)
        obb_mesh.paint_uniform_color(color) 
        all_boxes += obb_mesh
    return all_boxes

def parse_kitti_pred_txt(txt_path, calib):
    """KITTI 예측 텍스트를 읽어 박스 리스트와 클래스 이름 리스트를 반환"""
    if not os.path.exists(txt_path):
        return [], []
        
    with open(txt_path, 'r') as f:
        lines = f.readlines()
        
    pred_boxes = []
    pred_classes = []
    
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 15: continue
        cls_name = parts[0]
        if cls_name == 'DontCare': continue
        
        h, w, l = float(parts[8]), float(parts[9]), float(parts[10])
        x, y, z = float(parts[11]), float(parts[12]), float(parts[13])
        ry = float(parts[14])
        
        rect_pts = np.array([[x, y, z]], dtype=np.float32)
        lidar_pts = calib.rect_to_lidar(rect_pts)
        lidar_pts[0, 2] += h / 2
        heading = -(ry + np.pi / 2)
        
        box = [lidar_pts[0, 0], lidar_pts[0, 1], lidar_pts[0, 2], l, w, h, heading]
        pred_boxes.append(box)
        pred_classes.append(cls_name)
        
    return np.array(pred_boxes), pred_classes

def main():
    args = parse_config()
    os.makedirs(args.out_dir, exist_ok=True)
    
    cfg = yaml.load(open(args.cfg_file, 'r'), Loader=yaml.Loader)
    dataset = KITTIDataset(cfg['dataset'], split=args.split, is_training=False, augment_data=False)

    pred_files = [f for f in os.listdir(args.pred_dir) if f.endswith('.txt')]
    
    for pred_file in tqdm(pred_files, desc='Exporting pairs with Multi-Colors'):
        frame_id = pred_file.split('.')[0]
        
        if frame_id not in dataset.id_list:
            continue
            
        idx = dataset.id_list.index(frame_id)
        data_dict = dataset[idx]
        calib = dataset.get_calib(frame_id)
        
        # 1. Point Cloud 저장
        colored_points = data_dict['colored_points']
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(colored_points[:, 0:3])
        if colored_points.shape[1] >= 7:
            pcd.colors = o3d.utility.Vector3dVector(colored_points[:, 4:7])
        o3d.io.write_point_cloud(os.path.join(args.out_dir, f"{frame_id}_points.pcd"), pcd)

        # 2. GT Boxes 저장
        if data_dict.get('gt_boxes') is not None and len(data_dict['gt_boxes']) > 0:
            gt_boxes = data_dict['gt_boxes'][:, :7]
            # 인덱스를 통해 클래스 이름 추출 (dataset_player.py 방식)
            gt_classes = [dataset.class_names[int(k - 1)] for k in data_dict['gt_boxes'][:, 7]]
            gt_mesh = create_box_mesh(gt_boxes, gt_classes, box_type='GT')
            o3d.io.write_triangle_mesh(os.path.join(args.out_dir, f"{frame_id}_boxes_gt.ply"), gt_mesh)

        # 3. Pred Boxes 저장
        txt_path = os.path.join(args.pred_dir, pred_file)
        pred_boxes, pred_classes = parse_kitti_pred_txt(txt_path, calib)
        
        if len(pred_boxes) > 0:
            pred_mesh = create_box_mesh(pred_boxes, pred_classes, box_type='PRED')
            o3d.io.write_triangle_mesh(os.path.join(args.out_dir, f"{frame_id}_boxes_pred.ply"), pred_mesh)

if __name__ == '__main__':
    main()