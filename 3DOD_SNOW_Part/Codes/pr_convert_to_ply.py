import os
import numpy as np
import argparse
from tqdm import tqdm

# 예측(PRED) 박스 색상 지정 (RGB 0~255 변환)
# Pedestrian (Magenta), Cyclist (Orange), Car (Red)
PRED_COLORS = {
    'Pedestrian': (255, 0, 255),
    'Cyclist': (255, 127, 0),
    'Car': (255, 0, 0)
}

def read_calib_file(filepath):
    data = {}
    with open(filepath, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if not line: continue
            key, value = line.split(':', 1)
            data[key] = np.array([float(x) for x in value.split()])
    return data

def rect_to_velo(pts_rect, calib_data):
    # 카메라 좌표계 -> LiDAR 좌표계 변환 행렬
    R0_ext = np.eye(4)
    R0_ext[:3, :3] = calib_data['R0_rect'].reshape(3, 3)
    Tr_velo_to_cam = np.eye(4)
    Tr_velo_to_cam[:3, :4] = calib_data['Tr_velo_to_cam'].reshape(3, 4)

    T_cam_to_velo = np.linalg.inv(Tr_velo_to_cam)
    R0_inv = np.linalg.inv(R0_ext)

    pts_hom = np.hstack((pts_rect, np.ones((pts_rect.shape[0], 1))))
    pts_velo = np.dot(pts_hom, R0_inv.T)
    pts_velo = np.dot(pts_velo, T_cam_to_velo.T)
    return pts_velo[:, :3]

def compute_box_3d(obj):
    # 3D Bounding Box의 8개 꼭짓점 좌표 계산 (PointRCNN 카메라 좌표계 기준)
    R = np.array([
        [np.cos(obj['ry']), 0, np.sin(obj['ry'])],
        [0, 1, 0],
        [-np.sin(obj['ry']), 0, np.cos(obj['ry'])]
    ])
    l, h, w = obj['l'], obj['h'], obj['w']
    x_corners = [l/2, l/2, -l/2, -l/2, l/2, l/2, -l/2, -l/2]
    y_corners = [0, 0, 0, 0, -h, -h, -h, -h]
    z_corners = [w/2, -w/2, -w/2, w/2, w/2, -w/2, -w/2, w/2]
    
    corners_3d = np.dot(R, np.vstack([x_corners, y_corners, z_corners]))
    corners_3d[0, :] += obj['tx']
    corners_3d[1, :] += obj['ty']
    corners_3d[2, :] += obj['tz']
    return np.transpose(corners_3d)

# 🚨 Face(면) 요소 적용으로 완벽한 정육면체 렌더링
def save_box_ply(corners_list, colors_list, out_file):
    num_boxes = len(corners_list)
    if num_boxes == 0:
        return
    
    num_vertices = num_boxes * 8
    num_faces = num_boxes * 6 # 육면체는 6개의 면(Face)을 가짐

    with open(out_file, 'w') as f:
        # 1. PLY 헤더 작성 (Face 요소 명시)
        f.write("ply\nformat ascii 1.0\n")
        f.write(f"element vertex {num_vertices}\n")
        f.write("property float x\nproperty float y\nproperty float z\n")
        f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        f.write(f"element face {num_faces}\n") # Edge 대신 Face 요소 사용
        f.write("property list uchar int vertex_index\n")
        f.write("end_header\n")

        # 2. 꼭짓점(Vertex) 좌표 및 색상 정보 기록
        for corners, color in zip(corners_list, colors_list):
            for pt in corners:
                f.write(f"{pt[0]:.4f} {pt[1]:.4f} {pt[2]:.4f} {color[0]} {color[1]} {color[2]}\n")

        # 3. 4개의 꼭짓점을 연결하여 6개의 폴리곤 면(Face) 생성
        for i in range(num_boxes):
            base = i * 8
            f.write(f"4 {base+0} {base+1} {base+2} {base+3}\n") # 밑면
            f.write(f"4 {base+4} {base+5} {base+6} {base+7}\n") # 윗면
            f.write(f"4 {base+0} {base+1} {base+5} {base+4}\n") # 앞면
            f.write(f"4 {base+1} {base+2} {base+6} {base+5}\n") # 우측면
            f.write(f"4 {base+2} {base+3} {base+7} {base+6}\n") # 뒷면
            f.write(f"4 {base+3} {base+0} {base+4} {base+7}\n") # 좌측면

def process_sample(sample_id, args):
    calib_file = os.path.join(args.calib_dir, f'{sample_id}.txt')
    if not os.path.exists(calib_file): return

    calib = read_calib_file(calib_file)
    pred_corners, pred_colors = [], []

    # 3개의 예측 폴더 경로 리스트
    pred_dirs = [args.dir_car, args.dir_ped, args.dir_cyc]

    for p_dir in pred_dirs:
        if p_dir is None: continue
        pred_file = os.path.join(p_dir, f'{sample_id}.txt')
        
        if os.path.exists(pred_file):
            with open(pred_file, 'r') as f:
                for line in f.readlines():
                    parts = line.split()
                    if len(parts) < 15: continue
                        
                    cls_type = parts[0]
                    if cls_type not in PRED_COLORS: continue
                        
                    obj = {'type': cls_type, 'h': float(parts[8]), 'w': float(parts[9]), 'l': float(parts[10]),
                           'tx': float(parts[11]), 'ty': float(parts[12]), 'tz': float(parts[13]), 'ry': float(parts[14])}
                    
                    corners_velo = rect_to_velo(compute_box_3d(obj), calib)
                    pred_corners.append(corners_velo)
                    pred_colors.append(PRED_COLORS[cls_type])

    # 세 클래스의 결과가 합쳐진 리스트를 하나의 PLY로 저장
    if pred_corners:
        save_box_ply(pred_corners, pred_colors, os.path.join(args.out_dir, f'{sample_id}_pred_merged.ply'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--split_file', type=str, default='../data/KITTI/ImageSets/val.txt')
    parser.add_argument('--calib_dir', type=str, default='../data/KITTI/object/training/calib')
    
    parser.add_argument('--dir_car', type=str, default='../output/rcnn/car/eval/epoch_70/val/final_result/data', help='Path to Car predictions')
    parser.add_argument('--dir_ped', type=str, default='../output/rcnn/pedestrian/eval/epoch_70/val/final_result/data', help='Path to Pedestrian predictions')
    parser.add_argument('--dir_cyc', type=str, default='../output/rcnn/cyclist/eval/epoch_70/val/final_result/data', help='Path to Cyclist predictions')
    
    parser.add_argument('--out_dir', type=str, default='../results')
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    with open(args.split_file, 'r') as f:
        sample_ids = [line.strip() for line in f.readlines()]

    print(f"[*] 총 {len(sample_ids)}개의 데이터에 대해 3개 클래스 병합 및 Face(면) 변환을 시작합니다.")
    
    for sample_id in tqdm(sample_ids, desc="Merging Predictions"):
        process_sample(sample_id, args)
        
    print("[*] 정육면체 형태의 통합 PLY 파일 생성이 완료되었습니다!")
