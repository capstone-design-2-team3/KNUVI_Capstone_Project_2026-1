import cv2
import os
import glob

def resize_images(target_width, target_height):
    # Support multiple extensions
    extensions = ['*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG']
    image_files = []
    for ext in extensions:
        image_files.extend(glob.glob(f'./**/{ext}', recursive=True))

    print(f"Found {len(image_files)} images to resize.")

    for img_path in image_files:
        try:
            # Skip the script itself if it matches
            if os.path.basename(img_path) == 'resize_images.py':
                continue

            img = cv2.imread(img_path)
            if img is None:
                print(f"Failed to read: {img_path}")
                continue

            # Resize using area interpolation (good for downsampling)
            resized_img = cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_AREA)
            
            # Save the resized image (overwriting the original)
            cv2.imwrite(img_path, resized_img)
            # print(f"Resized: {img_path}")
        except Exception as e:
            print(f"Error processing {img_path}: {e}")

if __name__ == "__main__":
    resize_images(1024, 656)
    print("Resizing complete.")
