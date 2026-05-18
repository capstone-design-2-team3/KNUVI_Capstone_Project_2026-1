# Snow Image Refinement Pipeline for 3DGS Reconstruction

본 소프트웨어는 정렬된 snow image folder를 입력받아 외부 MWFormer 모델을 실행하고,
복원 결과를 LongSplat/COLMAP+3DGS가 바로 사용할 수 있는 `scene/input/*.png` 구조로 정리하는
2D refinement runner SW입니다.

본 SW는 MWFormer 모델 자체를 개발하거나 수정하는 것이 아니라, 외부 third-party 모델을
3DGS_snow 파이프라인에 연결하기 위한 입력 관리, 실행 자동화, 출력 정리, 로그 저장,
manifest 생성 기능을 제공합니다.

## Folder Structure

```text
snow_refinement_pipeline/
├── README.md
├── THIRD_PARTY_LICENSES.md
├── requirements.txt
├── configs/
│   └── refinement.yaml
├── tools/
│   ├── validate_input.py
│   ├── run_mwformer_inference.py
│   ├── collect_outputs.py
│   ├── make_manifest.py
│   └── run_refinement.py
├── utils/
│   ├── file_utils.py
│   ├── image_utils.py
│   ├── logging_utils.py
│   └── manifest_utils.py
├── external/
│   └── MWFormer/
├── weights/
│   └── MWFormer/
├── data/
│   ├── snow/
│   └── de_snow/
└── outputs/
    ├── logs/
    ├── manifests/
    └── mwformer_raw/
```

## 1. Input Validation

```bash
python tools/validate_input.py \
  --input_dir data/snow/grass/input
```

## 2. MWFormer Inference Only

```bash
python tools/run_mwformer_inference.py \
  --input_dir data/snow/grass/input \
  --raw_output_dir outputs/mwformer_raw/grass \
  --mwformer_repo external/MWFormer \
  --backbone_path weights/MWFormer/MWFormer_L/backbone \
  --style_filter_path weights/MWFormer/MWFormer_L/style_filter
```

## 3. Collect Raw Outputs

```bash
python tools/collect_outputs.py \
  --input_dir data/snow/grass/input \
  --raw_output_dir outputs/mwformer_raw/grass \
  --output_dir data/de_snow/grass/input \
  --overwrite
```

## 4. Full Pipeline

```bash
python tools/run_refinement.py \
  --input_dir data/snow/grass/input \
  --output_dir data/de_snow/grass/input \
  --mwformer_repo external/MWFormer \
  --backbone_path weights/MWFormer/MWFormer_L/backbone \
  --style_filter_path weights/MWFormer/MWFormer_L/style_filter
```

## 5. Test Without MWFormer

MWFormer 설치 전에는 이미 존재하는 raw output을 이용해 출력 정리 단계만 테스트할 수 있습니다.

```bash
python tools/run_refinement.py \
  --input_dir data/snow/grass/input \
  --output_dir data/de_snow/grass/input \
  --mwformer_repo external/MWFormer \
  --backbone_path weights/MWFormer/MWFormer_L/backbone \
  --style_filter_path weights/MWFormer/MWFormer_L/style_filter \
  --raw_output_dir outputs/mwformer_raw/grass \
  --skip_mwformer
```

## Notes

- 입력 snow image folder는 이미 정렬되어 있다고 가정합니다.
- `data_prep.sh` 또는 `prepare_dataset.py`는 본 SW의 필수 구성요소가 아닙니다.
- MWFormer repo 및 pretrained weights는 외부 third-party component입니다.
- 본 SW 등록 범위는 wrapper/runner, I/O management, output collection, manifest generation입니다.
