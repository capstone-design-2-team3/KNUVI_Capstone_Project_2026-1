# 3DOD RAIN & NIGHT Part — Kyungjin

## 개요
nuScenes 야간 데이터셋에서 LLIE(Low-Light Image Enhancement) 전처리가
3D Object Detection 성능에 미치는 영향 분석

## 실험 구성
- **데이터**: nuScenes val night (602 scenes)
- **LLIE 방법**: CLAHE, EnlightenGAN, ZeroDCE++
- **3DOD 모델**: MoME, DeepInteraction, BEVFusion

## 폴더 구조
```
3DOD_RAIN&NIGHT_Part/
├── README.md
├── 1_Models/                                       # 외부 모델 세팅 가이드
│   ├── LLIE_models.md                                  # EnlightenGAN, Zero-DCE++
│   └── 3DOD_models.md                                  # MoME, DeepInteraction, BEVFusion
├── 2_Experiments/                                  # 실험별 자료 + 공통 분석 스크립트
│   ├── scripts/                                        # 공통 분석 코드
│   │   ├── data_prep/                                  # LLIE pkl 생성 (data_prep_utils 공유)
│   │   ├── metrics/                                    # 수치 분석 (feature_utils 공유)
│   │   └── visualization/                              # 시각화 (make_grid, visualize_bbox_llie)
│   ├── 1_baseline_MoME_night/                          # MoME 야간 베이스라인 재현
│   │                                                   #   (원본 nuScenes, 야간 필터링 데이터 사용)
│   ├── 2_finetune_MoME_LLIE/                           # LLIE 전처리 + 파인튜닝 통한
│   │                                                   #   MoME 성능 개선 시도
│   ├── 3_multi_model_LLIE_eval/                        # LLIE 전처리 × 3 모델
│   │                                                   #   (MoME/DI/BEVFusion) 성능 개선 여부 확인
│   ├── 4_LLIE_evaluation_goodbad_cases/                # LLIE 정량+정성 평가 후
│   │                                                   #   good/bad 케이스 분류 + 케이스별 성능 비교 분석
│   └── 5_performance_based_HardEasy_quality/           # AP 성능 기반 Hard/Easy 그룹 분류
│                                                       #   + 이미지·LiDAR 품질 비교 분석
└── 3_Paper/                                        # 논문 작성 자료
    ├── Figures/                                        # 논문 제출 figure
    └── research/                                       # 조사 자료
```