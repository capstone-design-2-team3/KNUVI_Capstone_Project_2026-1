"""
야간 nuScenes 이미지에 CLAHE를 적용하는 스크립트.

원본 야간 pkl에서 경로를 읽어 이미지를 처리하고
/raid2/kyungjin/data/nuscenes_clahe/samples/{CAM}/ 에 저장.

실행:
    python run_clahe_night.py
"""

import os
import pickle
import cv2
import numpy as np
from tqdm import tqdm

from data_prep_utils import CAMERAS

NIGHT_PKL_PATH = '/raid2/kyungjin/data/nuscenes/nuscenes_infos_val_night.pkl'
OUTPUT_ROOT    = '/raid2/kyungjin/data/nuscenes_clahe/samples'

# pkl의 data_path가 './data/nuscenes/...' 같은 상대경로일 때 절대경로로 변환하기 위한 base
DATA_ROOT = '/raid2/kyungjin/data/nuscenes'

CLAHE_CLIP_LIMIT  = 2.0
CLAHE_TILE_GRID   = (8, 8)


def apply_clahe(img_bgr: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP_LIMIT, tileGridSize=CLAHE_TILE_GRID)
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def main():
    for cam in CAMERAS:
        os.makedirs(os.path.join(OUTPUT_ROOT, cam), exist_ok=True)

    print(f'[INFO] pkl 로드: {NIGHT_PKL_PATH}')
    with open(NIGHT_PKL_PATH, 'rb') as f:
        data = pickle.load(f)

    infos = data['infos']

    paths = {}  # img_name -> (orig_path, cam)
    for info in infos:
        for cam in CAMERAS:
            cam_info = info['cams'].get(cam)
            if cam_info is None:
                continue
            orig_path = cam_info['data_path']
            img_name  = os.path.basename(orig_path)
            paths[img_name] = (orig_path, cam)

    print(f'[INFO] 처리할 이미지 수: {len(paths)}')

    ok_count   = 0
    fail_count = 0

    for img_name, (orig_path, cam) in tqdm(paths.items(), desc='CLAHE'):
        out_path = os.path.join(OUTPUT_ROOT, cam, img_name)

        if os.path.exists(out_path):
            ok_count += 1
            continue

        # 상대경로 처리: './data/nuscenes/...' -> 절대경로
        if not os.path.isabs(orig_path):
            rel = orig_path.replace('./data/nuscenes/', '', 1)
            abs_path = os.path.join(DATA_ROOT, rel)
        else:
            abs_path = orig_path

        img = cv2.imread(abs_path)
        if img is None:
            print(f'[WARN] 읽기 실패: {abs_path}')
            fail_count += 1
            continue

        enhanced = apply_clahe(img)
        cv2.imwrite(out_path, enhanced)
        ok_count += 1

    print(f'[완료] 성공: {ok_count}, 실패: {fail_count}')
    print(f'저장 위치: {OUTPUT_ROOT}')


if __name__ == '__main__':
    main()
