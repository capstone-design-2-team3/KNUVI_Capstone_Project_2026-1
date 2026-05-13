# 멀티모달 3D Object Detection 모델 세팅 가이드

3개 모델(MoME / DeepInteraction / BEVFusion)을 nuScenes 야간 데이터에 대해
4개 조건(Original / CLAHE / EnlightenGAN / Zero-DCE)으로 inference 한 결과(pkl)를
[2_Analysis](../2_Experiments/) 의 분석 스크립트가 입력으로 사용함.

각 모델별 환경, 설치, inference 명령, 결과 pkl 저장 위치 정리.

---

## MoME

- **저장소**: <!-- TODO: github URL -->
- **논문**: <!-- TODO: citation -->

### 환경
<!-- TODO: Python, CUDA, mmdet3d 버전, conda env spec -->

### 설치
```bash
# TODO
```

### 데이터 준비
- 야간 GT pkl: `nuscenes_infos_val_night.pkl`
- LLIE 조건별 pkl: `create_*_pkl.py` 로 생성 (cam_info['data_path']가 변환 이미지를 가리킴)

### Inference (4 조건)
```bash
# TODO: Original
# TODO: CLAHE
# TODO: EnlightenGAN
# TODO: Zero-DCE
```

### 결과 pkl 위치
- Original:     `/.../MoME/results/night_results.pkl`
- CLAHE:        `/.../MoME/results/night_clahe_results.pkl`
- EnlightenGAN: `/.../MoME/results/night_enlighten_results.pkl`
- Zero-DCE:     `/.../MoME/results/night_zerodce_results.pkl`

### 변경사항 / 주의사항
<!-- TODO: config 변경, 좌표계 관련 (BEVFusion 과 z_correction 차이 등) -->

---

## DeepInteraction

- **저장소**: <!-- TODO -->
- **논문**: <!-- TODO -->

### 환경
<!-- TODO -->

### 설치
```bash
# TODO
```

### Inference (4 조건)
```bash
# TODO
```

### 결과 pkl 위치
- `/.../DeepInteraction/results/night_results.pkl`
- `/.../DeepInteraction/results/night_clahe_results.pkl`
- `/.../DeepInteraction/results/night_egan_results.pkl`
- `/.../DeepInteraction/results/night_zerodce_results.pkl`

### 변경사항 / 주의사항
<!-- TODO -->

---

## BEVFusion

- **저장소**: <!-- TODO -->
- **논문**: <!-- TODO -->

### 환경
<!-- TODO -->

### 설치
```bash
# TODO
```

### Inference (4 조건)
```bash
# TODO
```

### 결과 pkl 위치
- `/.../BEVFusion/results/night_results.pkl`
- `/.../BEVFusion/results/night_clahe_results.pkl`
- `/.../BEVFusion/results/night_egan_results.pkl`
- `/.../BEVFusion/results/night_zerodce_results.pkl`

### 변경사항 / 주의사항
<!-- TODO: bbox z-좌표가 3D center 직접 저장 (MoME / DI 는 bottom-center → +h/2 보정 필요).
     visualize_bbox_llie.py 의 z_correction 분기 참고. -->