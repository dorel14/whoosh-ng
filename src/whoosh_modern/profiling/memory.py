"""Memory profiling for index operations."""

from __future__ import annotations

import os
import sys


def _get_process_memory_mb() -> float:
    """Return current process RSS memory in MB."""
    try:
        import psutil  # pyright: ignore[reportMissingImports]

        return float(psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024))
    except ImportError:
        pass

    if sys.platform == "win32":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            mem = MEMORYSTATUSEX()
            mem.dwLength = ctypes.sizeof(mem)
            if kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
                return float(mem.ullTotalPhys / (1024 * 1024) - mem.ullAvailPhys / (1024 * 1024))
        except Exception:
            pass

    try:
        with open("/proc/self/status", encoding="utf-8") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except Exception:
        pass

    return 0.0


class MemoryProfiler:
    """Measures memory usage during indexing."""

    def __init__(self) -> None:
        self.start_mb: float = 0.0
        self.peak_mb: float = 0.0
        self.end_mb: float = 0.0
        self._samples: list[float] = []
        self._enabled: bool = True

    def start(self) -> None:
        self.start_mb = _get_process_memory_mb()
        self.peak_mb = self.start_mb
        self._samples = [self.start_mb]

    def sample(self) -> None:
        mb = _get_process_memory_mb()
        self._samples.append(mb)
        if mb > self.peak_mb:
            self.peak_mb = mb

    def stop(self) -> None:
        self.end_mb = _get_process_memory_mb()
        self._samples.append(self.end_mb)

    @property
    def delta_mb(self) -> float:
        return self.end_mb - self.start_mb

    @property
    def peak_delta_mb(self) -> float:
        return self.peak_mb - self.start_mb

    def report(self) -> str:
        return (
            f"Memory Start : {self.start_mb:.1f} MB\n"
            f"Memory Peak  : {self.peak_mb:.1f} MB\n"
            f"Memory End   : {self.end_mb:.1f} MB\n"
            f"Delta        : {self.delta_mb:+.1f} MB\n"
            f"Peak Delta   : {self.peak_delta_mb:+.1f} MB"
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "start_mb": round(self.start_mb, 1),
            "peak_mb": round(self.peak_mb, 1),
            "end_mb": round(self.end_mb, 1),
            "delta_mb": round(self.delta_mb, 1),
            "peak_delta_mb": round(self.peak_delta_mb, 1),
        }
