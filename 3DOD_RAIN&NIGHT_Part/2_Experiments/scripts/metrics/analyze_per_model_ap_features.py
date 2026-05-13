"""
모델별 AP 기준 Hard/Easy 그룹 특성 분석

ap_matrix.npy (602, 3, 4): axis1=model(MoME/DI/BEVFusion), axis2=condition
각 모델에서 avg_ap = nanmean(ap_mat[:, m, :], axis=1) → q25=Hard, q75=Easy
특성은 602개 샘플에 대해 1회 계산 후 모델별 그룹에 재적용
"""
import pickle, numpy as np
from pathlib import Path
from scipy.stats import mannwhitneyu

from feature_utils import image_quality, lidar_quality, IMG_KEYS, SCN_KEYS

BASE     = Path('/home/knuvi/Undergraduate/kyungjin')
GT_PKL   = BASE / 'model/MoME/data/nuscenes/nuscenes_infos_val_night.pkl'
IMG_BASE = BASE / 'model/MoME'
AP_MAT   = BASE / 'analysis/outputs/ap_difficulty/ap_matrix.npy'
OUT_CSV  = BASE / 'analysis/outputs/per_model_ap_features.csv'

MODEL_NAMES = ['MoME', 'DeepInteraction', 'BEVFusion']


def print_table(model_name, hard_idx, easy_idx, all_idx, data, keys):
    print(f"\n=== {model_name} (Hard={len(hard_idx)}, Easy={len(easy_idx)}) ===")
    print(f"{'Metric':<22} {'Hard (mean±std)':>20} {'Easy (mean±std)':>20} {'Overall':>10} {'p-value':>10} {'sig':>4}")
    print('-' * 92)
    img_printed, scn_printed = False, False
    for fi, key in enumerate(keys):
        if not img_printed and key in IMG_KEYS:
            print('[이미지 품질]')
            img_printed = True
        elif not scn_printed and key in SCN_KEYS:
            print('[씬 특징]')
            scn_printed = True
        col = data[:, fi]
        h  = col[hard_idx]; h  = h[~np.isnan(h)]
        e  = col[easy_idx]; e  = e[~np.isnan(e)]
        ov = col[all_idx];  ov = ov[~np.isnan(ov)]
        if len(h) >= 2 and len(e) >= 2:
            _, p = mannwhitneyu(h, e, alternative='two-sided')
            sig  = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
            p_str = f'{p:.2e}'
        else:
            p_str, sig = 'nan', ''
        print(f"  {key:<20}  {h.mean():>7.4f}±{h.std():<8.4f}  {e.mean():>7.4f}±{e.std():<8.4f}  {ov.mean():>8.4f}  {p_str:>10} {sig:>3}")


def main():
    print("Loading GT pkl...")
    with open(GT_PKL, 'rb') as f:
        gt_infos = pickle.load(f)['infos']
    ap_mat = np.load(AP_MAT)   # (602, 3, 4)
    N = len(gt_infos)

    print(f"Computing features for {N} samples...")
    all_keys = IMG_KEYS + SCN_KEYS
    feats = []
    for i, gt_info in enumerate(gt_infos):
        if i % 100 == 0:
            print(f"  [{i}/{N}]")
        img_path = IMG_BASE / gt_info['cams']['CAM_FRONT']['data_path']
        iq = image_quality(img_path)
        lq = lidar_quality(gt_info)
        feats.append([iq[k] for k in IMG_KEYS] + [lq[k] for k in SCN_KEYS])
    data = np.array(feats, dtype=float)   # (602, 12)

    import csv
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    csv_rows = []

    for mi, mname in enumerate(MODEL_NAMES):
        avg_ap = np.nanmean(ap_mat[:, mi, :], axis=1)   # (602,)
        q25, q75 = np.nanpercentile(avg_ap, 25), np.nanpercentile(avg_ap, 75)
        hard_idx = np.where(avg_ap <= q25)[0]
        easy_idx = np.where(avg_ap >= q75)[0]
        all_idx  = np.arange(N)

        print_table(mname, hard_idx, easy_idx, all_idx, data, all_keys)

        for fi, key in enumerate(all_keys):
            col = data[:, fi]
            h  = col[hard_idx]; h  = h[~np.isnan(h)]
            e  = col[easy_idx]; e  = e[~np.isnan(e)]
            ov = col[all_idx];  ov = ov[~np.isnan(ov)]
            if len(h) >= 2 and len(e) >= 2:
                _, p = mannwhitneyu(h, e, alternative='two-sided')
                sig  = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
                p_val = f'{p:.2e}'
            else:
                p_val, sig = 'nan', ''
            csv_rows.append([mname, key,
                              f'{h.mean():.4f}', f'{h.std():.4f}',
                              f'{e.mean():.4f}', f'{e.std():.4f}',
                              f'{ov.mean():.4f}', f'{ov.std():.4f}',
                              p_val, sig])

    with open(OUT_CSV, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['model', 'metric',
                         'hard_mean', 'hard_std', 'easy_mean', 'easy_std',
                         'overall_mean', 'overall_std', 'p_value', 'sig'])
        writer.writerows(csv_rows)
    print(f"\nCSV saved: {OUT_CSV}")


if __name__ == '__main__':
    main()
