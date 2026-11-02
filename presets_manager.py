"""
Engine Presets Manager Module
Stores and loads sound tuning configurations, including default presets for:
- American Muscle V8 (6.2L Supercharged)
- Porsche 911 GT3 (Boxer-6)
- Ferrari F8 / 458 (Flat-plane V8)
- Maserati GranTurismo (Cross-plane V8)
- Lamborghini Huracán (V10)
"""

import json
import os
from typing import Dict, Any

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PRESETS_FILE = os.path.join(CURRENT_DIR, "supercar_sound_presets.json")

DEFAULT_PRESETS: Dict[str, Dict[str, Any]] = {
    "아메리칸 머슬카 V8 (6.2L Supercharged)": {
        "model_key": "muscle_v8",
        "description": "6.2L 헤미/콜벳 V8. 거친 아이들 캠 롭(Cam Lope), 심장을 울리는 서브우퍼급 저음 럼블 및 슈퍼차저 휘슬.",
        "idle_rpm": 780,
        "max_rpm": 6800,
        "cylinders": 8,
        "bass_boost": 1.7,
        "mid_punch": 1.3,
        "treble_scream": 0.8,
        "valve_open": True,
        "pop_and_bang": True,
        "pop_intensity": 1.5,
        "distortion": 0.45,
        "supercharger": True,
        "master_volume": 0.90,
    },
    "포르쉐 911 GT3 (Flat-6)": {
        "model_key": "porsche_gt3",
        "description": "4.0L 수평대향 6기통 9,000 RPM 박서. 앙칼진 금속성 고회전 비명과 독특한 박서 비트.",
        "idle_rpm": 850,
        "max_rpm": 9000,
        "cylinders": 6,
        "bass_boost": 0.9,
        "mid_punch": 1.2,
        "treble_scream": 1.5,
        "valve_open": True,
        "pop_and_bang": True,
        "pop_intensity": 1.2,
        "distortion": 0.50,
        "supercharger": False,
        "master_volume": 0.85,
    },
    "페라리 F8 / 458 (Flat-plane V8)": {
        "model_key": "ferrari_f8",
        "description": "180도 플랫 크랭크 8기통. F1 머신처럼 날카롭게 찢어지는 초고주파 스크리머 톤.",
        "idle_rpm": 900,
        "max_rpm": 9000,
        "cylinders": 8,
        "bass_boost": 0.7,
        "mid_punch": 1.1,
        "treble_scream": 1.7,
        "valve_open": True,
        "pop_and_bang": True,
        "pop_intensity": 1.1,
        "distortion": 0.40,
        "supercharger": False,
        "master_volume": 0.85,
    },
    "마세라티 그란투리스모 (Cross-plane V8)": {
        "model_key": "maserati_gt",
        "description": "4.7L 크로스플레인 V8. 가슴을 울리는 깊은 바리톤 저음 럼블과 폭발적인 디셀 버블.",
        "idle_rpm": 750,
        "max_rpm": 7500,
        "cylinders": 8,
        "bass_boost": 1.5,
        "mid_punch": 1.3,
        "treble_scream": 0.9,
        "valve_open": True,
        "pop_and_bang": True,
        "pop_intensity": 1.6,
        "distortion": 0.55,
        "supercharger": False,
        "master_volume": 0.90,
    },
    "람보르기니 우라칸 (V10)": {
        "model_key": "lamborghini_v10",
        "description": "5.2L 자연흡기 V10. 맹렬하고 공격적인 맹수 울음소리와 날카로운 백파이어 팝.",
        "idle_rpm": 850,
        "max_rpm": 8800,
        "cylinders": 10,
        "bass_boost": 1.1,
        "mid_punch": 1.4,
        "treble_scream": 1.4,
        "valve_open": True,
        "pop_and_bang": True,
        "pop_intensity": 1.4,
        "distortion": 0.50,
        "supercharger": False,
        "master_volume": 0.88,
    },
}


class PresetsManager:
    def __init__(self, filepath: str = PRESETS_FILE):
        self.filepath = filepath
        self.presets = dict(DEFAULT_PRESETS)
        self.load()

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.presets.update(data)
            except Exception as e:
                print(f"Error loading presets: {e}")
        else:
            self.save()

    def save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.presets, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving presets: {e}")

    def get_preset(self, name: str) -> Dict[str, Any]:
        return self.presets.get(name, DEFAULT_PRESETS["아메리칸 머슬카 V8 (6.2L Supercharged)"])

    def set_preset(self, name: str, settings: Dict[str, Any]):
        self.presets[name] = settings
        self.save()

    def delete_preset(self, name: str):
        if name in self.presets and name not in DEFAULT_PRESETS:
            del self.presets[name]
            self.save()

    def list_preset_names(self) -> list[str]:
        return list(self.presets.keys())
