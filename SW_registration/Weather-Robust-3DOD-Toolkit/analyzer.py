# analyzer.py

import os
import json
import numpy as np
import pandas as pd
from tqdm import tqdm

SCN_KEYS = [
    'total_lidar_pts',
    'mean_dist',
    'mean_pts_per_obj',
    'small_obj_ratio',
    'gt_obj_count'
]

def lidar_quality(gt_info: dict) -> dict:
    boxes = np.array(gt_info['gt_boxes'])
    npts  = np.array(gt_info['num_lidar_pts'])

    valid = gt_info['valid_flag']

    boxes = boxes[valid]
    npts = npts[valid]

    N = len(boxes)

    if N == 0:
        return {k: np.nan for k in SCN_KEYS}

    dist = np.sqrt((boxes[:, :2] ** 2).sum(axis=1))
    area = boxes[:, 3] * boxes[:, 4]

    return {
        'total_lidar_pts': float(npts.sum()),
        'mean_dist': float(dist.mean()),
        'mean_pts_per_obj': float(npts.mean()),
        'small_obj_ratio': float((area < 2.0).mean()),
        'gt_obj_count': float(N),
    }

def analyze_dataset(dataset_infos, save_path="./analysis.csv"):

    results = []

    for info in tqdm(dataset_infos):
        metrics = lidar_quality(info)
        results.append(metrics)

    df = pd.DataFrame(results)

    df.to_csv(save_path, index=False)

    print(f"saved : {save_path}")

    return df

if __name__ == "__main__":

    # example
    dummy_infos = []

    analyze_dataset(dummy_infos)
