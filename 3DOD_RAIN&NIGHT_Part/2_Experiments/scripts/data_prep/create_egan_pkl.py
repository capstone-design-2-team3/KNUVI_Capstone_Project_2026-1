"""EnlightenGAN pkl 생성.

testA/는 카메라 서브폴더 없이 파일명에 카메라명 포함된 flat 구조.
예: n015-2018-...__CAM_FRONT__1542799322112460.jpg
"""
import os

from data_prep_utils import make_llie_pkl

NIGHT_PKL_PATH  = '/raid2/kyungjin/data/nuscenes/nuscenes_infos_val_night.pkl'
ENHANCED_ROOT   = '/home/knuvi/Undergraduate/kyungjin/test_dataset/testA'
OUTPUT_PKL_PATH = '/raid2/kyungjin/data/nuscenes/nuscenes_infos_val_night_egan.pkl'

# flat dir 의 파일명을 set으로 미리 캐시 (in-set 검사용)
_enhanced_files = set(os.listdir(ENHANCED_ROOT)) if os.path.isdir(ENHANCED_ROOT) else set()


def resolve(img_name, cam):  # cam 미사용 (flat 구조)
    return os.path.join(ENHANCED_ROOT, img_name)


def exists_in_set(path):
    return os.path.basename(path) in _enhanced_files


if __name__ == '__main__':
    make_llie_pkl(NIGHT_PKL_PATH, OUTPUT_PKL_PATH, resolve, exists_in_set)
