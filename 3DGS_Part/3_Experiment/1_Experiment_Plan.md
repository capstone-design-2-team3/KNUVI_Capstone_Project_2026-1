> 강설 환경 내 Posed 와 Unposed 3DGS 의 기상 강건성 및 2D 전처리 적용 효과 비교 연구
> 핵심 질문: 눈(Snow) 아티팩트와 2D 전처리(De-snowing)가 포즈 추정 기반(Posed)과 포즈-형상 결합 최적화(Unposed) 파이프라인에 각각 어떤 영향을 미치는가?

# 1. Variable and Data
### 대상 데이터셋: Free Dataset (Real-world / 비정형 궤적)
- F2-NeRF에서 제공하는 7개 씬 중 실내 장면인 **Lab을 제외한 6개 씬** 사용 (Grass, Hydrant, Pillar, Road, Sky, Stair)
- **전처리 (Downsampling):** 모든 원본 및 합성 영상은 **1024 * 656** 해상도로 다운샘플링하여 사용

### 입력 데이터 조건 (3가지)
1. **Clean (Raw):** 날씨 노이즈가 없는 맑은 상태. (Upper Bound 기준)
2. **Snow (Weathered):** WeatherEdit을 사용하여 각 씬에 눈 아티팩트 합성.
3. **De-snow (Preprocessed):** **MWFormer**를 사용하여 Snow 영상에서 눈 아티팩트를 제거한 상태. (2D 전처리 효과 확인)

# 2. Experiment Case
### Case A. Posed 3DGS (COLMAP + Vanilla 3DGS)
순차적 파이프라인(SfM -> 3DGS)에서 날씨 노이즈가 특징점 매칭 및 포즈 추정 안정성에 미치는 영향을 분석합니다.
- **A1 (Clean + Posed):** 기준 성능 측정
- **A2 (Snow + Posed):** 눈 입자로 인한 COLMAP의 포즈 추정 실패 및 궤적 붕괴 관찰
- **A3 (De-snow + Posed):** 전처리를 통한 포즈 추정 기능 회복 여부 및 시점 불일치 영향 분석

### Case B. Unposed 3DGS (LongSplat)
포즈와 형상을 동시에 최적화하는 모델이 눈 입자와 전처리 오차를 기하학적으로 어떻게 수용하는지 분석합니다.
- **B1 (Clean + Unposed):** 기준 성능 측정
- **B2 (Snow + Unposed):** 눈 입자가 가우시안으로 복원되며 발생하는 렌더링 품질 저하 분석
- **B3 (De-snow + Unposed):** 전처리된 이미지의 시점 불일치를 결합 최적화 과정에서 보정하는 능력 관찰

# 3. Evaluation Metrics
### Metrics (평가지표)
1. **Rendering Quality (시각적 품질):**
   - **PSNR:** 픽셀 단위 오차 측정
   - **SSIM:** 구조적 유사도 측정
   - **LPIPS:** 인지적 유사도 측정 (2D 전처리의 아티팩트 감지에 중점)
2. **Pose Accuracy (포즈 정확도):**
   - **ATE (Absolute Trajectory Error):** 전체 궤적 일치도
   - **RTE (Relative Translation Error):** 상대적 이동 오차
   - **RPE (Relative Pose Error):** 상대적 회전/포즈 오차

* 모든 지표의 GT는 각 Case의 Clean Output을 기준으로 측정함
