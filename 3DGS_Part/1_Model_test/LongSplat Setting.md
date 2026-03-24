# 연구실 서버 원격접속 
https://hojunking.notion.site/Tailscale-2d2cb6677057803393c6ea8cbeab0482
```
#DL2 접속 
ssh knuvi@100.90.194.39
#DL2 서버 passward : knuvi
```

---
# LongSplat 환경설정
https://github.com/NVlabs/LongSplat?tab=readme-ov-file
```
# git clone

git clone --recursive https://github.com/NVlabs/LongSplat.git
cd LongSplat
```

```
# 환경 설정 및 pytorch 설치 (cuda version = 12.1)

conda create -n yoonho_longsplat python=3.10.13 cmake=3.14.0 -y
conda activate yoonho_longsplat
conda install pytorch torchvision pytorch-cuda=12.1 -c pytorch -c nvidia  
```

```
# pytorch3d, torch_scatter 두 개 설치할 때 torch를 못 찾음
# -> pre-built wheel 사용해서 먼저 따로 설치

pip install --extra-index-url https://miropsota.github.io/torch_packages_builder \ 
	pytorch3d==0.7.8+pt2.5.1cu121
	
pip install torch_scatter -f https://data.pyg.org/whl/torch-2.5.1+cu121.html

pip install -r requirements.txt
```

```
# 3DGS submodule 들을 위한 세팅

# 1. CUDA 12.1을 PATH로 잡기
export PATH=/usr/local/cuda-12.1/bin:$PATH export LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH

# 2. gcc 버전을 9 이상으로 올리기
gcc --version # 버전 확인
sudo apt-get install -y gcc-9 g++-9
sudo update-alternatives --set gcc /usr/bin/gcc-9
sudo update-alternatives --set g++ /usr/bin/g++-9
gcc --version # 9.4.0 나와야 함
```

```
# submodule install

pip install submodules/simple-knn --no-build-isolation 
pip install submodules/diff-gaussian-rasterization --no-build-isolation 

# 연구실 서버 : RTX 2080 Ti -> fused-ssim은 이에 맞춰서 빌드 필요

# fused-ssim 디렉토리로 이동
export TORCH_CUDA_ARCH_LIST="7.5"
pip install -e . --no-build-isolation
```

---
# 데이터셋 준비 및 모델 돌리기

`mkdir data` 로 디렉토리 미리 만들어 둬야 함.
`scp` 를 사용하면 편하게 원격 우분투 서버 <-> 로컬 맥 사이 데이터를 옮길 수 있다. 
참고 : https://develop-famous.tistory.com/199

```
# 기본 명령어
scp [옵션 -r:폴더 전송 모드] [로컬파일위치] [유저이름@호스트]:[옮길경로]
```

```
# Mac => Server
# Mac의 디렉토리가 Server 디렉토리 안으로 복사됨
scp -r /Users/yhlee/Documents/4_KNU/2_종프2/3_3DGS_Models/2_LongSplat/dataset/WGS_test/etc knuvi@100.90.194.39:/home/knuvi/Undergraduate/yoonho/LongSplat/data/custom
```

```
# Server => Mac
scp -r knuvi@100.90.194.39:/home/knuvi/Undergraduate/yoonho/LongSplat/outputs/data/custom /Users/yhlee/Documents/4_KNU/2_종프2/3_3DGS_Models/2_LongSplat/output
```

**Free dataset**
- LongSplat이 Free dataset을 위한 실행 명령어를 제공한다.
- `LongSplat/data/free` 디렉토리 안에 free_dataset 의 각 씬들을 위치시킨다.
- `bash scripts/train_free.sh` 실행한다.

**개인 데이터셋 사용 (WeatherGS Dataset)**
- data 디렉토리에 개인 데이터셋 디렉토리가 들어있어야 함
- ex. `LongSplat/data/CUSTOM/images/이미지들...`

```
cd /home/knuvi/Undergraduate/yoonho/LongSplat
nano scripts/train_custom.sh
# scene='./data/YOUR_CUSTOM_DATA' 이런 식으로 바꾸기
# Ctrl+O, Enter, Ctrl+X 저장 후 종료

bash scripts/train_custom.sh
```
이렇게 하면 하나의 카테고리만 돌릴 수 있음.. 그래서..
여러개 돌릴 수 있도록 만들었다.

먼저 train_custom.sh를 여러개로 복사한다.
```
cd /home/knuvi/Undergraduate/yoonho/LongSplat

cp scripts/train_custom.sh scripts/train_custom_data10.sh
cp scripts/train_custom.sh scripts/train_custom_data11.sh
cp scripts/train_custom.sh scripts/train_custom_data12.sh
cp scripts/train_custom.sh scripts/train_custom_data13.sh
cp scripts/train_custom.sh scripts/train_custom_data14.sh
cp scripts/train_custom.sh scripts/train_custom_data15.sh
cp scripts/train_custom.sh scripts/train_custom_data16.sh

# 이후 하나씩 수정.
nano scripts/train_custom_data1.sh
# Ctrl+O, Enter, Ctrl+X 저장 후 종료
```

```
nano run_all_customs3.sh
```

```
#!/bin/bash
set -e

bash scripts/train_custom_data10.sh 
bash scripts/train_custom_data11.sh 
bash scripts/train_custom_data12.sh
bash scripts/train_custom_data13.sh 
bash scripts/train_custom_data14.sh 
bash scripts/train_custom_data15.sh
bash scripts/train_custom_data16.sh

# Ctrl+O, Enter, Ctrl+X 저장 후 종료
```

```
chmod +x run_all_customs3.sh # 권한 주기
./run_all_customs3.sh        # 실행
```

만약 .DS_Store 얘 때문에 문제 생기는 것 같으면 아래 명령어로 다 지우기
```
cd /home/knuvi/Undergraduate/yoonho/LongSplat
find data -name ".DS_Store" -delete
```

---
*Free dataset을 위한 코드*

```
# Mac => Server
scp -r /Users/yhlee/Documents/4_KNU/2_종프2/3_3DGS_Models/2_LongSplat/dataset/free_dataset knuvi@100.90.194.39:/home/knuvi/Undergraduate/yoonho/LongSplat/data/free
```

```
# Server => Mac
scp -r knuvi@100.90.194.39:/home/knuvi/Undergraduate/yoonho/LongSplat/outputs/data/free /Users/yhlee/Documents/4_KNU/2_종프2/3_3DGS_Models/2_LongSplat/output
```