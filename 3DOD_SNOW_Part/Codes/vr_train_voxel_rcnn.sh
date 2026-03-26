#!/usr/bin/env bash

export CUDA_VISIBLE_DEVICES=0

CFG_NAME=voxel_rcnn/voxel_rcnn_3classes

python train.py --cfg_file cfgs/$CFG_NAME.yaml --epochs 80 --workers 8