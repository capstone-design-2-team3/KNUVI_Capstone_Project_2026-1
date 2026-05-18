from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot


def quote_cmd(cmd: list[str]) -> str:
    return " ".join(f'"{c}"' if " " in c else c for c in cmd)


class PipelineWorker(QObject):
    log = Signal(str)
    scene_started = Signal(str)
    scene_finished = Signal(str, bool)
    all_finished = Signal(bool)

    def __init__(
        self,
        project_root: Path,
        scenes: list[str],
        snow_root: str,
        output_root: str,
        raw_output_root: str,
        mwformer_repo: str,
        backbone_path: str,
        style_filter_path: str,
        device: str = "auto",
        batch_size: int = 1,
        num_workers: int = 0,
        max_side: int = 1024,
        size_multiple: int = 16,
        skip_mwformer: bool = False,
    ):
        super().__init__()
        self.project_root = Path(project_root)
        self.scenes = scenes
        self.snow_root = snow_root
        self.output_root = output_root
        self.raw_output_root = raw_output_root
        self.mwformer_repo = mwformer_repo
        self.backbone_path = backbone_path
        self.style_filter_path = style_filter_path
        self.device = device
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.max_side = max_side
        self.size_multiple = size_multiple
        self.skip_mwformer = skip_mwformer
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True

    def _run_command(self, cmd: list[str]) -> bool:
        self.log.emit("[COMMAND] " + quote_cmd(cmd))

        process = subprocess.Popen(
            cmd,
            cwd=str(self.project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        assert process.stdout is not None

        for line in process.stdout:
            self.log.emit(line.rstrip())

        process.wait()
        return process.returncode == 0

    @Slot()
    def run(self):
        overall_success = True

        for scene in self.scenes:
            if self._stop_requested:
                self.log.emit("[STOP] Stop requested. Remaining scenes skipped.")
                overall_success = False
                break

            self.scene_started.emit(scene)
            self.log.emit("")
            self.log.emit(f"========== Processing scene: {scene} ==========")

            input_dir = str(Path(self.snow_root) / scene / "input")
            output_dir = str(Path(self.output_root) / scene / "input")
            raw_output_dir = str(Path(self.raw_output_root) / scene)

            cmd = [
                sys.executable,
                "-u",
                "tools/run_refinement.py",
                "--input_dir", input_dir,
                "--output_dir", output_dir,
                "--mwformer_repo", self.mwformer_repo,
                "--backbone_path", self.backbone_path,
                "--style_filter_path", self.style_filter_path,
                "--raw_output_dir", raw_output_dir,
                "--device", self.device,
                "--batch_size", str(self.batch_size),
                "--num_workers", str(self.num_workers),
                "--max_side", str(self.max_side),
                "--size_multiple", str(self.size_multiple),
            ]

            if self.skip_mwformer:
                cmd.append("--skip_mwformer")

            success = self._run_command(cmd)
            self.scene_finished.emit(scene, success)

            if success:
                self.log.emit(f"[OK] Scene finished: {scene}")
            else:
                self.log.emit(f"[FAIL] Scene failed: {scene}")
                overall_success = False

        self.all_finished.emit(overall_success)


class CheckSetupWorker(QObject):
    log = Signal(str)
    finished = Signal(bool)

    def __init__(
        self,
        project_root: Path,
        input_dir: str,
        mwformer_repo: str,
        backbone_path: str,
        style_filter_path: str,
    ):
        super().__init__()
        self.project_root = Path(project_root)
        self.input_dir = input_dir
        self.mwformer_repo = mwformer_repo
        self.backbone_path = backbone_path
        self.style_filter_path = style_filter_path

    @Slot()
    def run(self):
        cmd = [
            sys.executable,
            "-u",
            "tools/check_mwformer_setup.py",
            "--input_dir", self.input_dir,
            "--mwformer_repo", self.mwformer_repo,
            "--backbone_path", self.backbone_path,
            "--style_filter_path", self.style_filter_path,
        ]

        self.log.emit("[COMMAND] " + quote_cmd(cmd))

        process = subprocess.Popen(
            cmd,
            cwd=str(self.project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        assert process.stdout is not None

        for line in process.stdout:
            self.log.emit(line.rstrip())

        process.wait()
        self.finished.emit(process.returncode == 0)
