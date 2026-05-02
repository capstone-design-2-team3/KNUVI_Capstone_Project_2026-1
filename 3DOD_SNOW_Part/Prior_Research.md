# Robust 3D Object Detection under Adverse Weather

## Paper Summary Table

| Title | Venue | Code | Dataset | Key Idea | Link |
|------|------|------|--------|----------|------|
| Robust multimodal 3D object detection: overcoming weather challenges in autonomous driving perception systems | Springer 2026 | - | nuScenes, KITTI | Robust fusion + data augmentation to mitigate feature mismatch under adverse weather | https://link.springer.com/article/10.1007/s11760-025-05081-9 |
| Enhancing Robustness of LiDAR-Based Perception in Adverse Weather using Point Cloud Augmentations | IEEE 2023 | - | STF (snow, fog, rain) | Point cloud augmentation improves LiDAR-based detector robustness (Voxel R-CNN) | https://ieeexplore.ieee.org/document/10186696 |
| LossDistillNet: 3D Object Detection in Point Cloud Under Harsh Weather Conditions | IEEE 2022 | - | KITTI + LISA (fog, snow) | Knowledge distillation + probabilistic point recovery for missing points | https://ieeexplore.ieee.org/document/9853505 |
| Equirectangular Point Reconstruction for Domain Adaptive Multimodal 3D Object Detection in Adverse Weather Conditions | AAAI 2025 | https://github.com/jhyoon964/EquiDetect | KITTI (synthetic), CADC, Dense | Point reconstruction + domain adaptation + noise matching | https://ojs.aaai.org/index.php/AAAI/article/view/33035 |
| Towards Accurate 3D Object Detection in Adverse Weather by Leveraging 4D Radar for LiDAR Geometry Enhancement | AAAI 2026 | (TBA) https://github.com/TongTianxu/REL | K-Radar, VoD + fog simulation | Generate virtual LiDAR points using 4D radar | https://ojs.aaai.org/index.php/AAAI/article/view/33035 |
| AW-MoE: All-Weather Mixture of Experts for Robust Multi-Modal 3D Object Detection | arXiv 2026 | https://github.com/windlinsherlock/AW-MoE | K-Radar | Weather-specific experts (MoE) + dual-modal augmentation | https://arxiv.org/abs/2603.16261 |

---

## Detailed Summaries

### 1. Robust Multimodal 3D Object Detection (Springer 2026)

* **Problem**
  Adverse weather causes **modality-specific degradation**, leading to feature mismatch between LiDAR and camera.

* **Method**

  * Introduces a **robustness evaluation benchmark** (4 weather conditions)
  * Combines:

    * Robust fusion design
    * Weather-aware data augmentation

* **Contribution**

  * Improves **multimodal consistency**
  * Enhances **generalization in real-world conditions**

---

### 2. LiDAR Augmentation for Adverse Weather (IEEE 2023)

* **Problem**
  LiDAR-based detectors degrade significantly under rain, snow, and fog.

* **Method**

  * Realistic **weather simulation-based point cloud augmentation**
  * Applied to **Voxel R-CNN**

* **Contribution**

  * Significant AP improvement across weather conditions
  * Demonstrates effectiveness of **data-centric robustness**

---

### 3. LossDistillNet (IEEE 2022)

* **Problem**
  Severe **point loss (missing points)** in adverse weather.

* **Method**

  * **Teacher–Student Knowledge Distillation**
  * **DMFA-based probabilistic point reconstruction**
  * Loss-convolution layer for recovery

* **Contribution**

  * Directly handles **point-level degradation**
  * Improves robustness without relying on multimodal fusion

---

### 4. Equirectangular Point Reconstruction (AAAI 2025)

* **Problem**
  Sparse and noisy point clouds + domain gap between datasets.

* **Method**

  * **Equirectangular projection-based reconstruction**
  * Distance-aware denoising + far-object point generation
  * Feature perturbation-based **domain adaptation**
  * **Weather noise matching** between synthetic & real data

* **Contribution**

  * Unified framework for:

    * Reconstruction
    * Domain adaptation
    * Noise alignment

---

### 5. REL: Radar-based LiDAR Enhancement (AAAI 2026)

* **Problem**
  LiDAR severely degrades in adverse weather.

* **Method**

  * Generate **virtual LiDAR points from 4D radar**
  * Key modules:

    * PGCA (Position-Guided Cross Attention)
    * AFF (Adaptive Feature Fusion)

* **Contribution**

  * Reduces dependence on LiDAR
  * Improves robustness using **complementary sensor (radar)**

---

### 6. AW-MoE (arXiv 2026)

* **Problem**
  Different weather distributions cause **performance conflicts** when trained jointly.

* **Method**

  * **Mixture of Experts (MoE)** for weather-specific specialization
  * **Image-guided Weather-aware Routing (IWR)**
  * **Unified Dual-Modal Augmentation (UDMA)** (LiDAR + radar)

* **Contribution**

  * Adaptive expert selection per weather
  * Resolves **distribution mismatch across conditions**

---

## Key Takeaways

* **Data-centric approaches**
  → Augmentation, simulation, noise matching

* **Model-centric approaches**
  → MoE, distillation, reconstruction

* **Sensor fusion evolution**

  * LiDAR only → LiDAR + Camera
 

## Point Cloud Completion & Augmentation Papers

| Title | Venue | Code | Dataset | Method Summary (KR + Key EN) | Modality |
|------|------|------|--------|-----------------------------|----------|
| Object Detection of Occlusion Point Cloud based on Transformer | IJCNN 2023 | X | KITTI, Waymo | 가려진 포인트 클라우드를 입력으로 받아 **Transformer 기반 shape completion**으로 누락된 포인트를 복원 | LiDAR |
| Improving 3D Vulnerable Road User Detection With Point Augmentation | IEEE 2023 | X | KITTI, Waymo | proposal 영역에서 **geometric symmetry 기반 fictional point 생성**으로 sparse 문제 완화 | LiDAR |
| PG-RCNN: Semantic Surface Point Generation for 3D Object Detection | ICCV 2023 |  | KITTI | RoI 내 문맥을 활용해 **semantic-aware surface point generation** 수행 | LiDAR |
| SIANet: 3D Object Detection with Structural Information Augment Network | IET 2024 | X | KITTI, Waymo | RoI 객체의 구조를 재구성하는 **structure reconstruction + feature fusion** | LiDAR |
| CRA-PCN: Point Cloud Completion with Cross-Resolution Transformers | AAAI 2024 |  | PCN, ShapeNet, MVP | **cross-resolution Transformer + coarse-to-fine upsampling**으로 점진적 복원 | LiDAR |
| AnchorFormer: Point Cloud Completion From Discriminative Nodes | CVPR 2023 |  | PCN, ShapeNet, KITTI | **learned anchor 확장 + 2D grid deformation**으로 missing point 생성 | LiDAR |
| SVDFormer: Self-view Augmentation and Dual-generator | ICCV 2023 |  | PCN, ShapeNet, KITTI, ScanNet | **multi-view depth + dual-generator (global + structure)** 기반 복원 | LiDAR + Image |
| PointSea: Self-structure Augmentation for Completion | IJCV 2025 |  | ShapeNet, PCN, KITTI, ScanNet, Matterport3D | **self-projected depth + dual-generator refinement**로 구조 보완 | LiDAR + Image |
| CP3: Pretrain-Prompt-Predict for Completion | IEEE 2023 |  | MVP, PCN | **IOI pretext task + prompt-based refinement**로 robust completion | LiDAR |
| P2C: Self-Supervised Completion from Partial Clouds | ICCV 2023 |  | ShapeNet, ScanNet | **patch masking + structural prior learning**으로 self-supervised 복원 | LiDAR |
| CSDN: Cross-Modal Shape-Transfer Dual-Refinement | TVCG 2024 |  | ShapeNet-ViPC | **image → shape transfer + graph refinement + global constraint** | LiDAR + Image |
| PU-Mask: Point Cloud Upsampling via Virtual Mask | IEEE 2024 |  | PU1K, ModelNet40 | **mask-guided Transformer**로 hidden 영역 복원 후 upsampling | LiDAR |
| Sparse Points to Dense Clouds | IEEE 2024 | X | KITTI, JackRabbot | **sparse LiDAR + single image fusion**으로 dense point reconstruction | LiDAR + Image |
| VirtualPainting: Virtual Points for 3DOD | Sensors 2025 | X | KITTI, nuScenes | 이미지 기반 **virtual LiDAR point 생성 + semantic labeling** | LiDAR + Image |
| Hyperspherical Embedding for Completion | CVPR 2023 |  | ModelNet40, ShapeNet, MVP, GraspNet | **hyperspherical embedding**으로 안정적인 feature 학습 후 복원 | LiDAR |
| Implicit and Efficient Completion for Tracking | IEEE 2023 | X | KITTI, Waymo | **temporal information (previous frames)** 활용한 completion | LiDAR + Temporal |
| FSC: Few-point Shape Completion | CVPR 2024 |  | ShapeNet, KITTI, PCN | **extreme sparse 대응 dual-branch + multi-stage refinement** | LiDAR + Image |
| SPU-IMR: Iterative Mask-Recovery Upsampling | AAAI 2025 |  | SAPCU | **iterative mask recovery + patch merging**으로 dense reconstruction | LiDAR |
| MoDAR: Motion Forecasting for 3DOD | CVPR 2023 | X | Waymo | **motion forecasting 기반 virtual point 생성** | LiDAR + Temporal |
  * → LiDAR + Radar (robust perception)

---

