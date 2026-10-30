"""Strata process manager for starting and stopping the local server on demand."""

import contextlib
import logging
import os
import subprocess
import time
from typing import Generator
import httpx

logger = logging.getLogger(__name__)

DEFAULT_STRATA_SCRIPT = "/var/home/ultraxav/projects/strata/run-iq2_xs.sh"
DEFAULT_BASE_URL = "http://127.0.0.1:8080/v1"


class StrataServerManager:
    """Manages the lifecycle of the local Strata inference server."""

    def __init__(
        self,
        launch_script: str = DEFAULT_STRATA_SCRIPT,
        base_url: str = DEFAULT_BASE_URL,
        startup_timeout_s: float = 60.0,
    ):
        self.launch_script = launch_script
        self.base_url = base_url.rstrip("/")
        self.startup_timeout_s = startup_timeout_s
        self._proc: subprocess.Popen | None = None

    def is_running(self) -> bool:
        """Check if the Strata server endpoint responds."""
        try:
            with httpx.Client(timeout=1.0) as client:
                res = client.get(f"{self.base_url}/models")
                return res.status_code == 200
        except Exception:
            return False

    def start(self) -> bool:
        """Start the Strata server if not already running, waiting until ready."""
        if self.is_running():
            logger.info("Strata server is already running.")
            return True

        if not os.path.exists(self.launch_script):
            raise FileNotFoundError(f"Strata launch script not found: {self.launch_script}")

        logger.info(f"Starting Strata server via {self.launch_script}...")
        self._proc = subprocess.Popen(
            [self.launch_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid if hasattr(os, "setsid") else None,
        )

        t0 = time.time()
        while time.time() - t0 < self.startup_timeout_s:
            if self._proc.poll() is not None:
                raise RuntimeError(
                    f"Strata server process exited unexpectedly with code {self._proc.returncode}"
                )
            if self.is_running():
                logger.info(f"Strata server is ready (took {time.time() - t0:.1f}s).")
                return True
            time.sleep(1.0)

        self.stop()
        raise TimeoutError(f"Strata server failed to become ready within {self.startup_timeout_s}s.")

    def stop(self) -> None:
        """Stop the Strata server process."""
        logger.info("Stopping Strata server...")
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=10.0)
            except Exception:
                try:
                    self._proc.kill()
                    self._proc.wait(timeout=5.0)
                except Exception:
                    pass
            self._proc = None

        # Clean up any lingering process listening on 8080 or matching run-iq2_xs / strata
        try:
            subprocess.run(
                ["pkill", "-f", "run-iq2_xs.sh"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            subprocess.run(
                ["pkill", "-f", "strata-iq2_xs.json"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    @contextlib.contextmanager
    def session(self) -> Generator["StrataServerManager", None, None]:
        """Context manager to ensure Strata runs only for the duration of the block."""
        was_already_running = self.is_running()
        if not was_already_running:
            self.start()
        try:
            yield self
        finally:
            if not was_already_running:
                self.stop()

