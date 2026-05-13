"""
LLIE 4개 조건 × 3개 모델 3D 바운딩 박스 시각화

레이아웃: 1행 × 4열 (Original | CLAHE | EnlightenGAN | Zero-DCE)
박스 색:  GT=초록 / MoME=빨강 / DeepInteraction=파랑 / BEVFusion=주황

투영 방식: 참고 코드와 동일 (LiDAR → Ego → Camera, Quaternion 사용)
"""
import pickle, numpy as np, cv2
from pathlib import Path
from pyquaternion import Quaternion
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

BASE      = Path('/home/knuvi/Undergraduate/kyungjin')
NIGHT_PKL = BASE / 'model/MoME/data/nuscenes/nuscenes_infos_val_night.pkl'
RAW_DIR   = BASE / 'dataset/raw_images_night_original'
CLAHE_DIR = BASE / 'dataset/LLIE_images_CLAHE'
EGAN_DIR  = BASE / 'dataset/LLIE_images_EnlightenGAN'
ZDCE_DIR  = BASE / 'dataset/LLIE_images_ZeroDCE'
OUT_DIR   = BASE / 'analysis/outputs/llie_comparison'
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_CAM   = 'CAM_FRONT'
SCORE_THRESH = 0.3

NUSCENES_CLASSES = [
    'car', 'truck', 'construction_vehicle', 'bus', 'trailer',
    'barrier', 'motorcycle', 'bicycle', 'pedestrian', 'traffic_cone'
]

COND_LABELS = ['Original', 'CLAHE', 'EnlightenGAN', 'Zero-DCE']

SAMPLES = [
    (322, 'n015-2018-11-21-19-21-35+0800__CAM_FRONT__1542799582862460', 'bbox_llie_comparison.png'),
    (282, 'n015-2018-11-21-19-21-35+0800__CAM_FRONT__1542799562862460', 'bbox_llie_comparison2.png'),
    (537, 'n015-2018-11-21-19-21-35+0800__CAM_FRONT__1542799709912460', 'bbox_llie_comparison3.png'),
]

PRED_PKLS = {
    'MoME': [
        BASE / 'model/MoME/results/night_results.pkl',
        BASE / 'model/MoME/results/night_clahe_results.pkl',
        BASE / 'model/MoME/results/night_enlighten_results.pkl',
        BASE / 'model/MoME/results/night_zerodce_results.pkl',
    ],
    'DeepInteraction': [
        BASE / 'model/DeepInteraction/results/night_results.pkl',
        BASE / 'model/DeepInteraction/results/night_clahe_results.pkl',
        BASE / 'model/DeepInteraction/results/night_egan_results.pkl',
        BASE / 'model/DeepInteraction/results/night_zerodce_results.pkl',
    ],
    'BEVFusion': [
        BASE / 'model/BEVFusion/results/night_results.pkl',
        BASE / 'model/BEVFusion/results/night_clahe_results.pkl',
        BASE / 'model/BEVFusion/results/night_egan_results.pkl',
        BASE / 'model/BEVFusion/results/night_zerodce_results.pkl',
    ],
}

COLOR_GT   = (0,   220,  80)   # 초록
COLOR_MOME = (255,  50,  50)   # 빨강
COLOR_DI   = ( 50,  80, 255)   # 파랑
COLOR_BEV  = (255, 165,   0)   # 주황

MODEL_COLORS = {
    'MoME':             COLOR_MOME,
    'DeepInteraction':  COLOR_DI,
    'BEVFusion':        COLOR_BEV,
}


class SafeUnpickler(pickle.Unpickler):
    _cache = {}
    def find_class(self, module, name):
        try:
            return super().find_class(module, name)
        except (ImportError, AttributeError):
            key = (module, name)
            if key not in self._cache:
                self._cache[key] = type(name, (), {})
            return self._cache[key]


def load_pkl(path):
    with open(path, 'rb') as f:
        return SafeUnpickler(f).load()


def draw_box_on_image(img, box_coords, cam_intrinsic, calib_trans, calib_quat, color, thickness=2):
    """
    box_coords : [x, y, z, w, l, h, yaw]  in Ego frame
    calib_trans: camera sensor2ego translation (3,)
    calib_quat : camera sensor2ego quaternion (Quaternion)
    color      : RGB tuple
    """
    x, y, z, w, l, h, yaw = box_coords

    # 8 코너 (로컬 박스 프레임)
    corners = np.array([
        [ l/2,  w/2, -h/2], [ l/2, -w/2, -h/2],
        [-l/2, -w/2, -h/2], [-l/2,  w/2, -h/2],
        [ l/2,  w/2,  h/2], [ l/2, -w/2,  h/2],
        [-l/2, -w/2,  h/2], [-l/2,  w/2,  h/2],
    ]).T   # (3, 8)

    # Yaw 회전
    rot = np.array([
        [np.cos(yaw), -np.sin(yaw), 0],
        [np.sin(yaw),  np.cos(yaw), 0],
        [0,            0,           1]
    ])
    corners = rot @ corners
    corners[0] += x
    corners[1] += y
    corners[2] += z

    # Ego → Camera
    corners -= np.array(calib_trans).reshape(3, 1)
    cam_rot = calib_quat.inverse
    corners_cam = cam_rot.rotation_matrix @ corners

    # 카메라 앞에 있는 코너가 4개 이상이어야 그림
    if (corners_cam[2] > 0.1).sum() < 4:
        return img

    corners_cam[2] = np.maximum(corners_cam[2], 0.1)

    # 픽셀 투영
    pts_2d = cam_intrinsic @ corners_cam
    pts_2d = (pts_2d[:2] / pts_2d[2]).T.astype(int)   # (8, 2)

    edges = [(0,1),(1,2),(2,3),(3,0),
             (4,5),(5,6),(6,7),(7,4),
             (0,4),(1,5),(2,6),(3,7)]
    h_img, w_img = img.shape[:2]
    for s, e in edges:
        p1 = (int(np.clip(pts_2d[s][0], -2000, w_img+2000)),
              int(np.clip(pts_2d[s][1], -2000, h_img+2000)))
        p2 = (int(np.clip(pts_2d[e][0], -2000, w_img+2000)),
              int(np.clip(pts_2d[e][1], -2000, h_img+2000)))
        cv2.line(img, p1, p2, color, thickness, lineType=cv2.LINE_AA)

    return img


def annotate(img_bgr, info, pred_list_by_model, cam_key):
    """img_bgr → RGB annotated image"""
    # BGR → RGB (참고 코드와 동일하게, cv2.line은 RGB 배열에 직접 씀)
    img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    cam = info['cams'][cam_key]
    cam_intrinsic  = np.array(cam['cam_intrinsic'])
    calib_trans    = np.array(cam['sensor2ego_translation'])
    calib_quat     = Quaternion(cam['sensor2ego_rotation'])

    lidar2ego_rot   = Quaternion(info['lidar2ego_rotation']).rotation_matrix
    lidar2ego_trans = np.array(info['lidar2ego_translation'])
    lidar2ego_quat  = Quaternion(info['lidar2ego_rotation'])

    gt_boxes = np.array(info['gt_boxes'])
    gt_names = np.array(info['gt_names'])

    for box, name in zip(gt_boxes, gt_names):
        if name not in NUSCENES_CLASSES:
            continue
        # gt_boxes: [x,y,z,l,w,h,yaw] 3D center, LiDAR frame
        xyz_ego = lidar2ego_rot @ box[:3] + lidar2ego_trans
        l, w, h = box[3], box[4], box[5]
        gt_quat  = Quaternion(axis=[0, 0, 1], angle=box[6])
        yaw_ego  = (lidar2ego_quat * gt_quat).yaw_pitch_roll[0]

        draw_box_on_image(img, [xyz_ego[0], xyz_ego[1], xyz_ego[2], w, l, h, yaw_ego],
                          cam_intrinsic, calib_trans, calib_quat, COLOR_GT, thickness=2)

    for model_name, pb in pred_list_by_model.items():
        color = MODEL_COLORS[model_name]
        box_tensor = pb['boxes_3d'].tensor.numpy()
        scores     = pb['scores_3d'].numpy()
        labels     = pb['labels_3d'].numpy()

        # MoME/DeepInteraction: bottom-center → +h/2 보정 필요
        # BEVFusion: 이미 3D center 저장 → 보정 불필요
        z_correction = model_name != 'BEVFusion'

        for box, score, label_idx in zip(box_tensor, scores, labels):
            if score < SCORE_THRESH:
                continue
            box = box.copy()
            if z_correction:
                box[2] += box[5] / 2      # bottom → 3D center
            xyz_ego = lidar2ego_rot @ box[:3] + lidar2ego_trans
            l, w, h = box[3], box[4], box[5]
            pred_quat = Quaternion(axis=[0, 0, 1], angle=box[6])
            yaw_ego   = (lidar2ego_quat * pred_quat).yaw_pitch_roll[0]

            draw_box_on_image(img, [xyz_ego[0], xyz_ego[1], xyz_ego[2], w, l, h, yaw_ego],
                              cam_intrinsic, calib_trans, calib_quat, color, thickness=2)

    return img


def draw_sample(infos, all_preds, sample_idx, img_stem, out_filename):
    info = infos[sample_idx]
    img_paths = [
        RAW_DIR   / f'{img_stem}.jpg',
        CLAHE_DIR / f'clahe__{img_stem}.jpg',
        EGAN_DIR  / f'egan__{img_stem}.jpg',
        ZDCE_DIR  / f'zerodce__{img_stem}.jpg',
    ]

    fig, axes = plt.subplots(1, 4, figsize=(28, 7))

    for col, (img_path, cond_label) in enumerate(zip(img_paths, COND_LABELS)):
        print(f"    [{cond_label}]", end=' ', flush=True)
        img_bgr = cv2.imread(str(img_path))
        pred_by_model = {m: all_preds[m][col][sample_idx] for m in PRED_PKLS}
        annotated = annotate(img_bgr, info, pred_by_model, TARGET_CAM)
        axes[col].imshow(annotated)
        axes[col].set_title(cond_label, fontsize=13, fontweight='bold', pad=6)
        axes[col].axis('off')
    print()

    def to_mpl(c): return tuple(v/255 for v in c)
    legend_handles = [
        mpatches.Patch(color=to_mpl(COLOR_GT),   label='GT'),
        mpatches.Patch(color=to_mpl(COLOR_MOME), label='MoME'),
        mpatches.Patch(color=to_mpl(COLOR_DI),   label='DeepInteraction'),
        mpatches.Patch(color=to_mpl(COLOR_BEV),  label='BEVFusion'),
    ]
    fig.legend(handles=legend_handles, loc='lower center', ncol=4,
               fontsize=12, framealpha=0.9, bbox_to_anchor=(0.5, -0.04))
    fig.suptitle(
        f'3D BBox Projection — {TARGET_CAM}  |  nuScenes Night  |  score≥{SCORE_THRESH}',
        fontsize=14, fontweight='bold'
    )
    plt.tight_layout()
    out = OUT_DIR / out_filename
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {out}")


def main():
    print("Loading GT pkl...")
    infos = load_pkl(NIGHT_PKL)['infos']

    print("Loading all prediction pkls (once)...")
    all_preds = {}
    for model_name, pkl_list in PRED_PKLS.items():
        all_preds[model_name] = []
        for pkl_path in pkl_list:
            print(f"  {model_name}/{pkl_path.name}")
            preds = load_pkl(pkl_path)
            extracted = []
            for p in preds:
                pb = p['pts_bbox'] if 'pts_bbox' in p else p
                extracted.append(pb)
            all_preds[model_name].append(extracted)

    print()
    for sample_idx, img_stem, out_filename in SAMPLES:
        print(f"Drawing sample {sample_idx} → {out_filename}")
        draw_sample(infos, all_preds, sample_idx, img_stem, out_filename)


if __name__ == '__main__':
    main()
