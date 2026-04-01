# Codes for train, eval, infer 3DOD models

pp_ : PointPillars  
pr_ : PointRCNN  
vr_ : VoxelRCNN  
mv_ : mvmm  
  
mv_inference.py : Inference kitti-snow dataset to predict model (ply file format)  
  
pp_evaluate_snow.py : Evaluate kitti-snow dataset  
pp_inference.py : Inference kitti-snow dataset to predict model (ply file format)  
  
pr_convert_to_ply.py :   
pr_eval.sh : Running pr_eval_rcnn for one code (Evaluate 3-object for one code as each object has each checkpoint file)  
pr_eval_rcnn.py : Evaluate objects for each checkpoint file(car, cyclist, pedestrian)  
  
vr_analyze_point_all.py : Calculate point loss rate for all point cloud  
vr_analyze_point_scene.py : Calculate point loss rate for each scene  
vr_eval_voxel_rcnn.sh : Running test code to get evaluation results  
vr_inference.py : Inference kitti-snow dataset to predict model (ply file format)  
vr_project_gt_to_image.py : Plotting GT bbox on image  
vr_project_to_image.py : Plotting predicted bbox on image  
vr_train_voxel_rcnn.sh : Running train code to get model checkpoint  
