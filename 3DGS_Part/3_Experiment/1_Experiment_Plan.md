> 주제: 강설 환경 내 Posed와 Unposed 3DGS의 기상 강건성 및 2D 전처리 적용 효과 비교 연구
> 핵심 질문: 눈(Snow) 아티팩트와 2D 전처리(De-snowing)가 포즈 추정 기반(Posed)과 포즈-형상 결합 최적화(Unposed) 파이프라인에 각각 어떤 영향을 미치는가?

# 1. Variable and Data
### 대상 데이터셋: Free Dataset (Real-world / 비정형 궤적)
- F2-NeRF에서 제공하는 7개 씬 중 실내 장면인 **Lab을 제외한 6개 씬** 사용 (Grass, Hydrant, Pillar, Road, Sky, Stair)
- **전처리 (Downsampling):** 모든 원본 및 합성 영상은 **1024 * 656** 해상도로 다운샘플링하여 사용

### 입력 데이터 조건 (3가지)
1. **Original (Raw):** 날씨 노이즈가 없는 맑은 상태. (Upper Bound 기준)
2. **Snow (Weathered):** WeatherEdit을 사용하여 각 씬에 눈 아티팩트 합성.
   - **1차 실험:** Heavy Snow (강한 눈)
   - **2차 실험:** Light Snow (약한 눈)
3. **De-snow (Preprocessed):** **MWFormer**를 사용하여 Snow 영상에서 눈 아티팩트를 제거한 상태. (2D 전처리 효과 확인)

# 2. Experiment Case
### Case A. Posed 3DGS (COLMAP + Vanilla 3DGS)
순차적 파이프라인(SfM -> 3DGS)에서 날씨 노이즈가 특징점 매칭 및 포즈 추정 안정성에 미치는 영향을 분석합니다.
- **A1 (Original + Posed):** 기준 성능 측정
- **A2 (Snow + Posed):** 눈 입자로 인한 COLMAP의 포즈 추정 실패 및 궤적 붕괴 관찰
- **A3 (De-snow + Posed):** 전처리를 통한 포즈 추정 기능 회복 여부 및 시점 불일치 영향 분석

### Case B. Unposed 3DGS (LongSplat)
포즈와 형상을 동시에 최적화하는 모델이 눈 입자와 전처리 오차를 기하학적으로 어떻게 수용하는지 분석합니다.
- **B1 (Original + Unposed):** 기준 성능 측정
- **B2 (Snow + Unposed):** 눈 입자가 가우시안으로 복원되며 발생하는 렌더링 품질 저하 분석
- **B3 (De-snow + Unposed):** 전처리된 이미지의 시점 불일치를 결합 최적화 과정에서 보정하는 능력 관찰

# 3. Result Analysis
### 후처리 (Post-processing)
- 정량적 평가를 위해 모든 **Rendering Output**과 **Original Image**를 **1000 * 640** 해상도로 **Centered Crop** 하여 비교 진행

### Metrics (평가지표)
1. **Rendering Quality (시각적 품질):**
   - **PSNR:** 픽셀 단위 오차 측정
   - **SSIM:** 구조적 유사도 측정
   - **LPIPS:** 인지적 유사도 측정 (2D 전처리의 아티팩트 감지에 중점)
2. **Pose Accuracy (포즈 정확도):**
   - **ATE (Absolute Trajectory Error):** 전체 궤적 일치도
   - **RTE (Relative Translation Error):** 상대적 이동 오차
   - **RPE (Relative Pose Error):** 상대적 회전/포즈 오차

### 분석 중점 사항
1. **날씨 민감도 대조 (A2 vs B2):** 특징점 기반 붕괴와 가우시안 형상 오염의 차이 분석
2. **전처리 결합 효과 (A3, B3):** MWFormer 도입이 각 파이프라인의 성능을 Original 수준으로 얼마나 회복시키는지 분석
3. **시점 불일치 대응력 (A3 vs B3):** 2D 복원 오차(Inconsistency)를 고정된 포즈(Posed)와 가변 포즈(Unposed)가 처리하는 메커니즘 차이 규명

# 4. 결론 (Conclusion)
실험 결과, 기상 강건성과 2D 전처리 적용 후의 렌더링 품질 회복 효과 모두 일반 3DGS에서 더 안정적으로 나타남을 확인하였습니다. 반면 Unposed 모델은 2D 전처리로 인해 포즈와 형상 최적화가 오히려 방해받을 수 있다는 결론을 도출하였습니다.
