# 실험 진행 체크리스트

## 1) 공통 환경 세팅
- [] Posed 3DGS 및 COLMAP 환경 세팅.
- [] Unposed 3DGS(LongSplat) 환경 세팅.
- [] MWFormer inference 환경 세팅.

## 2) 데이터 준비
### 2-1. Free Dataset
- [x] Free Dataset Weathered (WeatherEdit 합성본) 폴더 정리.
- [] Free Dataset Un-weathered (MWFormer 결과) 폴더 정리.
- [] Weathered / Un-weathered 씬/프레임 개수 일치 여부 확인.  

### 2-2. WeatherGS Dataset (보류)
- [] WeatherGS Weathered 정리.  
- [] WeatherGS Un-weathered 정리.  
- [] 씬별 meta 정보(해상도, 프레임 수) 정리.  

## 3) 2D 전처리 단계
- [] WeatherEdit로 Free Dataset에 눈/비 + severity(약 3단계) 세팅 후 Weathered 생성.
- [] MWFormer로 Weathered → Un-weathered inference 실행. (주저자)
- [] 전/후 프레임 샘플 시각 점검 (색감, 잔여 노이즈, 경계 깨짐).  
- [] Multi-view inconsistency 의심되는 샘플 따로 리스트업.

## 4) Posed 3DGS (Case A2, A3)
### 4-1. A2: Weathered + Posed
- [] COLMAP에 Free Dataset Weathered 입력, 포즈 추정 실행.
- [] Feature match 실패/트래킹 로스트가 발생한 씬 기록.
- [] COLMAP 포즈 결과를 이용해 3DGS train 실행.  
- [] 평가 렌더링 생성 (Free / WeatherGS 공통 포즈 기준).  
- [] PSNR / SSIM / LPIPS / ATE / RTE 계산.
- [] “날씨로 인한 SfM 붕괴 패턴” 메모.

### 4-2. A3: Un-weathered + Posed
- [] Free Dataset Un-weathered로 COLMAP 포즈 추정 재실행.
- [] A2 대비 포즈 품질(ATE/RTE) 얼마나 회복되는지 계산.
- [] 같은 포즈로 3DGS train 실행.  
- [] 평가 렌더링 생성 및 저장.
- [] PSNR / SSIM / LPIPS, A2 대비 성능 개선량 정리.
- [] 시점 불일치가 남아서 생긴 아티팩트 사례 캡처.

## 5) Unposed 3DGS (Case B2, B3)
### 5-1. B2: Weathered + Unposed
- [] LongSplat에 Free Dataset Weathered 입력 후 train.
- [] 날씨 입자(눈/비/안개)가 3D 가우시안으로 어떻게 복원되는지 샘플 확인.
- [] 렌더링 결과 저장.  
- [] PSNR / SSIM / LPIPS 계산.
- [] “악천후 → 기하학 오염 패턴” 메모.

### 5-2. B3: Un-weathered + Unposed
- [] LongSplat에 Free Dataset Un-weathered 입력 후 train.
- [] B2 대비 품질 상승 여부 시각적으로 확인.
- [] PSNR / SSIM / LPIPS 계산, B2와 차이 정리.
- [] 시점 불일치가 있는 입력을 LongSplat이 어느 정도 보정하는지 관찰 메모.

## 6) WeatherGS Dataset에 동일 파이프라인 적용
- [] WeatherGS Weathered로 A2, B2 절차 축약 실행.
- [] WeatherGS Un-weathered로 A3, B3 절차 축약 실행.
- [] Free Dataset 결과와 경향一致/불일치 포인트 메모.  

## 7) 결과 취합 및 분석
- [] 씬 × 케이스(A2, A3, B2, B3)별 metric csv 정리.
- [] A2 vs B2: 악천후에 대한 취약성 비교 그래프/표 생성.
- [] A2 vs A3, B2 vs B3: 전처리 도입 효과 시각화.
- [] A3 vs B3: 시점 불일치 수용 능력 비교 그래프/코멘트 작성.
- [] 대표 성공/실패 렌더링 이미지 모아서 figure 후보 폴더 구성.  
- [] 실험 로그, 하이퍼파라미터, 버전 정보 정리.  
