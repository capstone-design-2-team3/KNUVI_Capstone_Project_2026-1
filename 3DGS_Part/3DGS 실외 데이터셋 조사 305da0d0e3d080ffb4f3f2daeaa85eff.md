# 3DGS 실외 데이터셋 조사

상태: 완료
담당자: 규도 김
마감일: 2025/02/20
진행도: 100

# 1. 날씨 데이터가 포함된 GS 데이터셋

## References

1. WeatherGS: 3D Scene Reconstruction in Adverse Weather Conditions via Gaussian Splatting
2. **DeRainGS: Gaussian Splatting for Enhanced Scene Reconstruction in Rainy Environments**
3. **Rethinking Rainy 3D Scene Reconstruction via Perspective Transforming and Brightness Tuning**
4. ScatterNeRF: Seeing Through Fog with Physically-Based Inverse Neural Rendering
5. 3D Gaussian Splatting for Real-Time Radiance Field Rendering

## Dataset

| Dataset Name | Weather | scene | image | Year | GT Availability |
| --- | --- | --- | --- | --- | --- |
|  1. WeatherGS | rain/snow | 6 | 0.3k | 2024 | **O** |
| 2. DeRainGS (HydroViews) | rain streaks/rain drops | 20 | 7k | 2024 | **X** |
| 3. REVR-GSNet (OmniRain3D) | rain/brightness dynamicity | 10 | 7k | 2025 | **O** |
| 4. ScatterNeRF | fog | 3 | 0.4k | 2023 | **X** |

# 2. 날씨 미포함 실외 데이터셋

| Dataset | scene |
| --- | --- |
| TnT | 21 |
| DL3DV | 10k |
| LLFF | 8 |
| Free dataset | 7 |
| Hike dataset | 12 |