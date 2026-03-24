# WeatherGS 테스트 및 조사

상태: 완료

- **WeatherGS에서 인용된 논문 리스트업**
    
    # 1. 논문 정보
    
    **제목**
    
    *WeatherGS: 3D Scene Reconstruction in Adverse Weather Conditions via Gaussian Splatting*
    
    **한 줄 요약**
    
    WeatherGS는 **비·눈이 포함된 멀티뷰 이미지에서 날씨 아티팩트를 제거하고, 깨끗한 3D 장면을 복원하는 3DGS 기반 프레임워크**다. 핵심은 날씨로 인한 방해 요소를 **dense particles**와 **lens occlusions**로 나누고, 이를 **AEF → LED → masked 3DGS training** 순서로 처리하는 것이다.
    
    # 2. WeatherGS의 주요 축
    
    ### ① 3D 재구성 축
    
    NeRF 계열의 한계를 넘어, **3DGS를 백본으로 사용해 더 효율적이고 실시간성이 있는 3D 재구성**을 수행하는 축이다.
    
    ### ② Dense weather removal 축
    
    공기 중에 떠 있는 눈/비 입자를 **diffusion 기반 AEF**로 먼저 제거하는 축이다.
    
    ### ③ Lens occlusion handling 축
    
    렌즈에 붙은 물방울/눈으로 생긴 가림은 **LED로 검출하고 mask로 loss에서 제외**하는 축이다.
    
    # 3. 주요 6개 논문
    
    ### 1) NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis
    
    - **역할**: WeatherGS가 넘어서는 출발점
    - **의미**: 기존 radiance field 기반 3D 재구성의 대표 논문이며, WeatherGS는 NeRF가 dynamic weather particles에 취약하다는 점을 문제로 삼는다.
        
        <img width="579" height="130" alt="스크린샷_2026-03-12_215738" src="https://github.com/user-attachments/assets/3c6bf4c1-8c2a-4ced-aa03-e8e2818d84e9" />


    ### 2) 3D Gaussian Splatting for Real-Time Radiance Field Rendering
    
    - **역할**: WeatherGS의 핵심 백본
    - **의미**: WeatherGS는 이 논문의 3DGS를 기반으로 장면을 복원하고, 실험에서는 원본 3DGS를 vanilla baseline으로 비교한다.
        
    <img width="820" height="163" alt="스크린샷_2026-03-09_001348" src="https://github.com/user-attachments/assets/a5a6e8bd-ff81-4b2d-bfb1-890ac8050ad1" />

        
    ### 3) DerainNeRF: 3D Scene Estimation with Adhesive Waterdrop Removal
    
    - **역할**: 가장 직접적인 3D adverse-weather 선행연구
    - **의미**: 3D 공간에서 weather effect removal을 시도한 직접적인 prior work로, WeatherGS는 이를 확장해 snow/rain streak/lens occlusion까지 더 넓게 다룬다.
        
    <img width="676" height="123" alt="스크린샷_2026-03-12_220017" src="https://github.com/user-attachments/assets/6ddab54e-71d7-4d7c-8f76-d958e43180e5" />
        
    
    ### 4) High-Resolution Image Synthesis with Latent Diffusion Models
    
    - **역할**: AEF의 diffusion backbone
    - **의미**: WeatherGS의 AEF는 latent diffusion 기반 복원 아이디어 위에서 동작한다.
    
    ### 5) Diff-Plugin: Revitalizing Details for Diffusion-Based Low-Level Tasks
    
    - **역할**: AEF를 성립시키는 핵심 모듈 논문
    - **의미**: WeatherGS는 이 논문의 weather-specific prior / task plugin 아이디어를 따라 diffusion이 장면 내용을 덜 왜곡하면서 weather artifact를 제거하도록 유도한다. GitHub README에서도 WeatherGS가 DiffPlugin 위에 구축되었다고 명시한다.
    
    ### 6) Attentive Generative Adversarial Network for Raindrop Removal from a Single Image
    
    - **역할**: LED의 핵심 출처
    - **의미**: WeatherGS의 LED는 이 논문의 detection module을 활용해 렌즈 가림을 찾는다. GitHub README에서도 AttGAN 기반임을 밝힌다.
        
    <img width="669" height="195" alt="스크린샷_2026-03-12_220312" src="https://github.com/user-attachments/assets/25c472d4-747e-4abf-9b82-1d3e37144b23" />

    
    # 4. 인용 논문의 큰 갈래
    
    **전체 reference 항목**: 42개
    
    ### A. 기존 3D reconstruction 문제 설정용 논문
    
    저조도·블러 같은 기존 문제를 다룬 논문들이다.
    
    예: **Lighting up NeRF**, **Aleth-NeRF**, **DP-NeRF**, **Deblur-GS**
    
    → WeatherGS는 이를 통해 “기존 연구는 weather보다 illumination/blur 쪽에 집중했다”는 문제의식을 만든다.
    
    ### B. 직접적인 3D adverse-weather 선행연구
    
    예: **DerainNeRF**
    
    → WeatherGS와 가장 직접적으로 연결되는 3D weather removal 계열 논문이다.
    
    ### C. 3DGS 일반 배경 및 확장 연구
    
    예: **3DGS**, **Motion-aware 3DGS**, **Dynamic 3D Gaussians**, **4D Gaussian Splatting**, **Gaussian in the Wild**
    
    → 3DGS가 이미 dynamic scene, unconstrained collection, editing 등으로 확장되어 왔음을 보여주며, WeatherGS는 그 흐름을 악천후로 확장한다.
    
    ### D. 2D weather effect removal 연구
    
    예: **DesnowNet**, **DDMSNet**, **Progressive Image Deraining**, **AttGAN**, **AllWeather-Net**, **TransWeather**
    
    → 눈 제거, 비 제거, 렌즈 물방울 제거 등 2D 저수준 복원 연구의 축이다. WeatherGS는 이 계열을 3D reconstruction 파이프라인에 끌어온다.
    
    ### E. WeatherGS 모듈 구현에 직접 쓰인 building block 논문
    
    예: **Latent Diffusion Models**, **Diff-Plugin**, **CLIP**, **ResNet**, **VAE**, **Attentive GAN for Raindrop Removal**, **SfM Revisited**
    
    → AEF, LED, 3DGS 초기화가 실제로 어떤 기술 위에 세워져 있는지 보여주는 모듈성 참고문헌이다.
    
    ### F. 데이터셋/평가용 참고문헌
    
    예: **Deblur-NeRF**, **LPIPS**, Blender reference, video links
    
    → synthetic benchmark 생성과 perceptual metric 평가를 위한 참고문헌들이다.
    

---

- **날씨 환경 데이터 변환 모델 정리**
    
    ### 1. Dataset
    
    - **활용 가능성**: WeatherGS 재현 실험, baseline 비교, adverse weather 3D reconstruction 성능 평가용 benchmark로 활용 가능.
    - **근거**: 프로젝트 페이지에서 저자들은 adverse weather 3D reconstruction 평가를 위한 **benchmark**를 구축했고, 다양한 weather scenario에서 성능을 검증했다고 설명한다.
    
    ### 2. WeatherEdit
    
    - **활용 가능성**: 기존 3D Gaussian scene에 **비·눈·안개를 인위적으로 추가**해서 데이터 증강, 강도별 robustness 테스트, synthetic adverse-weather scene 생성에 활용 가능.
    - **근거**: WeatherEdit는 “**Controllable Weather Editing with 4D Gaussian Field**”로 소개되며, **snow/fog/rain 지원**, **light/moderate/heavy 강도 조절**, **multi-view driving scene의 temporal/spatial consistency**를 제공한다고 명시한다.
    
    ### 3. AllWeatherNet
    
    - **활용 가능성**: 악천후 이미지를 깨끗하게 만드는 **2D 전처리/복원 모델**로 활용 가능하고, WeatherGS 같은 3D reconstruction 전에 입력 이미지를 개선하는 용도나 2D restoration baseline 비교용으로도 쓸 수 있음.
    - **근거**: AllWeatherNet은 **snow, rain, fog, low-light** 환경에서 촬영된 이미지를 개선하는 **unified image enhancement framework**로 소개되며, adverse weather image와 normal weather image를 대응시켜 학습하는 구조를 사용한다.
    
    ### 4. WeatherDG
    
    - **활용 가능성**: 악천후 주행 장면을 **생성형 방식으로 증강**해서 segmentation 학습 데이터를 늘리거나, domain generalization 실험용 weathered dataset 생성에 활용 가능.
    - **근거**: WeatherDG는 **LLM-assisted diffusion model**로 **snow, rain, fog, low-light** 조건의 자율주행 장면 이미지를 생성하고, 이렇게 만든 데이터를 **semantic segmentation training**에 사용할 수 있다고 설명한다.

---

- **비/눈을 포함한 렌더링을 진행하는 GS 계열 모델**
    - 논문: **RainyGS (CVPR 2025)**
    - 날씨: 비
    - 핵심 아이디어: 
    3DGS 장면 위에 물리 기반 비 시뮬레이션을 얹어, 빗줄기뿐 아니라 바닥의 물, 반사·굴절 같은 고차 효과까지 포함한 photorealistic rain rendering을 목표로 함.
    - 구조: 
    멀티뷰 입력 → 3DGS로 장면 재구성 → 물리 기반 raindrop + shallow water simulation → rainy novel view 렌더링.
    
    - 논문: **WeatherEdit (2025)**
    - 날씨: 눈 / 비 / 안개
    - 핵심 아이디어: 
    3D scene에 날씨를 제어 가능하게 추가하는 weather editing 프레임워크. 배경 날씨는 diffusion으로 편집하고, 입자는 4D Gaussian field로 생성해 종류와 강도를 조절함.
    - 구조: 
    2D weather background editing → multi-view / multi-frame consistency 보정(TV-attention) → 3D scene 재구성 → 4D Gaussian field로 snowflakes / raindrops / fog 생성 → 최종 렌더링.
    
    - 논문: **Let it Snow! (2025)**
    - 날씨: 눈 / 비 / 안개 / sandstorm
    - 핵심 아이디어: 
    정적인 3DGS 장면에 동적인 전역 날씨 효과를 추가하는 데 초점. 날씨를 단순 오버레이가 아니라 물리적으로 자연스럽게 움직이는 particle dynamics로 다룸.
    - 구조: 
    static 3D Gaussians → particle representation으로 변환 → MPM(Material Point Method)으로 동적 입자 시뮬레이션 → Gaussian domain으로 다시 매핑 → weathered view 렌더링.
    
    - 논문: **Weather-Magician (2025)**
    - 날씨: 다양한 4D weather effects
    - 핵심 아이디어: 
    실제 장면을 빠르게 재구성한 뒤, 그 위에 시간적으로 변하는 4D 날씨 효과를 입혀 실시간 렌더링을 지향함. 공개 초록 기준으로는 개별 날씨 목록보다 연속적 weather synthesis와 real-time성이 강조됨
    - 구조: 
    real scene capture → Gaussian Splatting 기반 장면 재구성 → synthesized 4D weather effects 결합 → real-time weather rendering.
