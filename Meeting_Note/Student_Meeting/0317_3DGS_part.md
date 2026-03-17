> 참여자: 학부생 이윤호/김규도, 대학원생 송호준

# 실험 방향

- 연구 주제 : Weather Artifact가 존재하는 2D input에 대한 Unposed 3D Recon 모델의 성능 저하 측정 및 개선
- Baseline Model : LongSplat (Unposed 3DGS)
- Dataset : WeatherGS 논문이 제공하는 데이터셋 + Free Dataset (w/ Weather synthesis)
- Method : 딥러닝(딥퓨전)기반 Image Refinement가 가능한 모델 사용하여 LongSplat의 Input단에서 Weather Artifact 제거
- Metric : Rendered image에 대한 PSNR + LongSplat이 추정한 Camera Pose 정확도

# 논문 작성 관련

- Related Work 조사 : 코드 유무 체크, 탑 컨퍼런스 위주 논문으로 체크
- 논문의 대략적인 Novelty 설득 방향
  - NVS 렌더링의 중요성 -> NeRF/3DGS 소개 -> Unposed 3DGS 등장
  - Unposed GS + Weather 관련 연구 없음
  - 따라서 우리 연구가 필요함
- 주저자가 대부분 파트를 작성하되 공저자가 일부 파트를 지원
- Introduction, Method, Experiment 파트는 주저자가 작성

# 기타 사항

- KCC에 제출하는 것도 고려해보기
- Docker 사용시에 GPU Architecture에 따른 Ark number 체크해보기

# 할 일

- 논문작성 계획 수립 및 파트 분배
- Related Work 조사
- Image Refinement 모델 조사
- Colab에서 LongSplat Test
- Free Dataset에 WeatherGS가 사용한 날씨 합성 모델 사용 Test
