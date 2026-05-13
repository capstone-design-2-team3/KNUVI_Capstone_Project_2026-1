# nuScenes로 MoME 모델 평가

* 

### 진행한 세부 업무

* \[x]  할당받은 DL2 서버 원격 접속 (터미널, vscode 모두)
* \[x]  환경 설정
* \[x]  nuScenes 데이터셋 다운로드
* \[x]  nuScenes 데이터셋 전처리
* \[x]  MoME weight 다운로드
* \[x]  데이터셋에서 night/rain 씬 필터링
* \[x]  MoME 평가
* \[x]  지표 시각화 및 정리

\---

### 결과

* 표

  * 데이터 조건별 성능 지표



|Metric|Full Validation set|Night|Rain|
|-|-|-|-|
|mAP|71.2|42.78|71.98|
|mATE|0.2874|0.4885|0.2801|
|mASE|0.2536|0.4527|0.2675|
|mAOE|0.3500|0.4086|0.2577|
|mAVE|0.2560|0.5496|0.1941|
|mAAE|0.1916|0.5859|0.1430|
|NDS|73.6|46.53|74.56|

    * night, rain 조건에 맞춰 필터링한 nuScenes validation  사용
    * Night 조건에서 mAP가 급격히 낮은 이유는 아래 클래스별 지표와 함께 설명
    * Full validation set 수치는 실험을 직접 진행하지 않고 MoME 논문 Table 1 수치를 인용. 따라서 Rain mAP(71.98)가 Full val mAP(71.2)보다 높게 나온 것은 실험 환경 차이에 의한 것으로 추정
  * night 조건에서 class별 성능



|Class|AP (↑)|ATE (↓)|ASE (↓)|AOE (↓)|AVE (↓)|AAE (↓)|
|-|-|-|-|-|-|-|
|Car|0.898|0.169|0.119|0.034|0.399|0.459|
|Truck|0.836|0.186|0.109|0.019|0.370|0.656|
|Motorcycle|0.833|0.168|0.248|0.159|0.409|0.468|
|Pedestrian|0.709|0.094|0.263|0.289|0.115|0.102|
|Barrier|0.604|0.250|0.188|0.046|-|-|
|Bicycle|0.397|0.169|0.281|0.131|0.104|0.002|
|Traffic Cone|0.001|0.849|0.319|-|-|-|
|Bus|0.000|1.000|1.000|1.000|1.000|1.000|
|Trailer|0.000|1.000|1.000|1.000|1.000|1.000|
|Construction|||||||
| Vehicle|0.000|1.000|1.000|1.000|1.000|1.000|

    * Bus, Trailer, Construction Vehicle의 AP가 0.000으로 기록됨. night 특성상 해당 클래스가 등장하는 scene이 validation subset 내에 존재하지 않아 평가 자체가 이루어지지 않은 것으로 추정
    * mAP는 10개 클래스 AP의 단순 평균이기에, AP가 0인 4개 클래스(Bus, Trailer, Construction Vehicle, Traffic Cone)가 전체 mAP를 크게 떨어트린 것으로 추정. 해당 4개 클래스를 제외한 나머지 6개 클래스의 평균 AP는 0.712로, Rain 조건과 유사함.
    * 4개의 클래스를 제외한 AP는 0.712
  * rain 조건에서 class별 성능



|Class|AP (↑)|ATE (↓)|ASE (↓)|AOE (↓)|AVE (↓)|AAE (↓)|
|-|-|-|-|-|-|-|
|Car|0.905|0.167|0.144|0.044|0.221|0.139|
|Truck|0.847|0.154|0.315|0.262|0.217|0.062|
|Motorcycle|0.829|0.148|0.267|0.574|0.280|0.004|
|Pedestrian|0.825|0.333|0.187|0.029|0.285|0.628|
|Barrier|0.823|0.215|0.300|0.028|-|-|
|Bicycle|0.770|0.144|0.316|-|-|-|
|Traffic Cone|0.671|0.381|0.189|0.043|0.154|0.098|
|Bus|0.634|0.151|0.337|0.173|0.133|0.006|
|Trailer|0.550|0.539|0.221|0.586|0.177|0.084|
|Construction|||||||
| Vehicle|0.344|0.569|0.398|0.581|0.086|0.124|

    * Night 조건과 달리 10개 클래스 모두 AP가 측정됨.
    * Motorcycle의 AOE(0.574)가 유독 높음. 오토바이는 객체 크기가 비교적 작고, 전후 방향 구분이 어려워 높은 것으로 추정

    ⇒ 전반적으로 rain 조건에서는 Full validation 대비 성능 저하가 크지 않아, MoME가  rain에 대한 robustness를 어느 정도 갖추고 있음을 확인. 반면 night 조건에서의 성능 저하가 뚜렷하여, night에 대한 성능 개선이 필요함을 확인.



* 시각화 (ground truth와 prediction 비교)

  * 데이터 조건별

    * night

      !\[night\_compare\_1.jpg](night\_compare\_1.jpg)

      !\[night\_compare\_2.jpg](night\_compare\_2.jpg)

    * rain

      !\[rain\_compare\_2.jpg](rain\_compare\_2.jpg)

      !\[rain\_compare\_3.jpg](rain\_compare\_3.jpg)

  * 클래스별

    * night

      !\[car class](car\_compare\_1.jpg)

      car class

      !\[pedestrian class](pedestrian\_compare\_1.jpg)

      pedestrian class

      !\[bicycle class](bicycle\_compare\_1.jpg)

      bicycle class

    * rain

      !\[pedestrian class](pedestrian\_compare\_1%201.jpg)

      pedestrian class

      !\[car class](car\_compare\_1%201.jpg)

      car class

      !\[bicycle class](bicycle\_compare\_2.jpg)

      bicycle class



* 수치

  * night evaluation result

    Evaluating bboxes of pts\_bbox
mAP: 0.4278

    mATE: 0.4885
mASE: 0.4527
mAOE: 0.4086
mAVE: 0.5496
mAAE: 0.5859
NDS: 0.4653
Eval time: 2.7s

    Per-class results:
Object Class            AP      ATE     ASE     AOE     AVE     AAE

    car                     0.898   0.169   0.119   0.034   0.399   0.459
truck                   0.836   0.186   0.109   0.019   0.370   0.656
bus                     0.000   1.000   1.000   1.000   1.000   1.000
trailer                 0.000   1.000   1.000   1.000   1.000   1.000
construction\_vehicle    0.000   1.000   1.000   1.000   1.000   1.000
pedestrian              0.709   0.094   0.263   0.289   0.115   0.102
motorcycle              0.833   0.168   0.248   0.159   0.409   0.468
bicycle                 0.397   0.169   0.281   0.131   0.104   0.002
traffic\_cone            0.001   0.849   0.319   nan     nan     nan

    barrier                 0.604   0.250   0.188   0.046   nan     nan

* rain evaluation result

  Evaluating bboxes of pts\_bbox
mAP: 0.7198

  mATE: 0.2801
mASE: 0.2675
mAOE: 0.2577
mAVE: 0.1941
mAAE: 0.1430
NDS: 0.7456
Eval time: 12.2s

  Per-class results:
Object Class            AP      ATE     ASE     AOE     AVE     AAE

  car                     0.905   0.167   0.144   0.044   0.221   0.139
truck                   0.671   0.381   0.189   0.043   0.154   0.098
bus                     0.825   0.333   0.187   0.029   0.285   0.628
trailer                 0.550   0.539   0.221   0.586   0.177   0.084
construction\_vehicle    0.344   0.569   0.398   0.581   0.086   0.124
pedestrian              0.847   0.154   0.315   0.262   0.217   0.062
motorcycle              0.829   0.148   0.267   0.574   0.280   0.004
bicycle                 0.634   0.151   0.337   0.173   0.133   0.006
traffic\_cone            0.770   0.144   0.316   nan     nan     nan

  barrier                 0.823   0.215   0.300   0.028   nan     nan



  \---

  ### 트러블 슈팅

* vscode remote ssh 접속 오류

  #### 발생한 문제

  remote-ssh 설치 후, DL2 서버 접속 시도 시 다음과 같은 오류 발생

  &#x20;   ```jsx
    > Permission denied, please try again.
    ...
    Install terminal quit with output: 프로세스에서 없는 파이프에 쓰려고 했습니다.
    Received install output: 프로세스에서 없는 파이프에 쓰려고 했습니다.
    ...
    ```

  #### 해결 방법 및 원인 분석

  * 로컬 컴퓨터의 C:\\Users\\users.ssh\\known\_hosts파일에서, 할당 받은 서버 ip 관련 내용을 지우고 저장해, vscode 다시 실행해 접속 시도 ⇒ 여전히 동일한 오류 발생
  * 로컬 컴퓨터의 C:\\Users\\users.ssh\\config 파일에서, ip주소와 userid 직접 등록 후 ,
vscode 다시 실행해 접속 시도 ⇒ 성공
  * 맨처음 접속 시도 시, 서버 접속 주소를 잘못 작성. 해당 기록을 바탕으로 이후의 접속이 계속 시도되어 오류가 발생한 것으로 추정
* prediction 바운딩 박스 시각화 오류

  #### 발생한 문제

  초기에는, prediction 바운딩 박스가 거의 출력 되지 않는 문제 발생
해당 문제 해결 이후에는, 박스가 일부 출력 되었으나 ground truth와 방향 및 위치 불일치

  !\[바운딩 박스 출력 개수 적음](image.png)

  바운딩 박스 출력 개수 적음

  !\[출력된 박스의 방향 및 위치가 ground truth와 불일치](image%201.png)

  출력된 박스의 방향 및 위치가 ground truth와 불일치

  #### 해결 방법

  * **LiDAR → ego 좌표 변환 추가**

  ```jsx
        xyz\_ego = lidar2ego\_rot @ box\[:3] + lidar2ego\_trans
        ```

  * **yaw 쿼터니언 변환 적용**

  ```jsx
        pred\_quat = Quaternion(axis=\[0, 0, 1], angle=box\[6])
        rotated\_quat = lidar2ego\_quat \* pred\_quat
        final\_yaw = rotated\_quat.yaw\_pitch\_roll\[0]
        ```

  * **z축 중심점 보정**

  ```jsx
        box\[2] += box\[5] / 2
        ```

  * **w, l 순서 스왑**

  ```jsx
        w = box\[4]
        l = box\[3]
        ```

  * 카메라 뒤에 위치한 박스 처리 조건을 8개 코너 중 4개 이상이 z>0인 경우에만 해당 박스를 스킵하는
것으로 완화
  * draw\_box\_on\_images 함수 호출 코드를 for 루프 내부로 이동

  #### 원인 분석

  * 바운딩 박스 개수 부족 문제의 경우, draw\_box\_on\_iamges 함수가 for 루프에 걸리지 않아, 1개의 바운딩 박스만 생성되었던 것으로 확인.
  * 바운딩 박스의 방향 및 위치 불일치 문제의 경우, 다양한 원인이 존재

    * 좌표계 불일치 : prediction 바운딩 박스의 경우 LiDAR 좌표계 기준으로 출력되고, gt 박스는
ego 좌표계 기준으로 출력됨. 둘의 출력 방식을 통일하지 않고, 동일한 투영
함수를 사용했기에 위치 불일치 발생
    * yaw(방향각 오류) 변환 오류 : LiDAR → ego 변환 시 yaw를 단순히 더하는 방식 (box\[6] =
box\[6] + lidar2ego\_yae) 을 사용. 이후 쿼터니언 곱을 이용해 해결
    * 카메라 뒤 박스 처리 조건 과도한 제한 : 박스의 8개의 코너 중 한 개라도 z<0이면, 박스 전체를
스킵해버려 카메라 경계에 걸친 박스들이 모두 제거되는 문제 발생.
    * z축 중심점 기준의 차이 : MMDetection3D의 경우 바운딩 박스와 z좌표를 바닥면의 중심 기준으
로 저장, nuSceens의 경우 3D 박스의 정중앙을 기준으로 사용. 이를 보
정 없이 투영해 불일치 발생
    * w, l 순서의 차이 : MMDetection3D의 박스 포맷은 \[x, y, z, l, w, h, yaw]의 순서, ground truth의
박스 포맷은 \[x, y, z, w, l, h, yaw]의 순서.

  \---

  ### 공부한 내용

* nuScenes 데이터셋 폴더 구조

  * 중요한 폴더는 총 4개,  ‘v1.0-trainval/ ‘,  ‘ samples/’,  ‘sweeps/’,  ‘maps/’
  * v1.0-trainval/

    * 센서 데이터들의 저장 경로, 센서의 각도/위치를 담은 calibration, 어떤 사진의 어느 좌표에 자동차나 보행자가 있다는 정답(bounding box annotation) 등의 정보가 JSON 파일로 기록되어 있음
    * 실제 폴더 구조 및 설명

  ```jsx
            v1.0-trainval/
            ├── attribute.json             # 객체의 현재 상태나 세부 속성 (예: 차량이 '주차 중'인지, 보행자가 '걷고 있는지')
            ├── calibrated\_sensor.json     # 차량에 달린 각 센서의 정확한 부착 위치, 회전 각도 및 렌즈 파라미터 (캘리브레이션)
            ├── category.json              # 객체의 종류/클래스 분류 (예: car, pedestrian, bicycle 등)
            ├── ego\_pose.json              # 특정 순간(타임스탬프)에 자율주행 차량(Ego) 자체가 맵 상에서 어디에 있는지(위치/방향)
            ├── instance.json              # 여러 프레임에 걸쳐 동일한 객체를 추적하기 위해 부여된 객체별 고유 ID (Tracking용)
            ├── log.json                   # 주행 기록 메타데이터 (주행한 날짜, 지역, 차량 정보 등)
            ├── map.json                   # 해당 주행이 이루어진 지역의 지도(HD Map) 데이터 파일과의 연결 정보
            ├── sample.json                # 0.5초(2Hz) 간격으로 정답(Annotation)이 매겨진 핵심 기준 프레임들의 목록
            ├── sample\_annotation.json     # 정답지. 각 객체의 3D Bounding Box 크기(w,l,h), 좌표(x,y,z), 회전값
            ├── sample\_data.json           # 실제 센서 파일(.jpg, .pcd.bin)이 폴더 어디에 저장되어 있는지(경로)와 찍힌 시간
            ├── scene.json                 # 약 20초 길이로 잘라놓은 전체 주행 씬(Scene) 정보 (첫 sample과 마지막 sample을 연결)
            ├── sensor.json                # 장착된 12개 센서의 종류와 이름 (예: LIDAR\_TOP, CAM\_FRONT 등)
            └── visibility.json            # 객체가 다른 사물에 안 가려지고 얼마나 잘 보이는지에 대한 가시성 등급 (0\~100%)
            ```

      * 각각의 JSON 파일은 일종의 관계형 데이터베이스 상의 테이블 역할. 서로 고유한 키(token)로 연결되어 있음
  * samples/

    * 주요 센서 데이터. 차는 1초에 수십 번 데이터를 측정. 이를 모두 사용할 수 없기에, 1초에 2번(2Hz) 데이터를 골라냄. 해당 데이터에는 카메라 이미지(.jpg), 라이다(pcd.bin), 레이더 데이터들이 포함됨.
    * 실제 폴더 구조 및 설명

  ```jsx
            samples/
            ├── CAM\_FRONT/               # 전방 카메라 이미지
            │   ├── n015-2018-07-24-11-22-45+0800\_\_CAM\_FRONT\_\_1532402927612460.jpg
            │   └── n015-2018-07-24-11-22-45+0800\_\_CAM\_FRONT\_\_1532402928112460.jpg
            ├── CAM\_FRONT\_LEFT/          # 좌측 전방 카메라
            ├── CAM\_BACK/                # 후방 카메라
            ├── ... (총 6개의 카메라 폴더)
            ├── LIDAR\_TOP/               # 지붕 위 라이다 센서
            │   ├── n015-2018-07-24-11-22-45+0800\_\_LIDAR\_TOP\_\_1532402927647951.pcd.bin
            │   └── n015-2018-07-24-11-22-45+0800\_\_LIDAR\_TOP\_\_1532402928147951.pcd.bin
            ├── RADAR\_FRONT/             # 전방 레이더
            │   ├── n015-2018-07-24-11-22-45+0800\_\_RADAR\_FRONT\_\_1532402927600000.pcd
            │   └── ...
            └── ... (총 5개의 레이더 폴더)
            ```

      * 파일명은 항상 “씬이름\_\_센서이름\_\_타임스탬프.확장자” 의 구조
ex)   n015-2018-07-24-11-22-45+0800\_\_CAM\_FRONT\_\_1532402927612460.jpg
      * 총 12개의 센서 별 데이터 폴더가 존재 (6개의 카메라 + 1개의 라이다 + 5개의 레이더)
  * sweeps/

    * samples 사이에 찍힌 중간 과정 데이터. LiDAR 센서의 경우, 1초에 20번(20Hz) 회전하며 스캔함. 즉 samples 데이터 사이사이에, 정답이 매겨져 있지 않은 18번의 잔여 데이터들이 존재. sweeps 데이터를 여러 장 겹쳐서(stacking) 입력하면, 궤적에 대한 분석이 가능해짐. 즉
성능을 올리기 위해 주로 사용됨
    * 실제 폴더 구조 및 설명

  ```jsx
            sweeps/
            ├── CAM\_FRONT/
            │   ├── n015-2018-07-24-11-22-45+0800\_\_CAM\_FRONT\_\_1532402927662460.jpg  # sample과 sample 사이 시간!
            │   ├── n015-2018-07-24-11-22-45+0800\_\_CAM\_FRONT\_\_1532402927712460.jpg
            │   └── ...
            ├── LIDAR\_TOP/
            │   ├── n015-2018-07-24-11-22-45+0800\_\_LIDAR\_TOP\_\_1532402927697951.pcd.bin
            │   ├── n015-2018-07-24-11-22-45+0800\_\_LIDAR\_TOP\_\_1532402927747951.pcd.bin
            │   └── ...
            └── ... (나머지 10개 센서 폴더)
            ```

      * samples/ 와 동일하게 12개의 센서별 폴더로 구성되어 있음. 다만 파일 개수가 훨씬 더 많음.
  * maps/

    * 차량이 실제로 주행했던 지역의 고정밀 지도(HD 맵) 데이터. 차도, 인도, 횡단보도 등의 위치 정보가 포함되어 있음.  예를 들어, ‘이곳은 인도기에 자동차가 나타날 확률이 적다’ 와 같이 모델의 배경 지식(semantic prior)으로 활용됨
    * 실제 폴더 구조 및 설명

  ```jsx
            maps/
            ├── basemap/                 # 항공뷰 같은 고해상도 배경 이미지 (.png 파일들)
            ├── boston-seaport.json      # 보스턴 항구 지역 도로/인도 맵 정보
            ├── singapore-onenorth.json  # 싱가포르 원노스 지역
            ├── singapore-hollandvillage.json
            └── singapore-queenstown.json
            ```

      * 주행을 진행한 4곳의 지역(미국 보스턴 1곳, 싱가포르 3곳)에 대한 정보로 구성.





### 

