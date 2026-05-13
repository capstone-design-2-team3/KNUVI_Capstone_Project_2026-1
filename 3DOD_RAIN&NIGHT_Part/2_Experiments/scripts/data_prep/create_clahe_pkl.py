"""CLAHE pkl 생성. run_clahe_night.py 실행 완료 후 사용."""
import os

from data_prep_utils import make_llie_pkl

NIGHT_PKL_PATH  = '/raid2/kyungjin/data/nuscenes/nuscenes_infos_val_night.pkl'
ENHANCED_ROOT   = '/raid2/kyungjin/data/nuscenes_clahe/samples'
OUTPUT_PKL_PATH = '/raid2/kyungjin/data/nuscenes/nuscenes_infos_val_night_clahe.pkl'


def resolve(img_name, cam):
    return os.path.join(ENHANCED_ROOT, cam, img_name)


if __name__ == '__main__':
    make_llie_pkl(NIGHT_PKL_PATH, OUTPUT_PKL_PATH, resolve)
