# 강설 환경 내 Posed와 Unposed 3DGS의 기상 강건성 및 2D 전처리 적용 효과 비교 연구 (Capstone 2026-1)

본 프로젝트는 **눈(Snow) 아티팩트가 3DGS의 두 가지 패러다임(Posed vs. Unposed)에 미치는 영향**과, **2D 전처리(MWFormer)를 통한 품질 개선 효과**를 심층 분석합니다. (2026 한국방송·미디어공학회 하계학술대회 제출 논문 파트)

---

## 📌 주요 연구 결과 (Conclusion)
초기 가설(Unposed 3DGS가 더 강건할 것)과 달리, 실험을 통해 다음과 같은 결론을 도출하였습니다.
1. **기상 요소 자체에 대한 강건성**: 강설 아티팩트 환경에서 3D 장면 재구성의 안정성은 Unposed 모델보다 일반 3DGS에서 더 높게 나타났습니다.
2. **2D 전처리 도입 효과**: MWFormer 등 2D 전처리 적용 후의 렌더링 품질 회복 효과 역시 일반 3DGS 파이프라인에서 더 뛰어난 회복력을 보였습니다.
3. **Unposed 모델의 한계점**: Unposed 모델의 경우, 2D 전처리로 인해 유발된 프레임 간 시점 불일치가 궤적 추정 및 형상 최적화를 오히려 방해하는 현상이 관찰되었습니다.

---

## 📂 실험 설계 (Experiment Design)

### 1. 대상 데이터셋 및 전처리 (Data Preparation)
- **Dataset:** Free Dataset 중 실내(Lab)를 제외한 **6개 실외 씬** (Grass, Hydrant, Pillar, Road, Sky, Stair)
- **Weather Synthesis:** WeatherEdit을 이용한 **Heavy Snow** 및 **Light Snow** 합성
- **Downsampling:** 입력 데이터는 모두 **1024 * 656** 해상도로 통일
- **Post-processing:** 최종 렌더링 결과물은 **1000 * 640** 해상도로 **Centered Crop** 하여 평가

### 2. 파이프라인 대조군 (Comparison Cases)

| 구분 | Case A. Posed 3DGS (COLMAP + 3DGS) | Case B. Unposed 3DGS (LongSplat) |
| :--- | :--- | :--- |
| **Original** | A1: 맑은 날씨 기준 성능 (Upper Bound) | B1: 맑은 날씨 기준 성능 (Upper Bound) |
| **Snow** | A2: 눈 아티팩트로 인한 궤적 붕괴 측정 | B2: 눈 입자가 가우시안으로 복원되는 양상 분석 |
| **De-snow** | A3: 전처리를 통한 포즈 추정 회복력 분석 | B3: 결합 최적화의 시점 불일치 보정 능력 분석 |

---

## 🛠 핵심 모델 및 분석 도구

### 2D 복원: MWFormer (TIP 2025)
- 하이퍼 네트워크와 FiLM을 활용한 동적 파라미터 변조 기반 눈 제거(Snow Removal).

### 평가지표 (Metrics)
- **Rendering Quality:** `PSNR`, `SSIM`, `LPIPS`
- **Pose Accuracy:** `ATE` (절대 궤적 오차), `RTE/RPE` (상대 이동/포즈 오차)

---

## 📈 분석 전략 (Analysis Strategy)
1. **A2 vs. B2 (날씨 민감도)**: 특징점 기반 SfM 붕괴 vs. 기하학적 형상 오염의 시각적/정량적 차이 대조.
2. **A2 vs. A3, B2 vs. B3 (전처리 도입 효과)**: 2D 전처리가 성능 상한선(Original)에 얼마나 근접하게 만드는지 분석.
3. **A3 vs. B3 (시점 불일치 대응력)**: 전처리 오차를 고정된 포즈(A3)와 가변 포즈(B3)가 수용하는 안정성 비교.

---

## 📂 디렉토리 가이드
- `1_Model_test/`: LongSplat 및 WeatherGS 테스트 로그
- `3_Experiment/`: 상세 실험 계획(`1_Experiment_Plan.md`) 및 결과 수치(`2_Experiment_Log.md`)
- `4_Paper_Writing/`: 논문 초안 및 핵심 Figure
