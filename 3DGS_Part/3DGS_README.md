# 3DGS 실외 악천후 환경 복원 및 포즈 추정 강건성 연구 (Capstone 2026-1)

본 디렉토리는 **"비정형 긴 궤적(Casual Long Videos) 환경에서 2D 전처리(MWFormer)와 Unposed 3DGS(LongSplat)의 결합이 악천후 하의 포즈 추정 및 3D 복원에 미치는 영향"**을 분석하는 연구 공간입니다.

## 📌 연구 핵심 가설 (Hypothesis)
1. **Posed 3DGS(COLMAP)**는 악천후 노이즈로 인한 특징점 매칭 실패로 카메라 포즈 추정이 붕괴될 것이다.
2. **2D 전처리(MWFormer)**는 이미지를 정화하여 포즈 추정 기능을 회복시키지만, 시점 간 불일치(Multi-view Inconsistency)라는 새로운 오차를 유발할 수 있다.
3. **Unposed 3DGS(LongSplat)**의 포즈-형상 결합 최적화(Joint Optimization)는 이러한 전처리 오차를 스스로 보정하여 가장 높은 복원 성능을 보일 것이다.

---

## 📂 실험 설계 (Experiment Design)

### 1. 입력 데이터 변수 (Data Variables)
- **Raw (원본)**: 날씨 노이즈가 없는 맑은 영상 (성능 상한선: Upper Bound 확인용)
- **Weathered (악천후)**: WeatherEdit으로 합성된 비, 눈 아티팩트가 포함된 영상 (붕괴 기준선: Baseline 확인용)
- **Un-weathered (전처리)**: **MWFormer**를 통해 악천후 요소를 제거한 영상 (전처리 효과 및 오차 확인용)
*대상 데이터셋: **Free Dataset** (F2-NeRF 제공 7개 씬 기반 비정형 궤적 데이터)*

### 2. 파이프라인 대조군 (Comparison Cases)

#### Case A. Posed 3DGS (COLMAP + 일반 3DGS)
전통적인 SfM 기반의 순차적 파이프라인이 날씨 노이즈와 전처리 오차에 어떻게 반응하는지 확인합니다.
- **A1 (Raw + Posed)**: 최적 환경 기준 성능 측정
- **A2 (Weathered + Posed)**: 특징점 매칭 실패 및 카메라 궤적 붕괴(Tracking Loss) 지점 관찰
- **A3 (Un-weathered + Posed)**: 전처리 후 이미지 정화가 포즈 정확도 회복에 미치는 영향 분석

#### Case B. Unposed 3DGS (LongSplat)
포즈와 형상을 동시에 최적화하는 결합 방식의 대응력을 확인합니다.
- **B1 (Raw + Unposed)**: Unposed 방식의 기준 성능 측정
- **B2 (Weathered + Unposed)**: 날씨 입자가 가우시안 형상으로 직접 복원되며 발생하는 렌더링 품질 저하 분석
- **B3 (Un-weathered + Unposed)**: **결합 최적화 과정이 전처리의 한계(시점 불일치)를 보정해 내는 능력(핵심 지표)** 관찰

---

## 🛠 핵심 모델 및 분석 도구

### 2D 복원: MWFormer (TIP 2025)
- **메커니즘**: 하이퍼 네트워크(Hyper-network)와 FiLM을 사용하여 날씨 열화 상태에 따라 파라미터를 동적으로 변조.
- **장점**: 단일 및 복합 날씨(비+눈 등)에 대해 재학습 없이 유연한 복원 가능.

### 평가지표 (Metrics)
- **시각적 품질**: `PSNR`, `SSIM`, `LPIPS` (인지적 유사도 측정에 중점)
- **포즈 정확도**: `ATE` (절대 궤적 오차), `RTE/RPE` (상대 이동/포즈 오차)

---

## 📈 분석 전략 (Analysis Strategy)
1. **A2 vs. B2 (날씨 민감도 대조)**: 특징점 기반(SfM) 붕괴와 형상 기반(Optimization) 품질 저하의 양상 비교.
2. **A2 vs. A3, B2 vs. B3 (전처리 도입 효과)**: 2D 전처리가 각 모델의 성능 상한선(Raw)에 얼마나 가깝게 회복시키는지 분석.
3. **A3 vs. B3 (시점 불일치 대응력)**: 2D 전처리 오차가 고정 포즈(Posed) 모델과 가변 포즈(Unposed) 모델의 기하학적 일관성에 미치는 영향 대조.

---

## 📂 디렉토리 가이드
- `1_Model_test/`: LongSplat 설정 및 모델별 사전 테스트 로그
- `3_Experiment/`: 상세 실험 계획(`1_Experiment_Plan.md`) 및 결과 수치(`2_Experiment_Log.md`)
- `4_Paper_Writing/`: 논문 초안 및 핵심 Figure (방미공 '26 투고용)