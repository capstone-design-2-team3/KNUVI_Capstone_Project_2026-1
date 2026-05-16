# analyzer.py

import os
import numpy as np
import pandas as pd
from tqdm import tqdm

def analyze_pointcloud(bin_path):

    pts = np.fromfile(
        bin_path,
        dtype=np.float32
    ).reshape(-1, 4)

    if len(pts) == 0:
        return {
            "num_points": 0,
            "mean_distance": 0,
            "max_distance": 0,
            "min_distance": 0,
        }

    xyz = pts[:, :3]

    dist = np.linalg.norm(xyz, axis=1)

    result = {
        "num_points": len(pts),
        "mean_distance": float(dist.mean()),
        "max_distance": float(dist.max()),
        "min_distance": float(dist.min()),
    }

    return result

def analyze_directory(pc_dir):

    frames = sorted([
        f for f in os.listdir(pc_dir)
        if f.endswith(".bin")
    ])

    results = []

    for frame in tqdm(frames):

        path = os.path.join(pc_dir, frame)

        metrics = analyze_pointcloud(path)

        metrics["frame"] = frame

        results.append(metrics)

    df = pd.DataFrame(results)

    os.makedirs("./results", exist_ok=True)

    df.to_csv(
        "./results/analysis.csv",
        index=False
    )

    print(df.mean(numeric_only=True))

if __name__ == "__main__":

    analyze_directory("./infer_velodyne")
