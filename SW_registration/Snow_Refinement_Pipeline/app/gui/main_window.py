from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.config_manager import load_settings, save_settings
from app.services.pipeline_worker import CheckSetupWorker, PipelineWorker
from app.services.scene_scanner import scan_scenes


class PathRow(QWidget):
    def __init__(self, label: str, mode: str = "directory"):
        super().__init__()
        self.mode = mode
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(label)
        self.label.setMinimumWidth(140)
        self.line = QLineEdit()
        self.button = QPushButton("찾아보기")

        layout.addWidget(self.label)
        layout.addWidget(self.line, 1)
        layout.addWidget(self.button)

        self.button.clicked.connect(self.browse)

    def text(self) -> str:
        return self.line.text().strip()

    def setText(self, value: str):
        self.line.setText(value)

    def browse(self):
        if self.mode == "file":
            selected, _ = QFileDialog.getOpenFileName(self, self.label.text())
        else:
            selected = QFileDialog.getExistingDirectory(self, self.label.text())

        if selected:
            self.line.setText(selected)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Snow Image Refinement Pipeline for 3DGS Reconstruction")
        self.resize(1120, 820)

        self.project_root = PROJECT_ROOT
        self.settings_path = self.project_root / "configs" / "gui_settings.json"
        self.settings = load_settings(self.settings_path)

        self.worker_thread: QThread | None = None
        self.worker = None

        self._build_ui()
        self._load_settings_to_ui()

    def _build_ui(self):
        central = QWidget()
        root_layout = QVBoxLayout(central)
        self.setCentralWidget(central)

        path_group = QGroupBox("경로 설정")
        path_layout = QVBoxLayout(path_group)

        self.snow_root_row = PathRow("Snow root")
        self.output_root_row = PathRow("Output root")
        self.raw_output_root_row = PathRow("Raw output root")
        self.mwformer_repo_row = PathRow("MWFormer repo")
        self.backbone_row = PathRow("Backbone weight", mode="file")
        self.style_filter_row = PathRow("Style filter weight", mode="file")

        for row in [
            self.snow_root_row,
            self.output_root_row,
            self.raw_output_root_row,
            self.mwformer_repo_row,
            self.backbone_row,
            self.style_filter_row,
        ]:
            path_layout.addWidget(row)

        root_layout.addWidget(path_group)

        option_group = QGroupBox("실행 옵션")
        option_layout = QHBoxLayout(option_group)

        self.device_line = QLineEdit()
        self.device_line.setMaximumWidth(100)

        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(1, 64)

        self.num_workers_spin = QSpinBox()
        self.num_workers_spin.setRange(0, 16)

        self.max_side_spin = QSpinBox()
        self.max_side_spin.setRange(1, 8192)

        self.size_multiple_spin = QSpinBox()
        self.size_multiple_spin.setRange(1, 128)

        self.skip_mwformer_check = QCheckBox("MWFormer 실행 생략")
        self.skip_mwformer_check.setToolTip("테스트용: 이미 존재하는 raw output만 collect할 때 사용")

        option_layout.addWidget(QLabel("Device"))
        option_layout.addWidget(self.device_line)
        option_layout.addWidget(QLabel("Batch"))
        option_layout.addWidget(self.batch_spin)
        option_layout.addWidget(QLabel("Workers"))
        option_layout.addWidget(self.num_workers_spin)
        option_layout.addWidget(QLabel("Max side"))
        option_layout.addWidget(self.max_side_spin)
        option_layout.addWidget(QLabel("Multiple"))
        option_layout.addWidget(self.size_multiple_spin)
        option_layout.addWidget(self.skip_mwformer_check)
        option_layout.addStretch(1)

        root_layout.addWidget(option_group)

        scene_group = QGroupBox("Scene 자동 탐색")
        scene_layout = QVBoxLayout(scene_group)

        button_layout = QHBoxLayout()
        self.scan_button = QPushButton("Scene 탐색")
        self.select_all_button = QPushButton("전체 선택")
        self.unselect_all_button = QPushButton("전체 해제")
        self.check_button = QPushButton("환경 확인")
        self.run_button = QPushButton("선택 Scene 실행")
        self.stop_button = QPushButton("중지 요청")
        self.open_output_button = QPushButton("출력 폴더 열기")
        self.stop_button.setEnabled(False)

        button_layout.addWidget(self.scan_button)
        button_layout.addWidget(self.select_all_button)
        button_layout.addWidget(self.unselect_all_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.check_button)
        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.open_output_button)

        self.scene_list = QListWidget()
        scene_layout.addLayout(button_layout)
        scene_layout.addWidget(self.scene_list)

        root_layout.addWidget(scene_group, 2)

        log_group = QGroupBox("실행 로그")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)

        log_button_layout = QHBoxLayout()
        self.clear_log_button = QPushButton("로그 지우기")
        self.save_settings_button = QPushButton("설정 저장")
        log_button_layout.addWidget(self.clear_log_button)
        log_button_layout.addWidget(self.save_settings_button)
        log_button_layout.addStretch(1)

        log_layout.addWidget(self.log_text)
        log_layout.addLayout(log_button_layout)

        root_layout.addWidget(log_group, 3)

        self.scan_button.clicked.connect(self.scan_scenes)
        self.select_all_button.clicked.connect(lambda: self.set_all_scenes_checked(True))
        self.unselect_all_button.clicked.connect(lambda: self.set_all_scenes_checked(False))
        self.check_button.clicked.connect(self.check_setup)
        self.run_button.clicked.connect(self.run_selected_scenes)
        self.stop_button.clicked.connect(self.request_stop)
        self.open_output_button.clicked.connect(self.open_output_folder)
        self.clear_log_button.clicked.connect(self.log_text.clear)
        self.save_settings_button.clicked.connect(self.save_current_settings)

    def _load_settings_to_ui(self):
        self.snow_root_row.setText(self.settings.get("snow_root", "data/snow"))
        self.output_root_row.setText(self.settings.get("output_root", "data/de_snow"))
        self.raw_output_root_row.setText(self.settings.get("raw_output_root", "outputs/mwformer_raw"))
        self.mwformer_repo_row.setText(self.settings.get("mwformer_repo", ""))
        self.backbone_row.setText(self.settings.get("backbone_path", ""))
        self.style_filter_row.setText(self.settings.get("style_filter_path", ""))

        self.device_line.setText(str(self.settings.get("device", "auto")))
        self.batch_spin.setValue(int(self.settings.get("batch_size", 1)))
        self.num_workers_spin.setValue(int(self.settings.get("num_workers", 0)))
        self.max_side_spin.setValue(int(self.settings.get("max_side", 1024)))
        self.size_multiple_spin.setValue(int(self.settings.get("size_multiple", 16)))

    def collect_settings(self) -> dict:
        return {
            "snow_root": self.snow_root_row.text(),
            "output_root": self.output_root_row.text(),
            "raw_output_root": self.raw_output_root_row.text(),
            "mwformer_repo": self.mwformer_repo_row.text(),
            "backbone_path": self.backbone_row.text(),
            "style_filter_path": self.style_filter_row.text(),
            "device": self.device_line.text() or "auto",
            "batch_size": self.batch_spin.value(),
            "num_workers": self.num_workers_spin.value(),
            "max_side": self.max_side_spin.value(),
            "size_multiple": self.size_multiple_spin.value(),
        }

    def save_current_settings(self):
        save_settings(self.settings_path, self.collect_settings())
        self.append_log(f"[INFO] Settings saved: {self.settings_path}")

    def append_log(self, text: str):
        self.log_text.appendPlainText(text)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def scan_scenes(self):
        self.save_current_settings()

        snow_root = self.snow_root_row.text()
        scenes = scan_scenes(snow_root)

        self.scene_list.clear()

        if not scenes:
            self.append_log(f"[WARN] No scenes found under: {snow_root}")
            QMessageBox.warning(
                self,
                "Scene 탐색 실패",
                "scene을 찾지 못했습니다.\n예상 구조: snow_root/scene/input/*.png",
            )
            return

        for scene in scenes:
            item = QListWidgetItem(f"{scene.name} ({scene.image_count} images)")
            item.setData(Qt.UserRole, scene.name)
            item.setCheckState(Qt.Checked)
            self.scene_list.addItem(item)

        self.append_log(f"[INFO] Found scenes: {', '.join(s.name for s in scenes)}")

    def set_all_scenes_checked(self, checked: bool):
        state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.scene_list.count()):
            self.scene_list.item(i).setCheckState(state)

    def selected_scenes(self) -> list[str]:
        scenes = []
        for i in range(self.scene_list.count()):
            item = self.scene_list.item(i)
            if item.checkState() == Qt.Checked:
                scenes.append(item.data(Qt.UserRole))
        return scenes

    def validate_common_paths(self) -> bool:
        required = {
            "Snow root": self.snow_root_row.text(),
            "Output root": self.output_root_row.text(),
            "Raw output root": self.raw_output_root_row.text(),
            "MWFormer repo": self.mwformer_repo_row.text(),
            "Backbone weight": self.backbone_row.text(),
            "Style filter weight": self.style_filter_row.text(),
        }

        missing = [name for name, value in required.items() if not value]

        if missing:
            QMessageBox.warning(self, "경로 누락", "다음 경로를 입력하세요:\n" + "\n".join(missing))
            return False

        return True

    def first_scene_input_dir(self) -> str | None:
        scenes = self.selected_scenes()
        if not scenes:
            if self.scene_list.count() == 0:
                self.scan_scenes()
            scenes = self.selected_scenes()

        if not scenes:
            return None

        return str(Path(self.snow_root_row.text()) / scenes[0] / "input")

    def check_setup(self):
        if not self.validate_common_paths():
            return

        input_dir = self.first_scene_input_dir()
        if not input_dir:
            QMessageBox.warning(self, "Scene 없음", "먼저 Scene을 탐색하고 선택하세요.")
            return

        self.save_current_settings()
        self.append_log("[INFO] Checking MWFormer setup...")

        self.worker_thread = QThread()
        self.worker = CheckSetupWorker(
            project_root=self.project_root,
            input_dir=input_dir,
            mwformer_repo=self.mwformer_repo_row.text(),
            backbone_path=self.backbone_row.text(),
            style_filter_path=self.style_filter_row.text(),
        )
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.log.connect(self.append_log)
        self.worker.finished.connect(self.on_check_finished)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.check_button.setEnabled(False)
        self.worker_thread.start()

    def on_check_finished(self, success: bool):
        self.check_button.setEnabled(True)
        self.append_log("[OK] Setup check success." if success else "[FAIL] Setup check failed.")

    def run_selected_scenes(self):
        if not self.validate_common_paths():
            return

        scenes = self.selected_scenes()
        if not scenes:
            QMessageBox.warning(self, "Scene 없음", "실행할 scene을 선택하세요.")
            return

        self.save_current_settings()
        self.append_log(f"[INFO] Run selected scenes: {', '.join(scenes)}")

        self.worker_thread = QThread()
        self.worker = PipelineWorker(
            project_root=self.project_root,
            scenes=scenes,
            snow_root=self.snow_root_row.text(),
            output_root=self.output_root_row.text(),
            raw_output_root=self.raw_output_root_row.text(),
            mwformer_repo=self.mwformer_repo_row.text(),
            backbone_path=self.backbone_row.text(),
            style_filter_path=self.style_filter_row.text(),
            device=self.device_line.text() or "auto",
            batch_size=self.batch_spin.value(),
            num_workers=self.num_workers_spin.value(),
            max_side=self.max_side_spin.value(),
            size_multiple=self.size_multiple_spin.value(),
            skip_mwformer=self.skip_mwformer_check.isChecked(),
        )

        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.log.connect(self.append_log)
        self.worker.scene_started.connect(lambda s: self.append_log(f"[START] {s}"))
        self.worker.scene_finished.connect(lambda s, ok: self.append_log(f"[DONE] {s}: {'success' if ok else 'fail'}"))
        self.worker.all_finished.connect(self.on_pipeline_finished)
        self.worker.all_finished.connect(self.worker_thread.quit)
        self.worker.all_finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.run_button.setEnabled(False)
        self.check_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.worker_thread.start()

    def request_stop(self):
        if self.worker and hasattr(self.worker, "stop"):
            self.worker.stop()
            self.append_log("[INFO] Stop requested. Current scene may finish before stopping.")

    def on_pipeline_finished(self, success: bool):
        self.run_button.setEnabled(True)
        self.check_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        if success:
            self.append_log("[OK] All selected scenes completed.")
            QMessageBox.information(self, "완료", "선택한 scene 처리가 완료되었습니다.")
        else:
            self.append_log("[FAIL] Some scenes failed.")
            QMessageBox.warning(self, "실패", "일부 scene 처리에 실패했습니다. 로그를 확인하세요.")

    def open_output_folder(self):
        output_root = Path(self.output_root_row.text())
        output_root.mkdir(parents=True, exist_ok=True)

        if sys.platform.startswith("win"):
            os.startfile(str(output_root))
        elif sys.platform == "darwin":
            os.system(f'open "{output_root}"')
        else:
            os.system(f'xdg-open "{output_root}"')


def run_app():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
