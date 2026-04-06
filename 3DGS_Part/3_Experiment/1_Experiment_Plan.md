# 3DGS Experiment Plan

(보류)

> Weather Artifact가 있는 2D Multi-view Video에 2D Refinement 적용해
> Unposed 3DGS의 3D Reconstruction 성능 저하 개선

## 1. 개요
- **Baseline Model**: LongSplat (Unposed 3DGS)
- **2D Refinement 후보**: MWFormer (1순위) / UtilityIR (ablation)
- **Weather Synthesis 도구**: WeatherEdit
- **핵심 아이디어**: LongSplat Input단에서 Weather Artifact 제거 후 3D Reconstruction 수행

## 2. 데이터셋
### (1) WeatherGS Dataset
- Synthetic: Deblur-NeRF 기반 scene을 Blender로 재편집
- 3개 scene (Tanabata, Factory, Pool) × snowy + rainy = 6가지 조건
- 파티클 시스템으로 snowflake/raindrop 물리 시뮬레이션 + motion blur 적용
- Real-world: YouTube 영상에서 keyframe 추출 (snowy/rainy)
- GT: 맑은 날씨 동일 scene의 렌더링 결과
### (2) Free Dataset (자체 구성)
- F2-NeRF의 Free Dataset을 기반으로 활용 (7개 scene, free trajectory)
- WeatherEdit으로 weather synthesis 적용
- weather type: snow / rain / fog
- severity: light / moderate / heavy
- TV-Attention으로 multi-view, multi-frame 일관성 보장

## 3. 실험 전체 파이프라인
[Free Dataset / WeatherGS Dataset]
↓
[Weather Synthesis] WeatherEdit
(multi-view 일관성 보장, severity 조절 가능)
↓
Multi-view Frames (w/ Weather Artifact)
↓
[2D Refinement] MWFormer (or UtilityIR)
↓
Un-weathered Multi-view Frames
↓
[Unposed 3DGS] LongSplat
↓
3D Reconstruction + Camera Pose Estimation
### (1) 실험 변수
- Weather Type: Snow / Rain
- Weather Severity: Light / Moderate / Heavy
### (2) 실험 우선순위
- 1순위: Snow + MWFormer
- 2순위: Rain + MWFormer
- 3순위: 동일 조건 + UtilityIR

## 4. Evaluation Metric

-  **Raw Input**: weather 없는 원본으로 LongSplat 실행 → upper bound
- **Weathered Input**: artifact 있는 영상으로 LongSplat 실행 → baseline
- **Un-weathered Input**: 2D Refinement 적용 후 LongSplat 실행 → ours
### (1) PSNR (렌더링 결과 기준)
- 3가지 조건의 LongSplat 렌더링 결과를 GT(Raw)를 기준으로 계산
- 목표: Un-weathered의 PSNR이 Weathered 대비 유의미하게 향상되고 Raw에 근접시키는 것
### (2) Camera Pose 정확도
- LongSplat이 추정한 Camera Pose를 GT Pose와 비교
- ATE (Absolute Trajectory Error) / RTE (Relative Translation Error)
- 동일하게 Raw / Weathered / Un-weathered 3가지 조건에서 비교