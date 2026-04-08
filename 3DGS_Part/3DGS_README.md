# 3DGS 실외 악천후 환경 복원 연구 (Capstone Project 2026-1)

본 디렉토리는 2026년 하계 학술대회(방미공) 제출을 목표로 하는 **"카메라 포즈 정보가 없는 악천후 환경(Unposed 3DGS)을 위한 2D 전처리 기반 3DGS 파이프라인"** 연구를 위한 종합 작업 공간입니다.

## 📌 연구 요약 (Project Overview)
- **주제**: 비정형 긴 궤적(Casual Long Videos) 환경에서의 악천후 3D 복원 연구
- **문제점**: 실외 악조건(눈, 비 등)에서는 기존 3DGS 파이프라인의 특징점 매칭 및 카메라 포즈 추정(SfM, COLMAP 등)이 실패하여 3D 재구성 자체가 붕괴됨. 기존 악천후 3DGS 연구는 이미 포즈가 추출된 환경(Known Poses)만을 가정하는 한계가 있음.
- **해결 방안**: 포즈 정보가 주어지지 않는 **Unposed 3DGS(LongSplat)** 환경에서, 3D 파이프라인 진입 전 **날씨 열화 인지형 트랜스포머(MWFormer)**를 활용한 2D 이미지 복원 전처리(Pre-processing)를 선제적으로 진행.
- **기대 효과**: 포즈 추정의 붕괴 방지 및 시점 불일치(Multi-view Inconsistency) 등 전처리 한계를 모델 최적화(Joint Optimization)로 극복함으로써, 결과적으로 카메라 포즈 정확도(ATE/RTE) 및 3D 렌더링 품질(PSNR) 대폭 개선.

## 📂 디렉토리 구조 (Directory Structure)

### 1. `1_Model_test/`
모델 구동 테스트 및 관련 기술 조사가 포함되어 있습니다.
- **LongSplat / WeatherGS**: Unposed 3DGS 베이스라인 모델 및 기존 악천후 3DGS 기술 테스트, 로그 정리 (`LongSplat Setting.md`, `WeatherGS_test.ipynb` 등).
- **2D Refinement**: MWFormer 등 딥퓨전 기반의 2D 이미지 단일/복합 악천후 제거 트랜스포머 모델 탐색 요약 (`2D_Refinement_Model_Research.md`).

### 2. `2_Related_Work/`
연구 배경 조사를 위한 관련 논문 및 리포트들이 정리되어 있습니다.
- **조사 내용**: 3DGS 기반 실외 데이터셋 조사 내역, NVS/NeRF 발전 동향, Posed/Unposed 3DGS의 최신 동향 및 모델 조사 보고서.

### 3. `3_Experiment/`
구체적인 실험 계획 수립 및 벤치마킹 진행 로그가 기록되어 있습니다.
- **`1_Experiment_Plan.md`**: 데이터셋 변인(Raw, Weathered, Un-weathered) 및 파이프라인 대조군(Case A: Posed 3DGS vs Case B: Unposed 3DGS) 기반의 양방향 실험 설계. 평가 지표(PSNR, LPIPS, ATE 등)와 가설 검증 방법론 상세 기재.
- **`2_Experiment_Log.md`**: 실험 진행 상황 및 결과 수치 추적 기록장.

### 4. `4_Paper_Writing/`
논문 투고를 위한 초안(Draft) 및 시각 자료(Figure) 작업 공간입니다.
- **`0_3DGS_Draft.md`**: 논문 초록(Abstract) 및 서론(Introduction) 등 본문 작성 중인 문서.
- **`3DGS_Main_Figure.pptx`**: 논문 핵심 다이어그램 및 제안 방법 파이프라인 구성도.

---

## 🚀 실험 계획 요약 (Experiment Design)
본 프로젝트는 다음 3가지 데이터 조건을 2가지 방식에 각각 주입해 상호 비교합니다.

1. **테스트 데이터 (Variables)**
   - `Raw` (맑은 원본 영상: Upper Bound 확인용)
   - `Weathered` (악천후 합성 영상: 붕괴 기준선 확인용)
   - `Un-weathered` (2D 전처리 제거 후 영상: 제안 방식 및 한계 극복 확인용)

2. **비교 파이프라인 (Methods)**
   - `Case A`: 전통적 SfM 궤적 기반 `Posed 3DGS (COLMAP)`
   - `Case B`: 궤적 및 형상 결합 최적화 기반 `Unposed 3DGS (LongSplat)`

3. **주요 평가지표 (Metrics)**
   - 렌더링 시각 품질: `PSNR`, `SSIM`, `LPIPS`
   - 카메라 궤적 오류 측정: `ATE` (절대 오차), `RTE` (상대 이동 오차)