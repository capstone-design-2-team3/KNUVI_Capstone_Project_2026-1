# LLIE 모델 세팅 가이드

저조도 이미지 개선(LLIE) 모델을 nuScenes 야간 데이터에 적용하기 위한 환경 설정과
실행 명령 정리.

CLAHE 는 OpenCV로 직접 적용하므로 별도 모델 세팅 불필요 — [data_prep/run_clahe_night.py](../2_Experiments/scripts/data_prep/run_clahe_night.py) 참고.

---

## EnlightenGAN

- **저장소**: <!-- TODO: github URL -->
- **논문**: <!-- TODO: citation -->

### 환경
<!-- TODO: Python, CUDA, conda env spec -->

### 설치
```bash
# TODO
```

### Inference
```bash
# TODO: nuScenes 야간 이미지에 대한 inference 명령
# 입력 폴더 / 출력 폴더
```

### 출력 위치
<!-- TODO: 실제 변환된 이미지가 저장되는 경로 -->
- 예: `/home/.../dataset/LLIE_images_EnlightenGAN/`
- pkl 생성: [data_prep/create_egan_pkl.py](../2_Experiments/scripts/data_prep/create_egan_pkl.py)

### 변경사항 / 주의사항
<!-- TODO: 원 저장소 대비 변경한 config, 의존성 충돌 해결 등 -->

---

## Zero-DCE++

- **저장소**: <!-- TODO: github URL -->
- **논문**: <!-- TODO: citation -->

### 환경
<!-- TODO: Python, CUDA, conda env spec -->

### 설치
```bash
# TODO
```

### Inference
```bash
# TODO: nuScenes 야간 이미지에 대한 inference 명령
```

### 출력 위치
<!-- TODO -->
- 예: `/home/.../dataset/LLIE_images_ZeroDCE/`
- pkl 생성: [data_prep/create_zerodce_pkl.py](../2_Experiments/scripts/data_prep/create_zerodce_pkl.py)

### 변경사항 / 주의사항
<!-- TODO -->