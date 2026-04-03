## 추진배경
◯  자율주행, 로보틱스, 디지털 트윈 분야에서 3D Reconstruction 및 Object Detection 기술은 필수적이나, 대부분의 기존 모델은 맑은 날씨의 데이터셋을 기준으로 학습되어 있음.
◯  우천, 안개, 폭설 등 기상 악조건에서는 빛의 산란과 굴조 현상으로 인해 센서 데이터의 노이즈가 심화되며, 이는 모델의 성능 안정성을 저하시키는 주요 원인이 됨. 
◯ 실제 환경에서 모든 날씨 데이터를 수집하는 것은 비용과 안전 측면에서 한계가 있으므로, 시뮬레이션을 통한 고도화된 검증 체계 마련이 시급함.

## 1. 프로젝트 목표 
◯ 다양한 기상 환경을 모사한 합성 데이터를 생성하고, 최신 3D Vision 모델(3D Gaussian Splatting 기반 및 Detection 기반)의 Task 수행 능력을 정량적으로 검증 및 분석하고, 이를 통해 기상 악조건에 강건한 3D Vision 모델 개발 및 성능 최적화를 목표로 함.

## 2. 프로젝트 내용

### 1) 야간(Night) 및 우천(Rain) 환경 강건 3DOD 모델 개발
◯ 야간 및 우천 환경 데이터셋 구축: nuScenes 데이터셋에서 scene metadata를 활용해 night / rain 조건 장면을 선별하고, 클래스별 성능 평가를 위한 실험용 subset을 구축함.
◯ Baseline 모델 성능 분석: 선정된 3DOD baseline 모델을 재현하여 악천후 환경에서의 성능 저하를 정량적으로 분석함.
◯ Knowledge Distillation 기반 성능 개선: baseline 모델을 teacher-student 구조로 학습시켜, 야간 및 우천 환경에서의 탐지 성능을 향상시키고, multi-modal sensor (LiDAR + Camera) fusion 등 robust learning 전략을 적용함.
◯ 성능 검증 및 비교 실험: 원본 baseline 대비 향상된 성능을 정량/정성 평가하고, 악천후 환경에서의 개선 효과를 분석함.

그림  MoME 대표그림

### 2) 3D Reconstruction 모델 검증 및 개선 (LongSplat 등)
◯ LongSplat과 같은 최신 Gaussian Splatting 모델을 대상으로, 기상 노이즈가 3D 공간 복원력 및 렌더링 품질(PSNR, SSIM 등)에 미치는 영향을 분석함.
◯ 광범위한 장면 복원에 특화된 LongSplat과 기상 이미지를 복원할 수 있는 2D Refinement 모델을 결합하여 기상 악조건에서도 안정적인 3구조를 유지하는 복원 프로세스를 검증함.
◯ 기상 조건의 강도에 따른 PSNR, SSIM 등 정량적 지표 변화를 분석하여 기존 단일 모델 대비 결합 모델이 갖는 우위를 입증하고 최적의 파라미터를 도출함.
◯ 분석 기반, 최적화된 모델 개발 및 미세조정.

### 3) snow 환경에서의 3D Object Detection 모델 성능 분석
◯ Lidar 및 Camera 기반 혹은 둘을 모두 활용하는 멀티모달 기반의 3D Object Detection 모델에 증강된 데이터를 입력하여, 기상 악화 시 객체 탐지 정확도의 하락 폭을 측정함.
◯ 기상 악화 시 객체 경계의 모호함이 모델의 Bounding Box 예측 정확도와 신뢰도에 미치는 영향을 분석하여, 환경 변화에 민감한 센서의 취약점을 파악함.
◯ 분석 기반 취약점을 보완한 모델 최적화. 

## 기대효과
◯ 기상 악조건에서도 안정적으로 작동하는 AI 모델의 벤치마크 데이터를 확보하고, 향후 모델 고도화를 위한 가이드라인 제시.
◯ 자율주행 및 보안 관제 시스템의 기상 상황 대응 능력을 사전 검증함으로써 시스템의 안전성 상향 평준화에 기여.

---

## 1. 과제 목적 및 필요성
※ 과제 내용을 충분히 전달할 수 있도록 목적 및 필요성 기술  
(개략도, 모형도 등 첨부 가능)

### (1) 과제 목적
본 연구의 목표는 눈(Snow), 비(Rain), 안개(Fog), 야간(Night) 등 다양한 기상 악조건 환경에서 3D Vision 모델의 성능 저하 원인을 체계적으로 분석하고, 이를 기반으로 강건한 3D Vision 모델을 설계 및 개선하는 것이다.

구체적으로는 다음과 같은 목표를 가진다.
● 다양한 기상 조건에서의 3D Object Detection 및 3D Reconstruction 성능 변화 정량 분석  
● 기상 노이즈가 모델의 입력(이미지/포인트클라우드)에 미치는 영향 규명  
● 기존 모델의 취약점을 보완하는 robust learning 전략 및 모델 구조 개선  
● 실제 환경에 가까운 Weather Benchmark 및 평가 프로토콜 구축  

### (2) 과제 필요성
자율주행, 로보틱스, 디지털 트윈 등 실제 응용 환경에서는 맑은 날씨뿐 아니라 다양한 기상 악조건이 빈번하게 발생한다.  

그러나 대부분의 기존 3D Vision 모델은 상대적으로 깨끗한 환경에서 수집된 데이터셋을 중심으로 개발·평가되어, 눈, 비, 안개, 야간과 같은 환경 변화에 취약한 한계를 가진다.  

특히 기상 악조건은 카메라 영상의 시인성 저하, LiDAR 포인트 노이즈 증가, 객체 경계 및 구조 정보 손실 등을 유발하여, 3D Object Detection과 3D Reconstruction 성능을 크게 저하시킬 수 있다.  

따라서 실제 환경 적용 가능성을 높이기 위해서는, 악천후 환경에서의 성능 저하 원인을 정량적으로 분석하고 이를 개선할 수 있는 강건한 3D Vision 기술 확보가 필수적이다.

---

## 2. 과제 내용 및 추진 방법
※ 과제 분석 내용 작성 (구현할 기술, 기능 등)  
※ 추진을 위한 개발 환경, 툴, 장비, 재료 등의 활용 방안 및 절차 기술  

본 과제는 다양한 기상 악조건(야간, 우천, 강설 등) 환경에서의 3D Vision 모델 성능 저하를 분석하고, 이를 개선하기 위한 강건한 모델 및 실험 환경을 구축하는 것을 목표로 한다.  

연구는 크게 3D Object Detection(3DOD)와 Unposed 3DGS 두 축으로 구성되며, 각 세부 주제별로 데이터셋 구축, 베이스라인 선정, 성능 분석, 개선 기법 적용, 통합 Benchmark 정립의 절차로 수행한다.

### 논문1 - Knowledge Distillation을 활용한 야간(Night) 및 우천(Rain) 환경 강건 3DOD 모델 개발

#### (1) 데이터셋 구축 및 환경별 필터링
● 기존 공개 데이터셋인 nuScenes로부터 야간(night) 및 우천(rain) 환경에 해당하는 scene을 선별한다.  
● 각 scene의 metadata(description)에 포함된 키워드(예: night, rain, rainy 등)를 기준으로 조건별 subset을 구성한다.  
● 추출된 subset에 대해 주행 장면 특성, 클래스 분포, 센서 구성 등을 함께 분석하여 실험의 신뢰성을 확보한다.  

#### (2) 베이스라인 모델 선정 및 사전 성능 검증
● 야간 및 우천 환경에서의 강건성 평가에 적합한 멀티모달 3DOD 모델을 조사하고, 구현 가능성과 성능을 기준으로 베이스라인을 선정한다.  
● 선정 모델로는 MoME: Resilient Sensor Fusion via Multi-Modal Expert Fusion을 우선 검토하며, 필요 시 비교 대상 모델을 추가 구성한다.  
● nuScenes의 일반 환경과 night/rain subset 각각에 대해 클래스별 탐지 성능을 측정하여 baseline 성능 저하 양상을 분석한다.  

#### (3) 성능 저하 원인 분석 및 개선 기법 적용
● 야간 및 우천 환경에서 발생하는 조도 저하, 반사, 시야 저하, 센서 노이즈 등이 멀티모달 fusion 성능에 미치는 영향을 분석한다.  
● 성능 개선을 위해 다음과 같은 방법을 적용할 수 있다.  
- Knowledge Distillation (KD) 기반 teacher-student 학습  
- Weather-aware Data Augmentation  
- Noise-robust Feature Extraction  
- Multi-modal Fusion 구조 개선 (LiDAR + Camera)  
개선 기법은 단독 또는 복합적으로 적용하여 성능 향상 여부를 검증한다.  

#### (4) 성능 검증 및 비교 실험
● 개선 모델과 baseline 모델 간 성능을 비교하고, 조건별(class / weather / sensor modality) 성능 차이를 정량적으로 분석한다.  
● 주요 평가 지표는 mAP, NDS, class-wise AP 등을 활용한다.  
● 추가적으로 failure case 분석을 수행하여 실제 악조건 환경에서의 취약 패턴을 정리한다.  

### 논문2 – 눈(snow) 환경에서의 3D Object Detection(3DOD) 모델 성능 분석

#### (1) Snow 환경 데이터셋 구축
● snow simulation 모델을 활용하여 nuScenes-mini 및 KITTI 데이터셋에 강설 환경을 합성한다.  
● 강설 강도는 severity 1, 3, 5 등 다양한 수준으로 설정하여 환경 난이도를 단계적으로 구성한다.  
● 이미지 및 LiDAR 입력 모두에 대해 눈 입자, 시야 저하, 반사 왜곡 등의 효과를 반영한 실험 데이터를 생성한다.  

#### (2) 다양한 3DOD 베이스라인 모델 성능 측정
● Snow 환경에서의 성능 분석을 위해 여러 LiDAR 기반 3DOD 모델을 선정한다.  
● 사용 예정 모델은 다음과 같다.  
- PointPillars  
- PointRCNN  
- Voxel R-CNN  
- MVMM  
● 각 모델의 point representation 방식(point / pillar / voxel / fusion)에 따라 강설 노이즈에 대한 민감도 차이를 비교 분석한다.  

#### (3) 성능 저하 분석 및 비교
● Snow severity 수준별로 성능 변화를 측정하여, 기상 악조건 강도에 따른 탐지 성능 저하 패턴을 분석한다.  
● 주요 평가 지표는 mAP (mean Average Precision)를 중심으로 하며, 필요 시 class-wise AP, Recall, Precision 등을 함께 활용한다.  
● 특히 Car, Pedestrian, Cyclist와 같이 클래스별 크기와 형태가 다른 객체에 대해 성능 변화 양상을 세부적으로 분석한다.  

#### (4) 실험 결과 해석
● 각 모델의 구조적 특성에 따라 snow noise에 강건하거나 취약한 원인을 분석한다.  
● 이를 통해 악천후 환경에서 효과적인 3DOD representation 및 구조 설계 방향을 도출한다.  

### 논문3 - weather artifact 존재하는 2D input에 대한 unposed 3d reconstruction 모델의 성능 분석 및 개선

#### (1) 베이스라인 모델 조사 및 선정
● 다양한 Gaussian Splatting(GS) 기반 3D reconstruction 모델을 조사하고, 날씨 조건에서의 적용 가능성을 검토한다.  
● 특히 WeatherGS와 같이 날씨 환경을 고려한 관련 모델을 참고하여 비교 기준을 수립한다.  
● 카메라 포즈 추정까지 한번에 수행하는 Unposed 3DGS 모델을 찾는다.  
● 현재 LongSplat을 baseline 모델로 선정 고려 중  

#### (2) Weather 환경에서의 성능 측정
● Weather artifact가 포함된 2D input에 대해 LongSplat의 reconstruction 성능을 측정한다.  
● 주요 평가 지표는 다음과 같다. PSNR, SSIM, LPIPS, AUC  
● 이를 통해 기상 노이즈가 geometry 복원 정확도 및 texture/appearance 품질에 미치는 영향을 정량적으로 분석한다.  

#### (3) 2D Refinement 기반 성능 개선
● LongSplat의 성능 저하를 완화하기 위해, 입력 이미지 품질을 개선하는 2D Refinement / Image Restoration 모델을 조사 및 선정한다.  
● 적용 가능한 기법 예시는 다음과 같다.  
- Rain removal / deraining  
- Snow removal / desnowing  
- Low-light enhancement  
- General weather artifact suppression  

● 전처리된 입력을 활용하여 reconstruction 성능이 얼마나 회복되는지 검증한다.  

#### (4) 개선 모델 성능 비교 실험
● 원본 입력과 refinement 적용 입력 간 reconstruction 결과를 비교한다.  
● 단순 렌더링 품질뿐 아니라, scene consistency / view synthesis 품질 / geometry 안정성 측면에서의 개선 효과를 함께 분석한다.  

---

### 평가 및 Benchmark 구축

#### (1) 통합 실험 환경 구축
● 다양한 weather 조건을 포함하는 3D Vision 통합 실험 환경을 구축한다.  
● 3DOD와 3D Reconstruction task를 동일한 weather 조건 하에서 평가할 수 있도록 데이터셋 및 실험 파이프라인을 정리한다.  

#### (2) 평가 기준 정립
● task별 핵심 성능 지표를 정리하고, 환경 조건별 비교가 가능하도록 표준화된 평가 프로토콜을 설계한다.  

#### (3) 재현 가능한 실험 프로토콜 정리
● 실험 설정, 데이터 전처리, 학습 파라미터, 평가 스크립트 등을 문서화하여 재현 가능한 연구 환경을 구축한다.  
● 각 실험 결과를 체계적으로 기록하고, 향후 확장 가능한 형태로 코드와 설정 파일을 정리한다.  

#### (4) 공개 가능한 Benchmark 형태로 정리
● 최종적으로 weather 환경에서의 3D Vision 성능 평가를 위한 benchmark 형태의 결과물을 정리한다.  
● 이를 통해 향후 악천후 환경 강건성 연구를 위한 기준선(baseline) 및 비교 체계를 제공한다.  

---

### 결과 시각화 웹페이지 구축
● 논문 및 실험 결과를 직관적으로 확인할 수 있도록 결과 시각화 웹페이지를 구축한다.  
● weather 조건별 성능 비교, 정량 지표, 대표 qualitative result 등을 웹 기반으로 정리한다.  

---

### 소프트웨어 등록
● 본 과제에서 개발한 실험 코드, 평가 파이프라인, 결과 시각화 시스템을 정리하여 소프트웨어 등록을 추진한다.  
● 재현 가능한 연구 결과물로서 코드 및 시스템 자산화를 목표로 한다.  

---

## 추진을 위한 개발 환경, 도구 및 활용 방안

### (1) 개발 환경
운영체제: Ubuntu Linux  
개발 언어: Python  
3DOD 프레임워크: MMDetection3D, OpenPCDet 등으로부터 사용  
3D Reconstruction 프레임워크: Gaussian Splatting 계열 공개 구현체, LongSplat 관련 코드베이스  
협업 및 형상 관리: GitHub, Notion, Slack, Zoom, Discord, Kakaotalk, googledrive 등  
문서화 및 결과 정리: Excel, Notion, Google Drive, Word  

### (2) 활용 장비 및 자원
GPU RTX 3080 서버를 활용한 학습 및 추론 실험 수행  
고용량 데이터셋 저장 및 실험 로그 관리를 위한 외장 스토리지 활용  

---

## 3. 과제 추진 일정 및 예산 활용 계획
관련 논문 및 베이스라인 조사  
데이터셋 구축 및 전처리  
Baseline 재현 및 성능 검증  
악천후 환경별 성능 분석  
개선 기법 설계 및 구현  
비교 실험 및 정량/정성 평가  
논문 작성용 결과 정리 (대표 그림, 성능 표, 핵심 메시지 도출)  
1차 논문 초안 작성 (초록, 서론, Related Work, Method 개요)  
실험 결과 및 분석 파트 작성  
논문 전체 초안 완성 및 수정  
Benchmark 정리 및 최종 결과 문서화  
논문 결과 기반 시각화 웹페이지 구축  
실험 코드 및 결과 시스템 소프트웨어 등록 추진  

---

## 4. 기대효과 및 활용방안

기대효과  
악천후 환경에서의 3D Vision 모델 성능 저하 원인에 대한 체계적 분석  
자율주행·로보틱스 환경에 적합한 강건한 3D Object Detection / 3D Reconstruction 기술 확보  
실제 환경에 가까운 weather benchmark 기반 실험 결과 및 평가 기준 도출  
향후 후속 연구 및 산업 적용이 가능한 재현성 높은 실험 자산 구축  
악천후 환경에 대한 센서 활용 및 강건 학습 전략 설계 방향 제시  
기상 조건별 성능 차이를 분석한 실증적 연구 결과 확보  
프로젝트 수행 과정에서 3D Vision, 딥러닝, 데이터 전처리, 실험 설계 및 논문화 역량 향상 기대  

활용방안  
자율주행, 로보틱스, 디지털 트윈 등 실환경 기반 3D Vision 응용 분야 연구에 활용  
악천후 환경을 고려한 3DOD 및 3D Reconstruction 후속 연구의 baseline 및 benchmark로 활용  
실험 코드, 전처리 파이프라인, 평가 체계를 정리하여 재현 가능한 연구 자산으로 활용  
논문 및 실험 결과를 기반으로 한 성과 시각화 웹페이지 구축을 통해 연구 결과 확산  
개발한 코드 및 시스템 자산을 기반으로 소프트웨어 등록 및 기술 자산화 추진  

---

## 5. 예상되는 주요 과제성과 
● 방송미디어공학회 2026 하계학술대회 (추후 변경 가능성O) 대학생 논문 및 캡스톤디자인 경진대회 - 논문 3편(주저자: 이윤호, 최경진, 이상욱/ 공저자: 배채은, 김규도, 이동훈, 송호준) 제출 예정  
● SW 등록 1-2건 예정  
