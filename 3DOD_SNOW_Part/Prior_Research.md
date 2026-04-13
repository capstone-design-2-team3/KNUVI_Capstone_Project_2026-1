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
  * → LiDAR + Radar (robust perception)

---

원하면
👉 “연구 흐름 (timeline)”이나
👉 “baseline vs 개선 방향 그림”도 README용으로 같이 만들어줄게
