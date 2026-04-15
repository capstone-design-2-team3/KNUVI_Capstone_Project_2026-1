# 📊 실험 진행 로그 (Experiment Log)

## 🛠 Weathered Free dataset 구축 완료 - [2026-04-11]
**연구 주제**: 비정형 긴 궤적(Casual Long Videos) 환경에서의 악천후 3D 복원 (Free Dataset)

### 1. 구축 전략 (Data Preparation Strategy)
- **대상**: F2-NeRF `Free Dataset` 7개 씬 (비정형 궤적)
- **악천후 합성**: `WeatherEdit`을 활용한 비(Rain) 및 눈(Snow) 레이어 합성 데이터.
- **데이터 정제 단계**:
  1. **중복 데이터 제거**: 정렬된 목록 기준 매 3번째 이미지(00158, 00161, ...)를 삭제하여 1차 정제.
  2. **개수 최적화 (Max 200장)**: 3DGS 최적화 효율 및 일관된 비교를 위해, 200장이 넘는 씬은 균등하게(Evenly spaced) 샘플링하여 정확히 **200장**으로 제한.
- **결과**: 전체 카메라 궤적의 커버리지는 유지하면서 연산 부하를 줄인 최적의 실험 데이터셋 확보.

### 2. 최종 데이터셋 현황 (Final Inventory)
| Scene Group | Rain (Images) | Snow (Images) | Status |
| :--- | :---: | :---: | :--- |
| **Grass** | 197 | 197 | ✅ Ready |
| **Hydrant** | 141 | 141 | ✅ Ready |
| **Pillar** | 200 | 200 | ✅ Ready |
| **Road** | 200 | 200 | ✅ Ready |
| **Sky** | 200 | 200 | ✅ Ready |
| **Stair** | 200 | 200 | ✅ Ready |

### 3. 산출물 (Artifacts)
- 각 디렉토리 내 정제된 이미지 파일 (`00xxx.png`)
- 각 디렉토리별 최종 선택된 이미지 번호 기록 (`{Scene}_indices.txt`)

---
## 🚀 모델 학습 진행 (Training Progress)
**모델**: `LongSplat` (Unposed 3DGS baseline)
**데이터셋**: Weathered Free Dataset (Rain/Snow)

### 학습 개요
- **목표**: 악천후 입자가 포함된 상태에서 포즈와 형상을 동시에 최적화했을 때의 렌더링 품질 및 포즈 정확도 분석 (Case B2).
- **진행 중인 씬**: `grass_rain`, `stair_snow` 등 (전체 6개 씬 순차적 진행 예정)
- **설정**:
  - 입력 이미지: Reindexed 00001.png ~ (최대 200장)
  - 파라미터: LongSplat 기본 설정 (Unposed mode)

---
**다음 단계**: 각 데이터셋에 대해 `Posed 3DGS (COLMAP)` 및 `Unposed 3DGS (LongSplat)` 베이스라인 측정 및 `MWFormer` 전처리 성능 비교.


## Evaluation Issue
Posed 3DGS와 Unposed(LongSplat)의 reconstruction 성능을 PSNR로 비교해야 하는데, 두 모델의 출력 이미지가 서로 다른 좌표계에 있음

- **Posed 3DGS**: COLMAP undistortion 과정을 거친 이미지로 학습 → output이 undistorted 좌표계
- **Unposed LongSplat**: raw 이미지 그대로 학습 → output이 raw 좌표계
- **GT(clean 이미지)**: raw 좌표계

따라서 해상도도 다르고, 왜곡 보정 여부도 달라서 세 이미지가 픽셀 단위로 대응되지 않음.

**해결 방안**
1. Raw GT로 통일
- Posed output → `cv2.remap`으로 역변환 → raw 좌표계 복원
- Unposed output → resize
- GT → clean raw 이미지 resize
- 단점: 역변환 구현 번거로움, 역변환 시 품질 손실 가능

2. Undistorted GT로 통일
- Posed output → 바로 PSNR
- Unposed output → resize + `cv2.undistort` 적용
- GT → clean undistorted 이미지
- 단점: Unposed output에 왜곡 보정 적용이 부자연스러움

3. COLMAP undistortion 과정을 거치지 않고 학습
- 간단하지만 3DGS가 왜곡된 이미지로 학습하게 되어 reconstruction 성능 저하 가능성

4. Raw, Posed output, Unposed output 모두 resize만 진행 (결정)
- 간단하지만 어느 쪽을 잘라야 하는지 애매하고, Posed output의 경우 왜곡 보정으로 인한 불공정한 PSNR 수치 감소 우려
-> 왜곡 보정으로 인한 품질 변화는 미미한 수준으로 관찰됨. 따라서 4번 resize만 진행하는 것으로 함

## 2D Refinement Issue
- MWFormer 사용하여 grass, hydrant 두 씬에 deraining / desnowing 진행
- -> De-snowing은 좋은 output을 얻을 수 있었으나 De-raining 성능이 좋지 않음

**해결 방안**
1. 다른 모델을 도입하여 De-raining 또는 rain/snow 둘 모두 다시 refine 진행
  - 예비 후보 (1) https://github.com/Ephemeral182/ECCV24_T3-DiffWeather?tab=readme-ov-file (ECCV'24)
  - 예비 후보 (2) https://github.com/IGITUGraz/WeatherDiffusion (TPAMI'23)
2. 기존은 snow+rain이었으나, 시간을 고려하여 “Snow artifact”만 집중하는 것으로 타겟 변경

## 전체 파이프라인 수정 및 정리 (0415)
주제: 눈 환경에서의 Posed vs. Unposed 3DGS의 날씨 민감도 및 2D 전처리 결합 효과 비교 분석
1. Free Dataset의 7개 Scene 중 실내인 Lab을 제외한 6개 씬을 사용
2. Snow artifact가 적용된 Weathered Dataset 생성 : WeatherEdit을 사용하여 Free Dataset 각 씬에 대해 snow 합성 (1차: Heavy, 2차: Light)
3. Original/Weathered Dataset 전처리 진행 : 1024*656 해상도로 downsampling
4. MWFormer를 사용하여 Weathered의 각 씬에 대해 snow 제거
5. Posed 3DGS (COLMAP + 3DGS)와 Unposed 3DGS (LongSplat) 각각에 대해 3D Reconstruction 진행 (Original, snow, de-snow)
6. 모든 Rendering output과 Original image 1000*640 해상도로 centered crop
7. PSNR, SSIM, LPIPS, ATE, RTE, RPE 계산
