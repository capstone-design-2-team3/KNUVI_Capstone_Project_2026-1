dl_object_upsampler.py  
extract_masks.py  
filter_points.py  
frustum_dbscan_augment.py  
train_upsampler.py  
  
hybrid_augment.py  
: 2d bbox에 투영되는 모든 3d point를 잘라내서 객체에 해당하는 포인트를 DBSCAN 방법론을 적용하여 가장 덩어리가 큰 군집만 골라냄.  
그 군집에 gaussian noise를 적용하여 뼈대 주변의 포인트 증강 + 이미지 가이드 기반 depth completion 적용  
→ 라이다 점을 이미지 위로 projection, 이미지의 RGB 정보를 가이드로 삼아 구멍 뚫린 부분의 픽셀을 채워넣음. 다시 unprojection
  
spconv_denoiser.py  
: 3D Sparse Convolution 사용하여 포인트 클라우드 디노이징을 수행함.  
  
object_aware.py  
- 보행자 : 이미 탐지에 영향을 덜 미침. 따라서 노이즈만 제거하는 방식 적용  
- 자전거 : 형태 대칭성을 활용해서 자전거 중심을 기준으로 기존 포인트를 좌우 대칭으로 복사함  
- 자동차 : CNN 생성 포인트에 대한 KD-Tree 필터링을 적용하여 표면의 구멍을 메움  
