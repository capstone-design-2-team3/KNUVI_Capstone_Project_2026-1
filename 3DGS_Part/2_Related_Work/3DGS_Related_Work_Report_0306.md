# Related Work 조사

- *개념 정의*

    **keyframe**: 영상(연속 프레임) 중에서 정보가 충분히 달라지는 시점 - 대표 프레임

    **정성 비교**: 결과를 눈으로 보고 품질을 판단 (↔ 정량 비교)

    **PSNR(Peak Signal-to-Noise Ratio)**: ↑
    정답과 복원 결과 사이의 오차가 작을수록 값이 커짐.

    **SSIM(Structural Similarity Index Measure)**: ↑
    두 이미지가 구조(윤곽/패턴), 밝기, 대비 측면에서 비슷한 정도(0~1)

    **LPIPS(Learned Perceptual Image Patch Similarity**): ↓
    정성 비교의 SSIM - 사람 대신 해주는 모델(신경망)을 사용하여 특징(feature) 공간에서의 거리를 계산

    **ASM(Atmospheric Scattering Model)**:
    대기 산란 영상 모델, 안개 생성을 물리적으로 근사한 모델

    **NeRF(Neural Radiance Fields)**: 2D사진을 3D로 만드는 기술
    0. MLP 학습: 특정 좌표와 바라보는 각도를 입력 → 그 지점을 가상의 빛을 쏘아 해당 경로 위의 점들을 MLP에 입력 → 정답과 유사하도록 학습
    1. 확실한 정보: 여러 2D사진의과 각 사진을 찍은 카메라의 위치/각도를 입력하여 같은물체를 향해 쏜 직선들의 교차 지점을 신경망에 저장
    2. 정보가 없는 곳: 신경망이 학습한 공간 데이터를 바탕으로 카메라와 정보가 없는 곳 사이에 직선을 그어 직선 상의 점을 색상×신경망의 가중치를 합쳐 예측

    **멀티스케일 구조(Multi-scale architecture)**: 한 번에 한 해상도(스케일)로만 처리하지 않고, 여러 해상도(작게/중간/크게) 로 특징을 뽑아 결합하는 설계.(대표 구현 중 하나: U-Net)
    낮은 해상도(다운샘플): 전체적인 안개 분포, 전역 대비/색감 같은 큰 흐름(글로벌 컨텍스트) 을 잘 봄
    원/높은 해상도(업샘플·스킵 연결): 물체 경계, 텍스처 같은 세부 디테일 을 잘 살림

    **K-value (*AOD-Net* 계열의 K 맵/파라미터)**: “이 픽셀은 안개의 영향이 얼마나 섞였는가?”를 픽셀별로 조절하는 게이트/계수 같은 역할
    AOD-Net(및 변형들)은 Atmospheric Scattering Model(ASM)을 그대로 풀기보다, 여러 물리 항(전달률 t(x), 대기광 A 등)을 하나로 묶어 “K(x)”라는 이미지(맵) 형태의 값으로 학습.

    **AOD-Net**: 단일 이미지 디헤이징을 위한 딥러닝 모델
    대기 산란 모델(ASM)로 디헤이징을 하되(역연산), 그 모델의 여러 항(전달률 t(x), 대기광 A 등)을 따로 추정하지 않고 한 번에 묶어서 K(x) 라는 “픽셀별 맵”을 신경망이 직접 예측하게 만든 네트워크.

    **UDTIRI(Urban Digital Twins for Intelligent Road Inspection)**: 도로(road) 환경에서의 “지능형 도로 점검(Intelligent Road Inspection)”을 위한 공개 벤치마크/데이터셋

---

- WeatherGS
  - 논문명: WeatherGS: 3D Scene Reconstruction in Adverse Weather Conditions via Gaussian Splatting
  - 학회/저널: ICRA 2025
  - 주요 목적: 악천후(눈/비)에서 3DGS가 날씨 아티팩트를 같이 복원해버리는 문제를 해결해, 3D 장면 복원
  - 실제/합성 데이터 기상 조건:

        합성: Blender로 생성한 3개 장면(Tanabata, Factory, Pool)에 대해 각 장면마다 2가지 날씨 시나리오를 구성.(눈송이-snowflakes, 빗줄기-rain streaks/빗방울-raindrops)

        실제: 온라인에 공개된 실제 영상에서 *keyframe*을 추출해 멀티뷰 입력으로 사용(눈, 비) - GT가 없어서 *정성 비교* 중심

  - 평가 지표 및 실험결과 요약 :

        지표: *PSNR* / *SSIM* / *LPIPS*

    - 결과(합성 평균):
      - Snowy 평균: WeatherGS PSNR 25.066, SSIM 0.787, LPIPS 0.167
      - Rainy 평균: WeatherGS PSNR 23.670, SSIM 0.684, LPIPS 0.197

---

- DehazeGS
  - 논문명: DehazeGS: Seeing Through Fog with 3D Gaussian Splatting
  - 학회/저널: AAAI 2026
  - 주요 목적: 안개의 산란/감쇠를 대기 산란 모델(*ASM*) 기반하여 fog를 형성 후 fog-free 장면을 복원/렌더링
  - 실제/합성 데이터 기상 조건:

        합성: 대기 산란 모델로 제작

        실제: DehazeNerf에서 제공한 실내 3개 장면 (bear/elephant/lion), fog machine과 휴대폰으로 촬영된 데이터 사용.

  - 평가 지표 및 실험결과 요약:

        지표: PSNR / SSIM / LPIPS + 시간(학습/추론 시간 비교)

    - 결과:
      - 합성 평균: PSNR 19.83, SSIM 0.702, LPIPS 0.165
      - 실제 평균: PSNR 17.77, SSIM 0.742, LPIPS 0.157
      - 속도: *NeRF* 계열 대비 훨씬 빠른 속도(Additionally, our method achieves a rendering speed that is tens of times faster than that of NeRF-based methods.)

---

- DeRainGS
  - 논문명: **DeRainGS: Gaussian Splatting for Enhanced Scene Reconstruction in Rainy Environments**
  - 학회/저널: The Thirty-Ninth AAAI Conference on Artificial Intelligence
  - 주요 목적: 비오는 환경에서 향상된 장면 재구성을 위한 Gaussian Splatting (3DRRE)
  - 실제/합성 데이터 기상 조건 : 자체 제작 HydroViews 데이터셋, DerainNeRF
    - MipNeRF-360과 Tanks-and-Temples에 빗줄기/빗방울을 합성한 데이터셋
    - 실제로 촬영한 데이터셋 (빗줄기, 물방울 왜곡 포함)
  - 평가 지표 및 실험결과 요약: PSNR, SSIM, LPIPS
    - Deraining 성공적
    - 3DGS 단독 (PSNR 17.56) → 모든 모듈 결합(PSNR 24.67)

---

- Impact of Rain
  - 논문명: **Impact of Rain on 3D Reconstruction with Multi-View Stereo, Neural Radiance Fields and Gaussian Splatting**
  - 학회/저널: ISPRS 2025
  - 주요 목적: 다양한 3D Reconstruction 기술들에게 비 환경이 미치는 영향 분석
    - 어떤 것이 더 강건한가?
    - 비를 마스킹 처리했을 때 어떤 영향을 미치는가? (마스크가 완벽하지 못했음)
  - 실제/합성 데이터 기상 조건 : 직접 비를 뿌려 제작한 자체 데이터셋
    - General-Rain (일반 비): 카메라 플래시 없이 촬영. 비가 연속적인 선(Streaks) 형태로 나타나며, 이미지의 약 24%를 차지하는 마스크 범위를 가짐
    - Illuminated-Rain (조명된 비): 카메라 플래시를 사용하여 촬영. 비가 크고 밝은 고대비의 물방울(Droplets) 형태로 나타나 폐색 효과가 더 강함. 이미지의 약 4%를 차지하는 마스크 범위를 가짐.
    - [https://github.com/sqirrel3/STELLA](https://github.com/sqirrel3/STELLA)
  - 평가 지표 및 실험결과 요약
    - 평가 지표
      - Accuracy (정확도)↓: Mean, SD(표준편차), RMSE(Root Mean Squared Error).
      - Completeness (완전성)↑: 기준 메쉬에서 5mm 이내에 재구성된 포인트의 비율(%).
      - Efficiency (효율성)↓: Training Time.
    - 기타 생략, 3DGS의 경우…
      - 정확도 약 2배 이상 하락: 4.74mm → 8.42mm(General), 10.52mm(Illuminated)
      - 완전성 약 2~4배 하락: 82.75% → 41.79%(General), 25.12%(Illuminated)
      - 마스크 적용/비적용 큰 차이 없었음
        - General-Rain: 미적용(RMSE 8.42mm, Cpl 41.79%) → 적용(RMSE 8.50mm, Cpl = 40.53%)
        - Illuminated-Rain: 미적용(RMSE 10.52mm, Cpl 25.12%) → 적용(RMSE 10.35mm, Cpl 25.13%)

---

- Dehaze-attention
  - 논문명: **Dehaze-attention: enhancing image dehazing with a multi-scale, attention-based deep learning framework**
  - 학회/저널: *Scientific Reports* (Springer Nature), 2025
  - 주요 목적: 기존 디헤이징 기법들이 가변적인 헤이즈 강도에서 성능이 떨어지는 문제를 개선하기 위해, *멀티스케일 구조* + 어텐션 메커니즘 + 개선된 *K-value* 추정을 결합한 Dehaze-Attention 모델을 제안
  - 실제/합성 데이터 기상 조건:
    - *UDTIRI* 기반의 합성 헤이즈(synthesized hazy images) 로 평가
    - 헤이즈 강도는 **Light / Moderate / Dense** 3단계로 나눠 실험
  - 평가 지표 및 실험결과 요약:

        지표: PSNR, SSIM (정량), + 강도별 정성 비교

    - 강도별 Dehaze-Attention 성능
      - Light: PSNR 29.11 dB / SSIM 0.940
      - Moderate: PSNR 23.16 dB / SSIM 0.763
      - Dense: PSNR 21.47 dB / SSIM 0.681

---

- RaindropGS
  - 논문명: **RaindropGS: A Benchmark for 3D Gaussian Splatting under Raindrop Conditions**
  - 학회/저널: arXiv Preprint, 2025
  - 주요 목적:
    - 렌즈 부착 빗방울(Adherent Raindrop) 환경의 3DGS 통합 벤치마크 구축
    - 비제약적(Unconstrained) 입력 데이터 기반 전체 파이프라인(Pose Estimation, Point Cloud Initialization, Deraining, 3DGS Training) 성능 평가.
    - 카메라 초점(Focus) 변화에 따른 재구성 품질 저하 원인 분석.
  - 실제/합성 데이터 기상 조건:
    - 실제(Real-world) 빗방울 조건 (HydroViews 데이터셋 기반 확장).
    - 3개 데이터 세트: Raindrop-focused (RF), Background-focused (BF), Rain-free Ground Truth (GT).
  - 평가 지표 및 실험결과 요약:
    - 평가 지표: PSNR, SSIM, LPIPS, AUC@30 (Pose accuracy).
    - 카메라 포즈 추정 성능 (AUC@30 ↑):
      - COLMAP : BF(0.79), RF(0.17)
        - RF에서는 사실상 실패함.
      - VGGT : BF(0.91), RF(0.34)
        - COLMAP 대비 BF +15.2%, RF +100% 향상
        - 비교적 강건하지만 RF 환경에서 초기 포인트 클라우드 생성 수 0개 → 랜덤 초기화(100,000 points) 필수
    - 빗방울 제거(Deraining) 모델 성능 (PSNR ↑ / SSIM ↑):
      - Uformer : BF(28.997 / 0.880), RF(24.465 / 0.736)
      - Restormer : BF(28.442 / 0.861), RF(24.055 / 0.708)
    - 최종 3DGS 재구성 결과 (GS-W + VGGT + Uformer):
      - BF (배경 초점): PSNR=19.123, SSIM=0.555, LPIPS=0.483
        - Baseline 대비 PSNR +1.217dB
      - RF (빗방울 초점): PSNR=16.099, SSIM=0.512, LPIPS=0.808.
        - Baseline 대비 PSNR +2.205dB
    - 빗방울 초점 이미지(RF) 사용 시 배경 초점(BF) 대비 PSNR 약 4dB 하락.
