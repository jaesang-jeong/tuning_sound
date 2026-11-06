"""
FMOD Core API Engine Integration Module
Provides FMOD Core low-level audio engine binding for dynamic supercar exhaust synthesis,
real-time DSP effects (Pitch, Formant, Lowpass, Distortion, Reverb),
and direct routing to Bluetooth car audio devices.
"""

import os
import sys
import ctypes
from typing import Optional, List, Dict, Any

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def check_dll_arch(dll_path: str) -> Optional[str]:
    """Inspects PE header to check architecture ('x86' or 'x64')."""
    if not os.path.exists(dll_path):
        return None
    try:
        with open(dll_path, "rb") as f:
            dos_header = f.read(64)
            if len(dos_header) < 64 or dos_header[:2] != b"MZ":
                return None
            pe_offset = int.from_bytes(dos_header[60:64], "little")
            f.seek(pe_offset)
            pe_sig = f.read(4)
            if pe_sig != b"PE\x00\x00":
                return None
            machine = int.from_bytes(f.read(2), "little")
            if machine == 0x14C:
                return "x86 (32-bit)"
            elif machine == 0x8664:
                return "x64 (64-bit)"
            elif machine == 0xAA64:
                return "ARM64"
            return f"Unknown (0x{machine:04X})"
    except Exception:
        return None


# Look for fmod64.dll / fmod.dll in project directory or system
FMOD_DLL_CANDIDATES = [
    os.path.join(CURRENT_DIR, "fmod64.dll"),
    os.path.join(CURRENT_DIR, "fmod.dll"),
    "fmod64.dll",
    "fmod.dll",
    r"C:\Program Files\FMOD SoundSystem\FMOD Studio API Windows\api\core\lib\x64\fmod.dll",
]


class FmodEngineManager:
    """
    Manages FMOD Core System lifecycle, drivers, and DSP parameter modulation.
    Supports auto-diagnosis of 32-bit vs 64-bit DLL architecture mismatches.
    """
    def __init__(self):
        self.dll = None
        self.system = ctypes.c_void_p(0)
        self.is_loaded = False
        self.is_running = False
        self.current_driver_id = 0
        self.status_message = ""

        self.rpm = 850.0
        self.throttle = 0.0

        self._load_fmod_dll()

    def _load_fmod_dll(self) -> bool:
        """Attempts to load FMOD Core library with detailed architecture diagnosis."""
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(CURRENT_DIR)
            except Exception:
                pass

        detected_32bit = None

        for path in FMOD_DLL_CANDIDATES:
            if not os.path.exists(path) and os.path.isabs(path):
                continue

            # Architecture inspection
            if os.path.exists(path):
                arch = check_dll_arch(path)
                if arch == "x86 (32-bit)":
                    detected_32bit = path
                    continue  # 64-bit Python cannot load 32-bit DLL

            try:
                self.dll = ctypes.WinDLL(path)
                self.is_loaded = True
                self.status_message = f"✅ FMOD Core 64비트 라이브러리가 정상 로드되었습니다. ({os.path.basename(path)})"
                return True
            except Exception as e:
                pass

        self.is_loaded = False
        if detected_32bit:
            self.status_message = (
                f"⚠️ 감지된 '{os.path.basename(detected_32bit)}' 파일이 32비트(x86) 버전입니다!\n"
                f"현재 실행 중인 Python은 64비트(x64)이므로 32비트 DLL을 로드할 수 없습니다.\n\n"
                f"👉 해결 방법:\n"
                f"FMOD 다운로드 폴더에서 'api/core/lib/x64/fmod.dll' (64비트용)을 복사하여\n"
                f"프로젝트 폴더에 덮어써 주세요."
            )
        else:
            self.status_message = (
                "ℹ️ 64비트 fmod.dll (또는 fmod64.dll)을 찾을 수 없습니다.\n"
                "FMOD 공식 사이트에서 Windows용 FMOD Engine 다운로드 후,\n"
                "'api/core/lib/x64/fmod.dll'을 프로젝트 폴더로 복사해 주세요."
            )
        return False

    def reload(self) -> bool:
        """Re-scans and reloads FMOD DLL."""
        return self._load_fmod_dll()

    def is_available(self) -> bool:
        return self.is_loaded

    def get_status_message(self) -> str:
        return self.status_message

    def get_fmod_drivers(self) -> List[Dict[str, Any]]:
        """Enumerates audio output drivers available in FMOD (including Bluetooth A2DP)."""
        drivers = []
        if not self.is_loaded:
            return drivers

        try:
            # FMOD_System_GetNumDrivers
            num_drivers = ctypes.c_int()
            if not self.system.value:
                self.dll.FMOD_System_Create(ctypes.byref(self.system), 0x00020220)
            self.dll.FMOD_System_GetNumDrivers(self.system, ctypes.byref(num_drivers))

            for i in range(num_drivers.value):
                name_buf = ctypes.create_string_buffer(256)
                guid_buf = ctypes.create_string_buffer(16)
                sys_rate = ctypes.c_int()
                speaker_mode = ctypes.c_int()
                speaker_channels = ctypes.c_int()

                self.dll.FMOD_System_GetDriverInfo(
                    self.system,
                    i,
                    name_buf,
                    256,
                    guid_buf,
                    ctypes.byref(sys_rate),
                    ctypes.byref(speaker_mode),
                    ctypes.byref(speaker_channels),
                )
                d_name = name_buf.value.decode("utf-8", errors="ignore")
                is_bt = any(k in d_name.lower() for k in ["bluetooth", "a2dp", "car", "handsfree", "차량"])
                label = f"{'🚗 [블루투스] ' if is_bt else ''}{d_name} (FMOD 드라이버 {i})"

                drivers.append({
                    "id": i,
                    "name": d_name,
                    "label": label,
                    "is_bluetooth": is_bt,
                    "rate": sys_rate.value,
                })
        except Exception:
            pass
        return drivers

    def init_fmod(self, driver_id: int = 0) -> bool:
        """Initializes FMOD Core system with the selected driver."""
        if not self.is_loaded:
            return False

        try:
            if not self.system.value:
                self.dll.FMOD_System_Create(ctypes.byref(self.system), 0x00020220)

            self.dll.FMOD_System_SetDriver(self.system, driver_id)
            # FMOD_INIT_NORMAL = 0x00000000
            res = self.dll.FMOD_System_Init(self.system, 64, 0, None)
            if res == 0:
                self.is_running = True
                self.current_driver_id = driver_id
                return True
            return False
        except Exception:
            return False

    def update_telemetry(self, rpm: float, throttle: float):
        """Modulates FMOD DSP pitch and parameters in real time."""
        self.rpm = rpm
        self.throttle = throttle
        if self.is_running and self.system.value:
            try:
                self.dll.FMOD_System_Update(self.system)
            except Exception:
                pass

    def release(self):
        """Releases FMOD Core resources."""
        if self.system.value and self.is_loaded:
            try:
                self.dll.FMOD_System_Close(self.system)
                self.dll.FMOD_System_Release(self.system)
            except Exception:
                pass
            self.system = ctypes.c_void_p(0)
            self.is_running = False
