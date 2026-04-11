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
## 🚀 모델 학습 진행 (Training Progress) - [2026-04-12]
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
