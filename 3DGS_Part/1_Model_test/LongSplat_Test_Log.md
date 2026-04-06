# LongSplat Test
https://github.com/NVlabs/LongSplat/tree/main

## Task Contents

- 실험진행
  - Free dataset, 조사하신 날씨 GS dataset 3개에 대한 LongSplat baseline 결과 수집
  - Free dataset은 init이 잘 됐는지 확인 용
- 문제점 확인
  - 에러가 난다면 LongSplat의 어떤 파트에서 문제가 발생하는지
  - Rendered view 정성적인 문제점 시각화
  - 문제를 확인했다면, 어떻게 이 문제를 해결할 지 고민
- 유의점
  - Val set idx interval에 각별히 검증

환경 init (docker) : [참고](https://www.notion.so/310cb667705780a88dd9d4efec7bd9bf?pvs=21)

실습실 pc 1, 2 사용 : [참고](https://www.notion.so/2d2cb6677057803393c6ea8cbeab0482?pvs=21)

## Onboarding Tasks

3/4 기준 사용 가능한 자원 없음, 로컬환경에서 모델 사용가능 여부 확인
-> 실패. 계속해서 시도 중

3/10 기준 실습실 자원 사용 가능성 불확실. 개인장비 또는 코랩 런타임 사용 필요

# Model Test 

## 1. With WeatherGS dataset
- 연구실 서버 사용하여 진행
- 세팅 과정은 LongSplat Setting.md 참고
- 기본 렌더링 결과가 꽤 좋지 않게 나옴
  - WeatherGS가 제공하는 데이터셋 프레임 수가 적어서 그런지, LongSplat의 세팅이 잘못된 것인지 모르겠음
  - Free dataset으로 다시 시도해봐야 할 것 같음
  - 추가로, LongSplat의 output은 3DGS 포맷과 다름. 이것도 결과가 안좋아 보이는 원인일 수 있으니 변환을 거친 뒤에 확인하는 것도 필요함

## 2. With Free dataset
- 진행 예정