# Weather-Robust 3DOD Toolkit

## 1. 개요

본 소프트웨어는 KITTI 형식의 LiDAR 데이터를 입력으로 사용하여  
snow 환경에서의 3D point cloud 복원 및 분석을 수행하는 파이프라인입니다.

구성은 다음과 같습니다:
train → inference → analyzer → pipeline


---

## 2. 주요 기능

- Sparse LiDAR point cloud 복원 모델 학습
- Snow 환경 point cloud densification (추론)
- 복원된 point cloud 통계 분석
- 전체 파이프라인 자동 실행 지원

---

## 3. 프로젝트 구조
Weather-Robust-3DOD-Toolkit/

├── train.py
├── inference.py
├── analyzer.py
├── pipeline.py
├── requirements.txt
│
├── training/
│   ├── velodyne/
│   ├── snow_velodyne/
│   ├── label_2/
│   └── calib/
│
├── checkpoints/
│   └── best_model.pth   (학습 후 생성)
│
├── infer_velodyne/
│   └── *.bin            (추론 결과 생성)
│
└── results/
    └── analysis.csv     (분석 결과 생성)


---

## 4. 데이터셋 구조 (필수)

본 코드는 KITTI format 데이터를 사용합니다.

`training/` 폴더 아래 다음 구조로 데이터가 존재해야 합니다:
training/

├── velodyne/        # 원본 LiDAR point cloud (.bin)
├── snow_velodyne/   # snow 환경 LiDAR input (.bin)
├── label_2/         # 3D bounding box annotation
└── calib/           # camera-LiDAR calibration


각 point cloud 파일 형식: x, y, z, intensity (float32)


---

## 5. 환경 요구사항

### Python
- Python >= 3.9

### 주요 라이브러리
```bash
pip install -r requirements.txt
```
requirements:

torch
spconv
numpy
pandas
open3d
tqdm


---

## 6. 실행 방법

### 1) 모델 학습

```bash
python train.py
```

출력: checkpoints/best_model.pth

### 2) Point Cloud 추론

```bash
python inference.py
```

입력:

training/snow_velodyne/

출력:

infer_velodyne/*.bin

### 3) 데이터 분석

```bash
python analyzer.py
```

입력:

infer_velodyne/*.bin

출력:

results/analysis.csv

### 4) 전체 파이프라인 실행

```bash
python pipeline.py
```

(학습 → 추론 → 분석 자동 실행)

---

## 7. 실행 흐름

KITTI Dataset
    ↓
train.py
    ↓
best_model.pth
    ↓
inference.py
    ↓
dense point cloud (.bin)
    ↓
analyzer.py
    ↓
analysis.csv

---

## 8. 출력 결과

(1) 학습 결과
checkpoints/best_model.pth
(2) 추론 결과
infer_velodyne/*.bin
(3) 분석 결과
results/analysis.csv

---

## 9. 주의사항

데이터셋 경로는 training/ 기준으로 고정되어 있음
KITTI 데이터는 별도로 다운로드하여 배치해야 함
CUDA 환경에서 실행을 권장함
spconv는 CUDA 버전에 맞는 설치 필요
