#!/usr/bin/env bash

export CUDA_VISIBLE_DEVICES=0

CFG_NAME=voxel_rcnn/voxel_rcnn_3classes

python test.py --cfg_file cfgs/$CFG_NAME.yaml --batch_size 8 --ckpt ../output/$CFG_NAME/default/ckpt/checkpoint_epoch_80.pth

