import cv2
import numpy as np
import os
from ultralytics import YOLO

def extract_and_save_masks(image_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 모델 로드: 속도와 성능의 밸런스가 좋은 Small 모델 사용
    # (추후 성능을 높이려면 'yolov8x-seg.pt'로 변경만 하시면 됩니다)
    model = YOLO('yolov8x-seg.pt') 
    
    # 2. 관심 객체 필터링 (COCO 데이터셋 기준)
    # 0: person, 1: bicycle, 2: car, 3: motorcycle, 5: bus, 7: truck
    target_classes = [0, 1, 2]

    valid_extensions = ('.png', '.jpg', '.jpeg')
    
    for img_name in sorted(os.listdir(image_dir)):
        if not img_name.lower().endswith(valid_extensions):
            continue

        img_path = os.path.join(image_dir, img_name)
        img = cv2.imread(img_path)
        h, w = img.shape[:2]

        # 3. 추론 실행 (conf=0.3 이상만 탐지)
        results = model(img, classes=target_classes, conf=0.3, verbose=False)
        result = results[0]

        # 4. 투영 매핑을 위한 빈 2D 마스크 캔버스 생성 (H, W)
        # 0 = 배경, 1 이상 = 개별 객체의 Instance ID
        instance_mask = np.zeros((h, w), dtype=np.uint8)

        if result.masks is not None:
            # 추출된 다각형(Polygon) 좌표와 Bounding Box 정보 매칭
            boxes = result.boxes.data.cpu().numpy()
            polygons = result.masks.xy

            for i, (poly, box) in enumerate(zip(polygons, boxes)):
                instance_id = i + 1
                
                # 다각형 좌표를 이미지 픽셀 정수형으로 변환 후 마스크 캔버스에 채우기
                poly_pts = np.array(poly, dtype=np.int32)
                cv2.fillPoly(instance_mask, [poly_pts], instance_id)

        # 5. 추출된 마스크를 Numpy 압축 파일(.npz)로 저장
        # 용량을 줄이면서도 파이썬에서 불러오는 속도가 매우 빠릅니다.
        out_name = os.path.splitext(img_name)[0] + '.npz'
        out_path = os.path.join(output_dir, out_name)
        np.savez_compressed(out_path, mask=instance_mask)

        print(f"[{img_name}] 마스크 추출 완료 -> {out_path}")

if __name__ == "__main__":
    # 실제 Snow-KITTI 데이터셋의 경로로 수정하여 실행하세요.
    INPUT_IMAGE_DIR = './training/image_2'
    OUTPUT_MASK_DIR = './training/instance_masks'
    
    print("마스크 추출 작업을 시작합니다...")
    extract_and_save_masks(INPUT_IMAGE_DIR, OUTPUT_MASK_DIR)
    print("모든 작업이 완료되었습니다.")