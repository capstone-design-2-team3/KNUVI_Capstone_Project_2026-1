# python3 psnr_ssim_lpipls_score.py --gt_dir gt --pred_dir pred --multi_compare --output_csv results.csv

import os
import numpy as np
from PIL import Image
from tqdm import tqdm
from skimage.metrics import peak_signal_noise_ratio as compare_psnr
from skimage.metrics import structural_similarity as compare_ssim

import torch
import lpips
from torchvision import transforms

def load_image(path, for_lpips=False):
    """Normalize image to [0,1] or convert to tensor for LPIPS"""
    img = Image.open(path).convert('RGB')

    if for_lpips:
        transform = transforms.Compose([
            transforms.ToTensor(),  # [0,1]
            transforms.Normalize([0.5]*3, [0.5]*3)  # [-1,1] for LPIPS
        ])
        return transform(img).unsqueeze(0)  # (1, 3, H, W)
    else:
        return np.array(img).astype(np.float32) / 255.0

def compute_all_metrics(gt_dir, pred_dir, lpips_net='alex'):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    loss_fn = lpips.LPIPS(net=lpips_net).to(device).eval()

    gt_images = sorted([f for f in os.listdir(gt_dir) if f.endswith(('png', 'jpg', 'jpeg')) and not f.startswith('._')])
    pred_images = sorted([f for f in os.listdir(pred_dir) if f.endswith(('png', 'jpg', 'jpeg')) and not f.startswith('._')])

    if len(gt_images) != len(pred_images):
        raise ValueError("GT and prediction folders must contain the same number of images.")

    psnr_list, ssim_list, lpips_list = [], [], []
    for gt_img, pred_img in tqdm(zip(gt_images, pred_images), total=len(gt_images), desc='Computing Metrics'):
        gt_path = os.path.join(gt_dir, gt_img)
        pred_path = os.path.join(pred_dir, pred_img)

        # Load for PSNR/SSIM
        gt_np = load_image(gt_path)
        pred_np = load_image(pred_path)

        if gt_np.shape != pred_np.shape:
            raise ValueError(f"Shape mismatch: {gt_img} vs {pred_img}")

        psnr_val = compare_psnr(gt_np, pred_np, data_range=1.0)
        ssim_val = compare_ssim(gt_np, pred_np, data_range=1.0, channel_axis=2)

        psnr_list.append(psnr_val)
        ssim_list.append(ssim_val)

        # Load for LPIPS
        gt_tensor = load_image(gt_path, for_lpips=True).to(device)
        pred_tensor = load_image(pred_path, for_lpips=True).to(device)

        with torch.no_grad():
            lpips_val = loss_fn(gt_tensor, pred_tensor).item()
        lpips_list.append(lpips_val)

    avg_psnr = np.mean(psnr_list)
    avg_ssim = np.mean(ssim_list)
    avg_lpips = np.mean(lpips_list)

    print(f'Average PSNR:  {avg_psnr:.3f} dB')
    print(f'Average SSIM:  {avg_ssim:.3f}')
    print(f'Average LPIPS: {avg_lpips:.3f} ({lpips_net})')

    return avg_psnr, avg_ssim, avg_lpips

def compare_multiple_folders(gt_dir, pred_dir, lpips_net='alex', output_csv=None):
    """Automatically compare subfolders in GT and pred folders"""
    import glob
    import pandas as pd
    
    # Find subfolders in pred folder
    subfolders = sorted(glob.glob(os.path.join(pred_dir, '*')))
    subfolders = [f for f in subfolders if os.path.isdir(f)]
    
    if not subfolders:
        print(f"No subfolders found in {pred_dir}")
        return
    
    print(f"Found {len(subfolders)} subfolders in {pred_dir}:")
    for folder in subfolders:
        print(f"  - {os.path.basename(folder)}")
    
    results = []
    
    for subfolder in subfolders:
        folder_name = os.path.basename(subfolder)
        print(f"\n{'='*50}")
        print(f"Comparing GT with {folder_name}")
        print(f"{'='*50}")
        
        try:
            psnr, ssim, lpips = compute_all_metrics(gt_dir, subfolder, lpips_net)
            results.append({
                'folder': folder_name,
                'psnr': psnr,
                'ssim': ssim,
                'lpips': lpips
            })
        except Exception as e:
            print(f"Error comparing {folder_name}: {e}")
            results.append({
                'folder': folder_name,
                'psnr': None,
                'ssim': None,
                'lpips': None,
                'error': str(e)
            })
    
    # Print result summary
    print(f"\n{'='*60}")
    print("SUMMARY RESULTS")
    print(f"{'='*60}")
    print(f"{'Folder':<15} {'PSNR (dB)':<12} {'SSIM':<10} {'LPIPS':<10}")
    print("-" * 60)
    
    for result in results:
        if result['psnr'] is not None:
            print(f"{result['folder']:<15} {result['psnr']:<12.3f} {result['ssim']:<10.3f} {result['lpips']:<10.3f}")
        else:
            print(f"{result['folder']:<15} {'ERROR':<12} {'ERROR':<10} {'ERROR':<10}")
    
    # Save to CSV file
    if output_csv:
        df = pd.DataFrame(results)
        # Round to 3 decimal places
        for col in ['psnr', 'ssim', 'lpips']:
            if col in df.columns:
                df[col] = df[col].round(3)
        # CSV column order: folder, PSNR, SSIM, LPIPS, error (if exists)
        ordered_cols = [c for c in ['folder', 'psnr', 'ssim', 'lpips', 'error'] if c in df.columns]
        df = df[ordered_cols]
        df.to_csv(output_csv, index=False)
        print(f"\nResults saved to: {output_csv}")
    
    return results

def parse_source_txt(source_txt_path):
    """Parse source.txt and return gt directory and list of (display_name, pred_directory)

    Format example:
    gt
    /path/to/gt_dir
    pred
    Display Name 1
    /path/to/pred_dir1
    Display Name 2
    /path/to/pred_dir2
    ...
    """
    if not os.path.isfile(source_txt_path):
        raise FileNotFoundError(f"source file not found: {source_txt_path}")

    with open(source_txt_path, 'r') as f:
        # Ignore empty lines and comment lines (starting with #)
        lines = []
        for raw in f.readlines():
            stripped = raw.strip()
            if not stripped:
                continue
            if stripped.startswith('#'):
                continue
            lines.append(stripped)

    mode = None
    gt_dir = None
    pred_entries = []  # list of dicts: {name: str, dir: str}
    pending_name = None

    for line in lines:
        lower = line.lower()
        if lower == 'gt':
            mode = 'gt'
            continue
        if lower == 'pred':
            mode = 'pred'
            continue

        if mode == 'gt':
            if gt_dir is None:
                gt_dir = line
            else:
                # Do not allow multiple GT directories
                raise ValueError("Multiple GT directories specified in source file.")
        elif mode == 'pred':
            if pending_name is None:
                pending_name = line
            else:
                pred_entries.append({'name': pending_name, 'dir': line})
                pending_name = None
        else:
            # Prevent paths from coming before 'gt' or 'pred' keywords
            raise ValueError("Invalid format in source file. Expected 'gt' or 'pred' sections.")

    if gt_dir is None:
        raise ValueError("GT directory not specified in source file.")
    if pending_name is not None:
        raise ValueError("Dangling display name without a directory under 'pred' section.")
    if not pred_entries:
        raise ValueError("No prediction entries specified in source file.")

    if not os.path.isdir(gt_dir):
        raise NotADirectoryError(f"GT directory does not exist: {gt_dir}")
    for entry in pred_entries:
        p = entry['dir']
        if not os.path.isdir(p):
            raise NotADirectoryError(f"Prediction directory does not exist: {p}")

    return gt_dir, pred_entries

def compare_with_list(gt_dir, pred_entries, lpips_net='alex', output_csv=None):
    """Compare GT directory with given list of (display_name, pred_directory)"""
    import pandas as pd

    print(f"Found {len(pred_entries)} prediction entries from source file:")
    for e in pred_entries:
        print(f"  - {e['name']}: {e['dir']}")

    results = []

    for entry in pred_entries:
        pred_dir = entry['dir']
        display_name = entry['name'] or (os.path.basename(pred_dir.rstrip(os.sep)) or pred_dir)
        print(f"\n{'='*50}")
        print(f"Comparing GT with {display_name}")
        print(f"{'='*50}")

        try:
            psnr, ssim, lpips_val = compute_all_metrics(gt_dir, pred_dir, lpips_net)
            results.append({
                'folder': display_name,
                'psnr': psnr,
                'ssim': ssim,
                'lpips': lpips_val
            })
        except Exception as e:
            print(f"Error comparing {display_name}: {e}")
            results.append({
                'folder': display_name,
                'psnr': None,
                'ssim': None,
                'lpips': None,
                'error': str(e)
            })

    print(f"\n{'='*60}")
    print("SUMMARY RESULTS")
    print(f"{'='*60}")
    print(f"{'Folder':<15} {'PSNR (dB)':<12} {'SSIM':<10} {'LPIPS':<10}")
    print("-" * 60)

    for result in results:
        if result.get('psnr') is not None:
            print(f"{result['folder']:<15} {result['psnr']:<12.3f} {result['ssim']:<10.3f} {result['lpips']:<10.3f}")
        else:
            print(f"{result['folder']:<15} {'ERROR':<12} {'ERROR':<10} {'ERROR':<10}")

    if output_csv:
        df = pd.DataFrame(results)
        for col in ['psnr', 'ssim', 'lpips']:
            if col in df.columns:
                df[col] = df[col].round(3)
        ordered_cols = [c for c in ['folder', 'psnr', 'ssim', 'lpips', 'error'] if c in df.columns]
        df = df[ordered_cols]
        df.to_csv(output_csv, index=False)
        print(f"\nResults saved to: {output_csv}")

    return results

# Example execution
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--gt_dir', type=str, help='Ground truth image folder')
    parser.add_argument('--pred_dir', type=str, help='Predicted/rendered image folder')
    parser.add_argument('--lpips_net', type=str, default='alex', choices=['alex', 'vgg', 'squeeze'], help='LPIPS network backbone')
    parser.add_argument('--multi_compare', action='store_true', help='Compare GT with all subfolders in pred directory')
    parser.add_argument('--output_csv', type=str, help='Output CSV file for results')
    parser.add_argument('--source_txt', type=str, help='Path to source.txt listing gt and pred directories')
    args = parser.parse_args()

    if args.source_txt:
        gt_dir, pred_entries = parse_source_txt(args.source_txt)
        compare_with_list(gt_dir, pred_entries, args.lpips_net, args.output_csv)
    elif args.multi_compare:
        if not args.gt_dir or not args.pred_dir:
            raise SystemExit("--multi_compare requires --gt_dir and --pred_dir")
        compare_multiple_folders(args.gt_dir, args.pred_dir, args.lpips_net, args.output_csv)
    else:
        if not args.gt_dir or not args.pred_dir:
            raise SystemExit("Single comparison requires --gt_dir and --pred_dir or use --source_txt")
        compute_all_metrics(args.gt_dir, args.pred_dir, args.lpips_net)
