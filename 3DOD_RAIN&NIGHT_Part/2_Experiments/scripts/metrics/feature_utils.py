"""
Shared utilities for night-evaluation scripts.

Image / scene features:
  image_quality          : 7 image-domain metrics from a CAM_FRONT image.
  lidar_quality          : 5 LiDAR/scene metrics from a nuScenes gt_info dict.

AP / mAP (nuScenes-style center-distance matching):
  compute_per_sample_ap  : per-sample mean AP across detected classes.
  compute_group_map      : group-level mAP over a set of sample indices.

Pickle loading:
  load_pkl               : safe loader that tolerates missing mmdet3d classes
                           and normalises BEVFusion-style bare-dict outputs.

Shared constants:
  NUSCENES_CLASSES, IMG_KEYS, SCN_KEYS, DIST_THRESH
"""
import pickle
import numpy as np
import cv2
from pathlib import Path
from scipy.stats import entropy as scipy_entropy

NUSCENES_CLASSES = [
    'car', 'truck', 'construction_vehicle', 'bus', 'trailer',
    'barrier', 'motorcycle', 'bicycle', 'pedestrian', 'traffic_cone'
]

IMG_KEYS = ['luminance', 'rms_contrast', 'entropy', 'underexp_ratio',
            'laplacian_var', 'noise_est', 'illum_uniformity']
SCN_KEYS = ['total_lidar_pts', 'mean_dist', 'mean_pts_per_obj',
            'small_obj_ratio', 'gt_obj_count']

DIST_THRESH = 2.0


def image_quality(img_path: Path) -> dict:
    img = cv2.imread(str(img_path))
    if img is None:
        return {k: np.nan for k in IMG_KEYS}
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    h, w = gray.shape
    ph, pw = h // 5, w // 5
    patch_stds  = [gray[i*ph:(i+1)*ph, j*pw:(j+1)*pw].std()  for i in range(5) for j in range(5)]
    patch_means = [gray[i*ph:(i+1)*ph, j*pw:(j+1)*pw].mean() for i in range(5) for j in range(5)]
    hist, _ = np.histogram(gray.ravel(), bins=256, range=(0, 256), density=True)
    hist += 1e-12
    return {
        'luminance':        gray.mean(),
        'rms_contrast':     gray.std(),
        'entropy':          float(scipy_entropy(hist)),
        'underexp_ratio':   (gray < 20).mean(),
        'laplacian_var':    cv2.Laplacian(gray.astype(np.uint8), cv2.CV_64F).var(),
        'noise_est':        np.percentile(patch_stds, 10),
        'illum_uniformity': np.std(patch_means),
    }


def lidar_quality(gt_info: dict) -> dict:
    boxes = np.array(gt_info['gt_boxes'])
    npts  = np.array(gt_info['num_lidar_pts'])
    valid = gt_info['valid_flag']
    boxes, npts = boxes[valid], npts[valid]
    N = len(boxes)
    if N == 0:
        return {k: np.nan for k in SCN_KEYS}
    dist = np.sqrt((boxes[:, :2] ** 2).sum(axis=1))
    area = boxes[:, 3] * boxes[:, 4]
    return {
        'total_lidar_pts':  float(npts.sum()),
        'mean_dist':        dist.mean(),
        'mean_pts_per_obj': npts.mean(),
        'small_obj_ratio':  (area < 2.0).mean(),
        'gt_obj_count':     float(N),
    }


def _pr_to_ap(precision, recall):
    if len(precision) == 0:
        return 0.0
    prec = np.concatenate([[0.0], precision])
    rec  = np.concatenate([[0.0], recall])
    return float(np.trapz(prec, rec))


def compute_per_sample_ap(gt_infos, pred_list, dist_thresh=DIST_THRESH):
    """Returns (N,) array of per-sample mean AP across NUSCENES_CLASSES.

    nan when a sample has no valid GT.
    """
    N = len(gt_infos)
    ap_arr = np.full(N, np.nan)

    for i, (gt_info, pred) in enumerate(zip(gt_infos, pred_list)):
        gt_boxes = np.array(gt_info['gt_boxes'])
        gt_names = np.array(gt_info['gt_names'])
        valid_gt = np.array([n in NUSCENES_CLASSES for n in gt_names])
        gt_boxes_f = gt_boxes[valid_gt]
        gt_names_f = gt_names[valid_gt]

        if len(gt_boxes_f) == 0:
            continue

        gt_labels  = np.array([NUSCENES_CLASSES.index(n) for n in gt_names_f])
        gt_centers = gt_boxes_f[:, :2]

        pb = pred['pts_bbox']
        pred_boxes_np  = pb['boxes_3d'].tensor[:, :7].numpy()
        pred_scores_np = pb['scores_3d'].numpy()
        pred_labels_np = pb['labels_3d'].numpy()
        pred_centers   = pred_boxes_np[:, :2]

        diff = gt_centers[:, None, :] - pred_centers[None, :, :]
        dist_mat = np.sqrt((diff ** 2).sum(-1))

        class_aps = []
        for cls_idx in np.unique(gt_labels):
            cls_gt_mask   = gt_labels == cls_idx
            cls_pred_mask = pred_labels_np == cls_idx
            n_gt_cls = int(cls_gt_mask.sum())

            if cls_pred_mask.sum() == 0:
                class_aps.append(0.0)
                continue

            cls_scores = pred_scores_np[cls_pred_mask]
            cls_dist   = dist_mat[np.ix_(np.where(cls_gt_mask)[0],
                                         np.where(cls_pred_mask)[0])]

            sort_idx = np.argsort(-cls_scores)
            detected = np.zeros(n_gt_cls, dtype=bool)
            tp_arr   = np.zeros(len(sort_idx))

            for rank, pi in enumerate(sort_idx):
                dists = cls_dist[:, pi]
                cands = np.where((~detected) & (dists <= dist_thresh))[0]
                if len(cands) > 0:
                    gi = cands[np.argmin(dists[cands])]
                    detected[gi] = True
                    tp_arr[rank] = 1

            cum_tp    = np.cumsum(tp_arr)
            cum_fp    = np.cumsum(1 - tp_arr)
            precision = cum_tp / (cum_tp + cum_fp + 1e-10)
            recall    = cum_tp / n_gt_cls

            class_aps.append(_pr_to_ap(precision, recall))

        ap_arr[i] = float(np.mean(class_aps)) if class_aps else np.nan

    return ap_arr


def compute_group_map(indices, gt_infos, pred_list, dist_thresh=DIST_THRESH):
    """Group-level mAP across the given sample indices.

    Returns {'mAP': float, 'per_class': {class_name: AP, ...}}.
    """
    class_aps = {}

    for cls_idx, cls_name in enumerate(NUSCENES_CLASSES):
        global_preds = []
        n_total_gt   = 0
        gt_by_sample = {}

        for i in indices:
            gt_info  = gt_infos[i]
            pred     = pred_list[i]
            gt_boxes = np.array(gt_info['gt_boxes'])
            gt_names = np.array(gt_info['gt_names'])
            valid_gt = np.array([n in NUSCENES_CLASSES for n in gt_names])
            gt_boxes = gt_boxes[valid_gt]
            gt_names = gt_names[valid_gt]

            if len(gt_names) > 0:
                gt_labels   = np.array([NUSCENES_CLASSES.index(n) for n in gt_names])
                cls_gt_mask = gt_labels == cls_idx
                n_gt_cls    = int(cls_gt_mask.sum())
                n_total_gt += n_gt_cls
                gt_centers  = gt_boxes[cls_gt_mask, :2] if n_gt_cls > 0 else np.zeros((0, 2))
            else:
                n_gt_cls   = 0
                gt_centers = np.zeros((0, 2))

            gt_by_sample[i] = [gt_centers, np.zeros(n_gt_cls, dtype=bool)]

            pb = pred['pts_bbox']
            pred_boxes_np  = pb['boxes_3d'].tensor[:, :7].numpy()
            pred_scores_np = pb['scores_3d'].numpy()
            pred_labels_np = pb['labels_3d'].numpy()
            cls_pred_mask  = pred_labels_np == cls_idx

            for score, center in zip(pred_scores_np[cls_pred_mask],
                                     pred_boxes_np[cls_pred_mask, :2]):
                global_preds.append((float(score), i, float(center[0]), float(center[1])))

        if n_total_gt == 0:
            class_aps[cls_name] = np.nan
            continue
        if not global_preds:
            class_aps[cls_name] = 0.0
            continue

        global_preds.sort(key=lambda x: -x[0])
        tp_arr = np.zeros(len(global_preds))

        for rank, (score, sample_i, px, py) in enumerate(global_preds):
            gt_centers, detected = gt_by_sample[sample_i]
            if len(gt_centers) == 0:
                continue
            dists = np.sqrt(((gt_centers - np.array([px, py])) ** 2).sum(-1))
            cands = np.where((~detected) & (dists <= dist_thresh))[0]
            if len(cands) > 0:
                gi = cands[np.argmin(dists[cands])]
                detected[gi] = True
                tp_arr[rank] = 1

        cum_tp    = np.cumsum(tp_arr)
        cum_fp    = np.cumsum(1 - tp_arr)
        precision = cum_tp / (cum_tp + cum_fp + 1e-10)
        recall    = cum_tp / n_total_gt

        class_aps[cls_name] = _pr_to_ap(precision, recall)

    valid_aps = [v for v in class_aps.values() if not np.isnan(v)]
    map_val = float(np.mean(valid_aps)) if valid_aps else np.nan
    return {'mAP': map_val, 'per_class': class_aps}


class _SafeUnpickler(pickle.Unpickler):
    """Handles missing mmdet3d classes by creating placeholder types."""
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
    """Safe pickle load. Normalises BEVFusion-style bare dicts to {'pts_bbox': ...}."""
    with open(path, 'rb') as f:
        data = _SafeUnpickler(f).load()
    if isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], dict) and 'boxes_3d' in data[0]:
            data = [{'pts_bbox': item} for item in data]
    return data
