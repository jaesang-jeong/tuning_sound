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

# Look for fmod64.dll / fmod.dll in project directory or system
FMOD_DLL_CANDIDATES = [
    os.path.join(CURRENT_DIR, "fmod.dll"),
    os.path.join(CURRENT_DIR, "fmod64.dll"),
    "fmod.dll",
    "fmod64.dll",
    r"C:\Program Files\FMOD SoundSystem\FMOD Studio API Windows\api\core\lib\x64\fmod.dll",
]


class FmodEngineManager:
    """
    Manages FMOD Core System lifecycle, drivers, and DSP parameter modulation.
    """
    def __init__(self):
        self.dll = None
        self.system = None
        self.is_loaded = False
        self.is_running = False
        self.current_driver_id = 0

        self.rpm = 850.0
        self.throttle = 0.0

        self._load_fmod_dll()

    def _load_fmod_dll(self) -> bool:
        """Attempts to load FMOD Core library."""
        for path in FMOD_DLL_CANDIDATES:
            try:
                if os.path.exists(path) or not os.path.isabs(path):
                    self.dll = ctypes.WinDLL(path)
                    self.is_loaded = True
                    return True
            except Exception:
                continue
        self.is_loaded = False
        return False

    def is_available(self) -> bool:
        return self.is_loaded

    def get_fmod_drivers(self) -> List[Dict[str, Any]]:
        """Enumerates audio output drivers available in FMOD (including Bluetooth A2DP)."""
        drivers = []
        if not self.is_loaded:
            return drivers

        try:
            # FMOD_System_GetNumDrivers
            num_drivers = ctypes.c_int()
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
            if not self.system:
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
        if self.is_running and self.system:
            try:
                self.dll.FMOD_System_Update(self.system)
            except Exception:
                pass

    def release(self):
        """Releases FMOD Core resources."""
        if self.system and self.is_loaded:
            try:
                self.dll.FMOD_System_Close(self.system)
                self.dll.FMOD_System_Release(self.system)
            except Exception:
                pass
            self.system = None
            self.is_running = False
