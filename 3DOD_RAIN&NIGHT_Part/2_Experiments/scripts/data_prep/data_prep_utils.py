"""
Shared utilities for nuScenes night LLIE pkl preparation.

CAMERAS         : nuScenes 6 카메라 키.
make_llie_pkl   : 야간 GT pkl을 deep-copy하고 cam_info['data_path']를 LLIE 변환
                  이미지 경로로 교체한 새 pkl 저장.

사용 예 (CLAHE / Zero-DCE: cam별 폴더):
    def resolve(img_name, cam):
        return os.path.join(ENHANCED_ROOT, cam, img_name)
    make_llie_pkl(NIGHT_PKL, OUTPUT_PKL, resolve)

사용 예 (EnlightenGAN: flat 디렉토리):
    files = set(os.listdir(ENHANCED_ROOT))
    def resolve(img_name, cam):
        return os.path.join(ENHANCED_ROOT, img_name)
    def in_set(path):
        return os.path.basename(path) in files
    make_llie_pkl(NIGHT_PKL, OUTPUT_PKL, resolve, in_set)
"""
import copy
import os
import pickle
from typing import Callable, Optional

CAMERAS = [
    'CAM_FRONT', 'CAM_FRONT_RIGHT', 'CAM_FRONT_LEFT',
    'CAM_BACK',  'CAM_BACK_LEFT',   'CAM_BACK_RIGHT',
]


def make_llie_pkl(orig_pkl: str,
                  output_pkl: str,
                  resolve_path: Callable[[str, str], str],
                  exists_fn: Optional[Callable[[str], bool]] = None) -> None:
    """야간 GT pkl을 LLIE 변환 이미지 경로로 다시 쓴 새 pkl로 저장.

    resolve_path(img_name, cam) -> enhanced full path
    exists_fn(path) -> bool   (default: os.path.exists)
    """
    if exists_fn is None:
        exists_fn = os.path.exists

    print(f'[INFO] 원본 pkl 로드: {orig_pkl}')
    with open(orig_pkl, 'rb') as f:
        data = pickle.load(f)

    new_data = copy.deepcopy(data)
    infos = new_data['infos']

    updated = 0
    missing = 0
    for info in infos:
        for cam in CAMERAS:
            cam_info = info['cams'].get(cam)
            if cam_info is None:
                continue
            img_name = os.path.basename(cam_info['data_path'])
            enhanced_path = resolve_path(img_name, cam)
            if enhanced_path and exists_fn(enhanced_path):
                cam_info['data_path'] = enhanced_path
                updated += 1
            else:
                missing += 1

    print(f'[INFO] 업데이트: {updated}개, 미생성(원본 유지): {missing}개')
    print(f'[INFO] 새 pkl 저장: {output_pkl}')
    with open(output_pkl, 'wb') as f:
        pickle.dump(new_data, f)
    print('[완료]')
