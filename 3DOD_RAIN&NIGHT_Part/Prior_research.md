## 조사 필요한 논문 목록

| 논문명 | 학회/저널 | 연도 | 방법론 | KD 여부 | rain 포함 | night 포함 | 기타 | 링크 |
|---|---|---|---|---|---|---|---|---|
| **MoME** | CVPR | 2025 | Mixture of Experts + Adaptive Query Router (AQR) | X | O | O | nuScenes-C/R에서 Rain, Night, Fog, Snow, Sunlight 전 조건 명시 벤치마킹. 현재 해당 조건 내 최고 티어 논문 | [Link](https://arxiv.org/abs/2503.19776) |
| **AWARDistill** | Expert Systems with Applications | 2024 | Knowledge Distillation | O | O | X | 조건 내 유일한 KD 기반 논문. fog/rain/snow 대상. 야간 조건 미포함 | [Link](https://www.sciencedirect.com/science/article/abs/pii/S0957417424028999) |
| **ContextualFusion** | IEEE | 2024 | Gated Convolutional Fusion (GatedConv) | X | O | O | Day/Night, Clear/Rain 4가지 조건 명시 타깃. 자체 합성 데이터셋 AdverseOp3D 구축. nuScenes 야간에서 mAP +11.7% | [Link](https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=10588584&casa_token=qknElEItEC0AAAAA:NBUUtvoxn110bT9gdO31GCMSwLJWSXiMiFIv79LmLxyBH7vcZA8u--UG2DVvT45j0r7C-3XM_g) |
| **FlexFusion** | arXiv (미게재) | 2024 | 적응형 가중치 퓨전 전략 | X | O | X | fog/rain/snow/sunlight 4가지 날씨 조건 체계적 분석. 야간 조건 미포함. 방법론보다 분석 관점의 논문 | [Link](https://arxiv.org/abs/2402.02738) |
| **TransFusion** | CVPR | 2022 | Transformer 기반 soft-association 퓨전 | X | X | O | 야간/저조도를 명시적 motivation으로 언급. rain 직접 타깃은 아님. 해당 분야 핵심 베이스라인으로 광범위하게 활용됨 | [Link](https://openaccess.thecvf.com/content/CVPR2022/papers/Bai_TransFusion_Robust_LiDAR-Camera_Fusion_for_3D_Object_Detection_With_Transformers_CVPR_2022_paper.pdf) |

---

## 조사 내용 상세

- Improving Robustness of LiDAR-Camera Fusion Model against Weather Corruption from Fusion Strategy Perspective
    
    github 따로 공개 X
    
    **전체 요약** 
    
    **악천후 환경에서 LiDAR+카메라 fusion 모델의 성능 저하 이유를 분석하고, 상황에 따라 가중치를 바꿔서 robustness를 높이는 개선 방법 제안 (experimental paper)**
    
    **problem setting**
    
    **LiDAR + Camera fusion model의 경우 3D object detection에서 성능 좋으나 현실에는 fog / rain / snow / sunlight 같은 weather corruption 존재**, 이런 상황에서는 robustness가 잘 연구되지 않음 
    
    → Fusion 방식에 따라 날씨 조건마다 robustness가 다른지 성능 비교 분석
    
    → LiDAR vs Camera 중 날씨 조건이 추가되었을 때 어떤 게 더 중요한지
    
    **분석 실험**
    
    - Dataset
    **KITTI validation set에 weather 추가한 KITTI-C** 생성
        - weather - snow / rain / fog / sunlight
        - strength - low / high
        
        **image의 경우 imgaug, automold 같은 라이브러리 사용해 합성
        LiDAR의 경우 LISA 같은 물리 기반 시뮬레이션 사용
        → 이부분 조사해봐도 좋을 것 같음** 
        
        train: 원래 KITTI / test: KITTI-C
        
    - Metric
    3D AP, BEV AP
    RCE (Relative Corruption Error) = (AP - APc) / AP 클수록 robust X
    - Fusion 모델 종류
        - Image-led (Camera 중심)
        LiDAR → 이미지로 변환
        - Point cloud-led (LiDAR 중심)
        이미지 정보를 LiDAR에 붙임
        - Intermediate modal (중간 표현 기반)
        둘 다 다른 공간으로 변환 후 fusion
        
        Virtual (point-based) / Voxel / Ray / BEV 네가지 모델 사용
        
    - result
    **날씨마다 성능 떨어지는 패턴이 다르고, fusion 방식에 따라 robustness 차이가 크며, virtual (point-based) 방식이 가장 튼튼했음**
    → virtual point*가 semantic + depth 정보를 둘 다 잘 담고 있기 때문
        - 날씨 별 영향
        Rain / Snow (최악) - AP 30% 이상 감소
        Fog (중간) - 약 ~15% 감소
        Sunlight (거의 영향 없음)
        
        *Virtual (point-based) 모델
        LiDAR와 카메라를 결합할 때, 실제 LiDAR 점(Point)뿐만 아니라 카메라 정보를 이용해 ‘가상의 포인트’를 만들어서 fusion 하는 방식
        
        - 가상 포인트(Virtual Point) = 실제 3D 점이 아니지만, 이미지 정보를 3D 공간에 투영해서 만든 포인트
        - 이렇게 하면 LiDAR가 sparse해도, 카메라에서 얻은 풍부한 semantic 정보를 3D 공간에서 활용 가능
    
    **proposed method**
    
    **기존에는 LiDAR + Camera를 동일하게 fusion했으나 분석 결과 상황에 따라 중요한 센서가 다르므로 Light & Camera weight를 조정해서 fusion**
    
    **F = wP * FP + wI * FI**
    
    ![image.png](attachment:a20842bc-bb71-47fb-8385-467de2b6ec13:image.png)
    
    **method 적용 결과**
    
    - clean 데이터 성능 유지 & weather에서는 성능 증가
    - **Rain / Snow - Camera weight ↑ 시 성능 개선 
    Fog - 일정한 패턴 없음
    Sunlight - LiDAR weight ↑ 시 성능 개선**
    
    ![image.png](attachment:eb6fb7fe-48c2-4fbe-a362-56c63c13eef9:image.png)
    
    *Sigmoid는 전역 가중치를 통해 모달 간비중을 조절하는 반면, Attention은 위치별·특징별 상호작용을 기반으로 동적으로 feature에 가중치를 할당하는 메커니즘
---
  - TransFusion: Robust LiDAR-Camera Fusion for 3D Object Detection with Transformers
    
    https://github.com/xuyangbai/transfusion
    
    **코드 O, pretrained model X**
    
    **전체 요약**
    
    **LiDAR와 카메라를 결합한 3D 객체 검출에서 Transformer 기반 soft-association fusion과 query initialization 전략을 제안하여,**
    
    - **sparse LiDAR와 고해상도 이미지 데이터를 효과적으로 결합**
    - **야간, 이미지 결손, 센서 misalignment 등 열악한 환경에서도 robust 성능 달성**
    - **nuScenes와 Waymo benchmark에서 기존 LiDAR-only / fusion SOTA 대비 높은 mAP/NDS/APH 달성**
    
    **Problem Setting**
    
    - LiDAR-only 3D detection → 정확하지만 sparse point 때문에 멀리 있는 객체 / 작은 객체 detection 어렵다
    - Camera-only → 고해상도 semantic 정보 활용 가능하지만 depth 정보 부재
    - **기존 LiDAR-Camera fusion 방식
     point-wise hard-association* / voxel fusion***
        
        **→ LiDAR가 sparse하거나, 이미지에 결손이 있거나, 카메라와 LiDAR 센서 간 calibration 오류가 있으면 성능이 크게 떨어짐**
        
    - 목표: **adaptive fusion** + **robust 초기 query** → 열악한 환경에서도 안정적 detection 가능
    
    point-wise hard-association - LiDAR 포인트 하나마다 카메라 픽셀(feature)를 **딱 하나씩 매칭**해서 feature를 붙이는 방식
    voxel fusion - LiDAR 점들을 3D voxel grid로 변환 후 voxel 단위로 이미지를 fusion
    
    **제안 방법 (High-level)**
    
    ![image.png](attachment:c68c48b5-7743-45c3-bc18-f370565565e1:image.png)
    
    Query Initialization
    
    - Input-dependent: LiDAR BEV heatmap 기반 **top-N object candidates 선택(가장 있을법한 객체 검출)** → 1 decoder layer로 충분한 초기 bounding box 확보
    - Category-aware: **object feature에 category embedding 추가** → intra-category variance modeling 향상
    
    ![image.png](attachment:abcae618-abeb-4d33-817f-2bc669b4a39f:image.png)
    
    첫 번째: 입력 이미지 + 객체 후보(object queries)를 이미지 위에 투영한 결과
    → 모델이 “여기 객체가 있다”라고 판단한 위치를 보여줌
    두 번째: cross-attention 맵
    → 모델이 객체 후보가 이미지에서 어떤 영역(feature)에 주목했는지) 보여줌
    
    Transformer Decoder & Fusion
    
    - Self-attention: object-object(객체 후보끼리) 관계 학습
    - Cross-attention: object query ↔ LiDAR / 이미지 feature 연결
    - **SMCA (Spatially Modulated Cross Attention):**
        - 2D Gaussian mask로 projected box 주변 image feature에 집중
        - sensor misalignment(조금 안 맞는 센서 위치) 및 sparse LiDAR 환경에서도 robust (예상 후보 주변에만 집중하므로)
        
    
    Image-guided Query Initialization
    
    - LiDAR+Camera BEV feature fusion → 작은 객체 / sparse LiDAR에서도 query recall 향상
    
    **실험 설정 / Benchmarking**
    
    - **Datasets: nuScenes, Waymo**
    - Metrics: mAP, NDS, mAPH (Waymo), BEV 중심 기준
    - **Variants / Baselines:**
        - TransFusion-L (LiDAR-only)
        - TransFusion (full fusion)
        - CC / PA (기존 fusion methods)
    - **Robustness Tests:**
        - **Night vs Day**
        - Dropped images (0~6)
        - Sensor misalignment (translation offsets)
    
    **핵심 결과 / Observations**
    
    **Main Detection Performance**
    
    ![image.png](attachment:e0a98dd7-eb29-4358-a1e8-5ea008151cd7:image.png)
    
    - TransFusion-L already outperforms LiDAR-only SOTA
    - Fusion + query init → mAP + NDS 크게 향상
    - 멀리 있는 객체 detection 성능 크게 개선
    
    Robustness to Inferior Image Conditions
    
    - **Nighttime: 기존 fusion 대비 mAP +6%**
    
    ![image.png](attachment:ffbadbe6-99d5-481c-9997-8b9ed636761c:image.png)
    
    - Dropped Images(이미지 일부 손실): CC/PA mAP 39~47% → TransFusion 61.7% 유지
    - Sensor misalignment: 1m offset → mAP 0.49% drop (CC/PA 2~3%)
    
    Ablation Studies
    
    - Query Initialization: Input-dependent + Category-aware → decoder layer 최소화 가능
    - Image-guided query init + SMCA fusion → distant & small objects detection 향상
    - Fusion module 없으면 성능 4~5% 하락
    
    **결론 / Takeaways**
    
    - Soft-association Transformer fusion → robust 3D detection
    - Input-dependent & category-aware query initialization → sparse LiDAR에서도 strong baseline
    - **이미지 결손, 야간, 센서 오정렬 환경에서도 기존 fusion 대비 강력한 성능**
    - 향후: segmentation 등 다른 3D perception task에도 적용 가능

---
- **MoME : Resilient sensor fusion under adverse sensor failures via multi-modal expert fusion**

    * **(1) 개요**
      
      | 항목 | 내용 |
      |---|---|
      | **학회** | CVPR 2025 |
      | **입력** | LiDAR + Camera |
      | **평가 데이터셋** | nuScenes, nuScenes-R, nuScenes-C |
      | **방법론** | Mixture of Experts + Adaptive Query Router |
      | **타깃 조건** | 센서 고장 (LiDAR/Camera drop 등), 극한 날씨 (fog, snow, sunlight) |
      | **GitHub** | [https://github.com/konyul/MoME](https://github.com/konyul/MoME) |

    * **(2) 논문 제안 배경**
      * 기존 퓨전 모델은 LiDAR와 카메라 피처를 하나로 합쳐 단일 decoder로 처리하는 구조.
      * 이 구조에서는 두 모달리티 사이에 강한 의존성이 생겨, 한쪽이 오염되면 반대쪽 피처까지 영향을 받는 문제가 발생함.
      * 센서 고장 상황에서도 정상 작동하는 퓨전 모델의 구현을 목적으로 함.
      * 각 탐지 쿼리를 decoder를 이용해 라우팅해 오염된 정보의 영향을 최소화함.

    * **(3) 방법론**
      * **전체 구조도** (메인 figure)
        <br>![image.png](image.png)
      * **입력 처리:**
        * LiDAR 포인트 클라우드: VoxelNet을 통해 BEV 피처 맵으로 변환
        * 카메라 이미지: VoVNet을 통해 2D 피처 추출 이후 BEV 공간으로 투영
        * 두 BEV 피처를 이어붙여 결합 피처(F'lc) 생성 → AQR의 참고 자료로 활용
      * **MED (Multi-Expert Decoding):**
        * 하나의 decoder 대신에, 서로 다른 역할의 세 decoder를 병렬로 운영.
        * 각 decoder는 서로 독립적으로 학습되므로 한 decoder의 입력이 오염돼도 다른 decoder에 영향 없음.
        
        | Decoder | 사용 피처 | 최적 상황 |
        |---|---|---|
        | **LiDAR Decoder** | LiDAR 피처만 | 카메라 고장 시 |
        | **Camera Decoder** | Camera 피처만 | LiDAR 고장 시 |
        | **LiDAR-Camera Decoder** | 둘 다 결합 | 두 센서 모두 정상 시 |

      * **AQR (Adaptive Query Router):**
        * 각 탐지 쿼리가 가리키는 위치 주변의 로컬 피처를 LAM(Local Attention Mask)으로 추출.
        * cross-attention을 통해 세 decoder에 대한 선택 확률을 계산해 가장 적합한 decoder로 라우팅.
        * LAM 적용 시 전체 피처 맵이 아닌 쿼리 주변 로컬 영역만 참고해 라우팅 정확도 향상.
      * **학습 전략:**
        * 1단계: 세 decoder를 독립적으로 학습
        * 2단계: decoder 고정 후 AQR만 학습. LiDAR와 Camera를 각각 1/3 확률로 완전히 제거하는 sensor drop augmentation 적용.

    * **(4) 실험 결과 및 결론**
      * **센서 고장 시나리오에서의 성능**
        <br>![image.png](image%201.png)
        * Perf. Ratio R (Clean 성능 대비 악조건 평균 성능의 비율)은 ours가 CMT 대비 mAP +2.1
        * Limited FOV(부분적 센서 열화) 시나리오에서 ours가 CMT 대비 mAP +6.7
        * **⇒ 악조건(센서 열화 등)에서 성능이 덜 떨어지는 robustness 증명.**
      * **악천후 성능 (nuScenes val 데이터셋 사용)**
        <br>![image.png](image%202.png)
        * rainy mAP이 ours가 72.2로 기존 SOTA인 CMT 대비 +1.7
        * night mAP이 ours가 43.0으로 CMT 대비 +0.2
        * **⇒ 악천후 상황을 고려해 개발한 모델이 아니라, 비교적 성능 개선이 덜함.**

    * **(5) 활용 가능한 부분들**
      * rain, night 등의 악천후를 학습 목표로 한 연구가 아님. rain, night의 경우 재학습 없이 평가만 진행함.
      * nuScenes 기준 성능 수치가 공개되어 있어 비교 기준으로 활용 가능.
      * 위 연구는 악천후 강건성이 목표가 아니었을 뿐만 아니라 KD를 활용하지도 않았기에 이를 추가/활용하는 방향으로 개선 가능.
---
- **AWARDistill: Adaptive and robust 3D object detection in adverse conditions through knowledge distillation**

    * **(1) 개요**
      
      | 항목 | 내용 |
      |---|---|
      | **학회/저널** | Expert Systems With Applications, 2024 |
      | **입력** | LiDAR + Camera |
      | **평가 데이터셋** | KITTI, KITTI-C, KITTI-M, nuScenes, nuScenes-C, WOD-DA |
      | **방법론** | Staged Knowledge Distillation (clean teacher → adverse student) |
      | **타깃 조건** | Fog, Rain, Snow, Strong Light |
      | **GitHub** | 공개 X |

    * **(2) 논문 제안 배경**
      * 기존 멀티모달 퓨전 모델은 맑은 날 데이터로 학습되어 악천후 환경에서 성능이 크게 저하되는 문제 발생.
      * 실제 악천후 데이터의 수집이 어렵고, 기존 시뮬레이션 방법은 LiDAR와 카메라를 별도로 시뮬레이션해 두 모달리티 간 날씨 강도가 일치하지 않는 문제가 발생.
      * 위 두 문제를 동시에 해결하기 위해 물리 기반 멀티모달 악천후 시뮬레이션(MIST)과 KD 기반 학습 전략(AWARDistill)을 함께 제안.

    * **(3) 방법론**
      * **전체 구조도**
        <br>![image.png](image%203.png)
      * **MIST (Multi-modal Adverse-Weather Data Simulation Theory):**
        * fog, rain, snow, 강한 빛 4가지 악천후를 물리 모델 기반으로 시뮬레이션.
        * LiDAR와 카메라 시뮬레이션을 소광 계수(extinction coefficient)로 연동해 두 모달리티 간 날씨 강도 일관성 보장.
      * **RADAR (Robust Asynchronous Data Alignment):**
        * LiDAR와 카메라의 샘플링 시간 차이로 인한 모달리티 정렬 오차를 보정하는 모듈.
        * 차량 이동 모델을 통해 LiDAR 포인트를 카메라 타이밍에 맞춰 정렬. 다른 모델에도 plug-in 형태로 통합 가능.
      * **WSD (Adverse-Weather Scene Distillation):**
        * teacher(맑은 날씨)와 student(악천후)의 피처 맵 간 구조적 유사성을 맞추는 feature 레벨의 KD.
        * 피처 값을 직접 복사하는 대신, 피처들 사이의 관계(affinity matrix)를 일치시켜 날씨가 달라도 구조적 지식이 전달되도록 설계.
      * **EAFD (Entropy-driven Adaptive Feature Distillation):**
        * 데이터 블록별 entropy를 계산해 날씨 열화 정도를 정량화하고, 열화가 심한 영역은 학습 가중치를 낮추는 적응형 feature KD.
        * foreground 객체 중심 Gaussian mask를 적용해 배경 노이즈 간섭을 최소화.
      * **DART (Distance-Aware Response Distillation):**
        * 거리가 멀수록 LiDAR SNR(신호 대 잡음비)이 급격히 감소하는 물리 원칙에 기반한 response 레벨 KD.
        * 비선형 함수로 근거리 객체에 높은 학습 가중치 부여. classification loss + regression loss 모두 적용.
      * **SNOW (Suppressing Noise from adverse Weather):**
        * 안개, 물 분무, 눈보라 등 악천후 노이즈가 false positive를 유발하는 문제를 해결하는 모듈.
        * 예측 바운딩 박스 내 노이즈 비율을 계산해 노이즈성 바운딩 박스의 가중치를 조정.
      * **학습 전략:**
        * clean 환경으로 학습된 teacher 네트워크가 MIST로 생성된 악천후 데이터를 입력받는 student 네트워크를 단계적으로 지도.
        * AWSD → EAFD → DART → SNOW 순으로 모듈을 추가하며 학습.

    * **(4) 실험 결과 및 결론**
      * **악천후에서의 성능 비교**
        <br>![image.png](image%204.png)
        * KITTI-C Fog에서 car 클래스에 대해 ours가 EPNet(LiDAR-camera 퓨전 모델) 대비 AP +35.44
        * KITTI-C Rain에서 car 클래스에 대해 ours가 EPNet 대비 AP +38.58
        <br>![image.png](image%205.png)
        * nuScenes-C Fog에서 ours가 BEVFusion 대비 mAP +6.01
        * nuScenes-C Rain에서 ours가 BEVFusion 대비 mAP +0.80

    * **(5) 활용 가능한 부분들**
      * RADAR, SNOW 모듈의 경우 플러그인의 형태라 활용 가능.
      * night 데이터가 포함되어 있지 않았기에 이를 추가하는 방향 고려 가능.
---
- **ContextualFusion: Context-Based Multi-Sensor Fusion for 3D Object Detection in Adverse Operating Conditions**

    * **(1) 개요**
      
      | 항목 | 내용 |
      |---|---|
      | **학회/저널** | IEEE 2024 |
      | **입력** | LiDAR + Camera |
      | **평가 데이터셋** | nuScenes, AdverseOp3D (CARLA 기반 자체 합성 데이터셋) |
      | **방법론** | Gated Convolutional Fusion (GatedConv) |
      | **타깃 조건** | Rain, Night |
      | **GitHub** | 공개 X |

    * **(2) 논문 제안 배경**
      * 기존 LiDAR-Camera 퓨전 모델(BEVFusion 등)은 두 센서를 항상 동일한 비중으로 처리하는 context-agnostic 방식으로, 야간이나 비 환경에서 성능이 크게 저하되는 문제 발생.
      * 야간에는 카메라가 거의 무력화되는 반면 LiDAR는 정상 작동하고, 비에서는 LiDAR 빔이 산란되어 false positive가 증가하는 등 두 센서의 열화 방향이 환경마다 다름.
      * 기존 nuScenes 데이터셋은 맑은 낮 scene이 대다수(night 11.6%, rain+night 1.6%)로 악천후 학습에 불리한 구조.
      * 위 문제들을 해결하기 위해 환경 context(낮/밤, 비/맑음)를 퓨전 단계에 명시적으로 주입해 센서 가중치를 동적으로 조절하는 방식과, 악천후 균형 데이터셋(AdverseOp3D)을 함께 제안.

    * **(3) 방법론**
      * **전체 구조도** (논문 내 figure 4)
        <br>![image.png](image%206.png)
      * **입력 처리:**
        * LiDAR 포인트 클라우드: VoxelNet을 통해 BEV 피처 맵으로 변환 (80채널, 180×180)
        * 카메라 이미지: SwinTransformer를 통해 2D 피처 추출, BEV 공간으로 투영 (256채널, 180×180)
        * 두 BEV 피처를 이어붙여 결합 피처 생성 → GatedConv의 입력으로 활용
      * **AdverseOp3D:**
        * CARLA 시뮬레이터를 활용해 nuScenes와 동일한 센서 구성(카메라 6개 + LiDAR 1개)으로 합성 데이터 생성.
        * 4000개 이상의 샘플 중 75% 이상을 악천후 조건 (Night+Clear 25%, Day+Rain 25%, Night+Rain 25%)으로 구성하여 nuScenes의 데이터 편향 문제를 보완.
      * **GatedConv (Gated Convolutional Fusion):**
        * 환경 context(day/night, rain/clear)를 이진값으로 입력받아 LiDAR와 카메라 피처 채널별 가중치 벡터 G1, G2 생성.
        * 일반 컨볼루션과 달리 LiDAR 채널 그룹과 카메라 채널 그룹에 각각 다른 가중치를 곱한 후 컨볼루션을 수행. (예: 야간에는 G1(LiDAR)이 높아지고 G2(카메라)가 낮아지도록 학습)
        * **두 가지 변형 운영:**
          
          | 변형 | 설명 | 특징 |
          |---|---|---|
          | **CF (Constrained)** | G1, G2가 모달리티 내 모든 채널에 동일한 값 적용 | 단순한 구조 |
          | **CF (Independent)** | G1, G2가 채널별로 독립적으로 학습 | 더 세밀한 조절 가능, 야간에서 더 우수 |

      * **학습 전략:**
        * BEVFusion의 사전학습 가중치를 불러와 GatedConv의 추가 가중치만 새로 학습.
        * 학습 데이터: nuScenes 전체 학습셋(34,000샘플) + AdverseOp3D

    * **(4) 실험 결과 및 결론**
      * **악천후에서의 성능 개선**
        <br>![image.png](image%207.png)
        * Night 조건에서 CF(Independent)가 BEVFusion 대비 mAP +11.7
        * Rain 조건에서 CF(Independent)가 BEVFusion 대비 mAP +1.4

    * **(5) 활용 가능한 부분들**
      * KD 구조가 없기에 추가 가능성 고려.
     
## 코드 및 Weight 공개 여부

| 논문명 | 코드 공개 | Weight 공개 | 깃허브 링크 |
| --- | --- | --- | --- |
| **MoME** | O | O | [https://github.com/konyul/MoME](https://github.com/konyul/MoME) |
| **AWARDistill** | X | X | X |
| **ContextualFusion** | O | O | [https://github.com/ssuralcmu/ContextualFusion](https://github.com/ssuralcmu/ContextualFusion) |
| **FlexFusion** | X | X | X |
| **TransFusion** | O | X | [https://github.com/XuyangBai/TransFusion](https://github.com/XuyangBai/TransFusion) |

---

## MoME 모델 추가 조사

* **학습 데이터:**
  * nuScenes 학습셋 사용 (700개 scene)
  * 악천후 데이터 포함 X
  * sensor drop augmentation(LiDAR 또는 카메라를 1/3 확률로 완전히 제거) 적용
* **평가 데이터:**
  * nuScenes validation set (150개 scene)
