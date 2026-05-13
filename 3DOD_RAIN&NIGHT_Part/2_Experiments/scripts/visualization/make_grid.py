"""
LLIE 4 조건 비교 그리드 (bbox 없음).

visualize_bbox_llie.py 와 동일한 SAMPLES 항목에 대해 1행×4열 figure
(Original | CLAHE | EnlightenGAN | Zero-DCE) 를 생성. bbox는 그리지 않음.

bbox 포함 동일 layout 결과는 visualize_bbox_llie.py 가 만들며, 같은 SAMPLES
를 쓰므로 두 스크립트를 함께 돌리면 동일 샘플에 대해 bbox 유/무 비교 그리드를
짝지어 얻을 수 있다.
"""
import cv2
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE      = Path('/home/knuvi/Undergraduate/kyungjin')
RAW_DIR   = BASE / 'dataset/raw_images_night_original'
CLAHE_DIR = BASE / 'dataset/LLIE_images_CLAHE'
EGAN_DIR  = BASE / 'dataset/LLIE_images_EnlightenGAN'
ZDCE_DIR  = BASE / 'dataset/LLIE_images_ZeroDCE'
OUT_DIR   = BASE / 'analysis/outputs/llie_comparison'
OUT_DIR.mkdir(parents=True, exist_ok=True)

COND_LABELS = ['Original', 'CLAHE', 'EnlightenGAN', 'Zero-DCE']

# (image_stem, output_filename) — visualize_bbox_llie.py 의 SAMPLES 와 짝.
SAMPLES = [
    ('n015-2018-11-21-19-21-35+0800__CAM_FRONT__1542799582862460', 'llie_comparison.png'),
    ('n015-2018-11-21-19-21-35+0800__CAM_FRONT__1542799562862460', 'llie_comparison2.png'),
    ('n015-2018-11-21-19-21-35+0800__CAM_FRONT__1542799709912460', 'llie_comparison3.png'),
]


def img_paths_for(stem: str):
    return [
        RAW_DIR   / f'{stem}.jpg',
        CLAHE_DIR / f'clahe__{stem}.jpg',
        EGAN_DIR  / f'egan__{stem}.jpg',
        ZDCE_DIR  / f'zerodce__{stem}.jpg',
    ]


def draw_sample(stem: str, out_filename: str):
    fig, axes = plt.subplots(1, 4, figsize=(28, 7))
    for col, (path, label) in enumerate(zip(img_paths_for(stem), COND_LABELS)):
        img = cv2.imread(str(path))
        if img is None:
            axes[col].set_facecolor('#222222')
            axes[col].text(0.5, 0.5, 'N/A', ha='center', va='center',
                           transform=axes[col].transAxes, color='white')
        else:
            axes[col].imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        axes[col].set_title(label, fontsize=13, fontweight='bold', pad=6)
        axes[col].axis('off')

    fig.suptitle('LLIE Preprocessing Comparison — CAM_FRONT (nuScenes Night)',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    out = OUT_DIR / out_filename
    fig.savefig(out, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {out}")


def main():
    for stem, out_filename in SAMPLES:
        print(f"Drawing {stem} → {out_filename}")
        draw_sample(stem, out_filename)


if __name__ == '__main__':
    main()
