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
