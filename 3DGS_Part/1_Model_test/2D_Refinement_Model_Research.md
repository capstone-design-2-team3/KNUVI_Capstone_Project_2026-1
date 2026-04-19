# Model Search

- Weather Artifact를 제거할 수 있는 2D Refinement 모델 찾기
- Google Scholar Quary : multiple adverse weather conditions  "image restoration"
- 아래 세 모델 모두 Pretrained weight 제공

### 1. Histoformer
- Restoring Images in Adverse Weather Conditions via Histogram Transformer
- Sun et al., ECCV 2024
- Code : https://github.com/sunshangquan/Histoformer
- Paper : https://arxiv.org/abs/2407.10172

### 2. UtilityIR
- Always Clear Days: Degradation Type and Severity Aware All-In-One Adverse Weather Removal
- Chen et al., IEEE Access 2025
- Code : https://github.com/fordevoted/UtilityIR
- Paper : https://arxiv.org/abs/2310.18293

### 3. MWFormer
- MWFormer: Multi-Weather Image Restoration Using Degradation-Aware Transformers
- Zhu et al., TIP 2025
- Code : https://github.com/taco-group/MWFormer
- Paper : https://arxiv.org/abs/2411.17226


# Analysis & Comparison w/GPT-5.4

## 공통점

- 단일 unified 모델로 다중 날씨 열화(rain, haze, snow 등)를 동시에 처리하는 **All-in-One / Multi-Weather** 패러다임
- **Transformer 기반** 아키텍처
- 날씨별 degradation 특성을 구분하거나 인식하는 메커니즘 내장
- Haze, Rain, Snow 등 주요 weather artifact 제거 가능

## 핵심 차이점

### Histoformer
- **핵심 아이디어**: 픽셀 강도(intensity) 기반 히스토그램 정렬
- Dynamic-range Histogram Self-Attention (DHSA): 비슷한 밝기/열화 수준의 픽셀끼리 bins로 묶어 attention 수행
- 공간적으로 멀리 떨어진 유사 열화 픽셀들을 효율적으로 처리
- Pearson 상관계수를 Loss로 사용해 복원 픽셀의 순서를 GT와 일치
- Degradation 인식: **암묵적** (픽셀 강도 유사성)

### UtilityIR
- **핵심 아이디어**: Degradation Type + Severity(심각도)를 동시에 인식
- 같은 rain이라도 약한 비/강한 비처럼 severity 차이가 intra-domain 다양성을 유발한다는 점을 명시적으로 모델링
- Marginal Quality Ranking Loss (MQRL) + Contrastive Loss (CL)로 severity/type 표현 학습
- Multi-Head Cross Attention (MHCA) + Local-Global AdaIN (LG-AdaIN)으로 복원
- 학습 중 보지 못한 combined multiple degradation 이미지에도 복원 가능
- **Restoration level 조절(modulate) 가능**

### MWFormer
- **핵심 아이디어**: Hyper-network + Feature-wise Linear Modulation (FiLM) 기반으로 복원 네트워크 파라미터를 동적으로 변조
- 보조 네트워크(auxiliary hyper-network)가 content-independent, distortion-aware embedding 추출
- 해당 임베딩이 메인 Transformer의 파라미터를 조절
- Contrastive learning으로 weather-type 표현 학습
- **Retraining 없이 single-weather / hybrid-weather 복원 모드 전환 가능**

## 모델 비교표

| 항목 | Histoformer | UtilityIR | MWFormer |
|---|---|---|---|
| 핵심 메커니즘 | Histogram Self-Attention | MQRL + Contrastive Loss | Hyper-network + FiLM |
| Degradation 인식 | 암묵적 | 명시적 (type + severity) | 명시적 (contrastive → hyper-net) |
| Severity 인식 | ❌ | ✅ | 간접적 |
| Hybrid weather 처리 | 제한적 | ✅ | ✅ |
| 복원 레벨 제어 | ❌ | ✅ | ✅ |
| 발표 venue | ECCV 2024 | IEEE Access 2025 | TIP 2025 |

## 적용 추천 순위

### 요구사항
- Multi-view 간 시각적 일관성(consistency) 유지
- 뷰마다 날씨 심각도가 다를 수 있음
- Unposed 3DGS 입력 전 전처리 → feature matching에 유리한 clean image 복원
- 복원 품질 우선 (실시간성 불필요)

### 순위

**1순위: MWFormer ✅**
- Hyper-network가 각 뷰의 degradation embedding을 독립적으로 추출 → 뷰마다 다른 날씨 조건에 적응적 처리
- Retraining 없이 single/hybrid weather 모드 전환 → 다양한 입력에 범용적
- Contrastive learning 기반 embedding이 구조적 feature(edge, texture) 보존 → SfM/feature matching에 유리
- TIP급 검증으로 복원 품질 우수

**2순위: UtilityIR**
- Severity-aware라는 점이 multi-view에서 강점
- 단, 복원 레벨 조절 기능이 multi-view consistency를 해칠 수 있음
- IEEE Access로 venue가 상대적으로 낮음

**3순위: Histoformer**
- 단일 이미지 품질 복원에는 강하나, 뷰 간 강도 분포 차이로 multi-view consistency 무너질 위험
- Severity/type 명시적 모델링 없어 3DGS 파이프라인 통합 시 예측 가능성 낮음

### 결론
> **MWFormer**를 메인 2D Refinement 모델로 채택하고,  
> **UtilityIR**을 ablation 비교 대상으로 함께 실험하여 논문 기여도를 높이는 전략 권장


+추가로, AllWeatherNet도 있긴 함. 
**AllWeather-Net (ICPR 2025)**
- Qian et al., https://github.com/Jumponthemoon/AllWeatherNet
- snow, rain, fog, nighttime을 통합적으로 처리하는 image enhancement 모델
- SIAM (Scaled Illumination-aware Attention) + 3-level hierarchical discrimination
- 기상 파티클 제거에 그치지 않고 color/texture 전반을 보정하는 enhancement 방식
- **→ MWFormer 대비 추가 ablation 후보로 고려 가능**
- 평가 데이터: ACDC, Dark Zurich, Foggy Zurich, Nighttime Driving
