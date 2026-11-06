"""
Supercar & Muscle Car Exhaust Sound Simulator & Cockpit (PySide6)
Professional Desktop GUI with:
  - PEAK PCAN-USB Pro Dual-Channel Interface & Live Raw CAN Sniffer
  - Bluetooth Car Audio (A2DP) Output Device Routing & Buffer Jitter Control
  - Hybrid Audio Engines: High-End Native DSP, FMOD Core API, Pure Data (Pd-vanilla)
  - Cockpit Cabin Interior & Exterior Tailpipe Views
  - GTA / Real-Game 3D Stereo Spatial Audio & Intake Induction Roar
"""

import sys
import os
import time
import threading
import numpy as np

from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QBrush, QLinearGradient
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QTabWidget,
    QLabel,
    QSlider,
    QPushButton,
    QComboBox,
    QCheckBox,
    QGroupBox,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QTextEdit,
    QFrame,
    QMessageBox,
)

from sound_engine import ExhaustSoundSynthesizer
from can_interface import VirtualVehicleSimulator, CanReceiver
from pcan_manager import PcanManager, PCAN_CHANNELS, CAR_BROADCAST_PRESETS
from fmod_engine import FmodEngineManager
from pd_bridge import PdBridgeManager
from presets_manager import PresetsManager


class CanSignalBridge(QObject):
    """Thread-safe Qt signal bridge between background CAN/Sim worker threads and PySide6 GUI."""
    sig_telemetry = Signal(float, float, float)
    sig_status = Signal(str, bool)
    sig_log = Signal(str)
    sig_generic_can = Signal(float, float, float)
    sig_sim_tick = Signal(float, float, float, int)


class WaveformWidget(QFrame):
    """Real-time sound waveform visualizer."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(70)
        self.waveform_data = np.zeros(256, dtype=np.float32)
        self.setStyleSheet("background-color: #121418; border: 1px solid #2b303a; border-radius: 6px;")

    def update_waveform(self, data: np.ndarray):
        if len(data) >= 256:
            step = len(data) // 256
            self.waveform_data = data[::step][:256]
        else:
            self.waveform_data = data
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        mid_y = height / 2.0

        # Center reference line
        pen_grid = QPen(QColor(40, 50, 65, 120), 1, Qt.DashLine)
        painter.setPen(pen_grid)
        painter.drawLine(0, int(mid_y), width, int(mid_y))

        # Waveform line
        pen = QPen(QColor(0, 220, 255), 2)
        painter.setPen(pen)

        points = []
        n = len(self.waveform_data)
        if n < 2:
            return

        for i in range(n):
            x = (i / (n - 1)) * width
            val = float(self.waveform_data[i])
            y = mid_y - (val * (height * 0.42))
            points.append((x, y))

        for i in range(len(points) - 1):
            painter.drawLine(int(points[i][0]), int(points[i][1]), int(points[i+1][0]), int(points[i+1][1]))


class ModernTachometer(QWidget):
    """Digital Tachometer & Cockpit Gauge Display."""
    def __init__(self, max_rpm=6800, parent=None):
        super().__init__(parent)
        self.rpm = 780.0
        self.max_rpm = max_rpm
        self.speed = 0.0
        self.gear = 1
        self.throttle = 0.0
        self.perspective = "exterior"
        self.source_label = "가상 시뮬레이터"
        self.setMinimumHeight(150)

    def set_max_rpm(self, max_rpm: float):
        self.max_rpm = max_rpm
        self.update()

    def set_perspective(self, perspective: str):
        self.perspective = perspective
        self.update()

    def set_source(self, label: str):
        self.source_label = label
        self.update()

    def set_data(self, rpm: float, throttle: float, speed: float, gear: int):
        self.rpm = rpm
        self.throttle = throttle
        self.speed = speed
        self.gear = gear
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        # Background card
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(16, 18, 24))
        painter.drawRoundedRect(0, 0, width, height, 12, 12)

        # Big RPM Number
        painter.setPen(QColor(240, 245, 255))
        font_rpm = QFont("Consolas", 34, QFont.Bold)
        painter.setFont(font_rpm)
        painter.drawText(24, 55, f"{int(self.rpm):05d}")

        painter.setFont(QFont("Arial", 11))
        painter.setPen(QColor(140, 150, 170))
        painter.drawText(160, 44, "RPM")

        # Gear Display Badge
        gear_rect_x = width - 110
        painter.setBrush(QColor(30, 36, 48))
        painter.setPen(QPen(QColor(60, 75, 100), 2))
        painter.drawRoundedRect(gear_rect_x, 14, 85, 70, 10, 10)

        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.setPen(QColor(120, 140, 170))
        painter.drawText(gear_rect_x + 28, 34, "GEAR")

        painter.setFont(QFont("Consolas", 26, QFont.Bold))
        painter.setPen(QColor(255, 180, 0))
        gear_str = "N" if self.gear == 0 else str(self.gear)
        painter.drawText(gear_rect_x + 32, 70, gear_str)

        # Speed and Throttle Stats
        painter.setFont(QFont("Consolas", 20, QFont.Bold))
        painter.setPen(QColor(0, 230, 255))
        painter.drawText(230, 52, f"{self.speed:5.1f} km/h")

        painter.setFont(QFont("Arial", 11))
        painter.setPen(QColor(150, 160, 180))
        painter.drawText(370, 50, f"부하: {int(self.throttle * 100)}%")

        # Perspective & Source Tags
        persp_text = "💺 실내(Cabin)" if self.perspective == "cabin" else "🏎️ 실외(Exterior)"
        persp_col = QColor(168, 85, 247) if self.perspective == "cabin" else QColor(34, 197, 94)
        painter.setFont(QFont("Arial", 11, QFont.Bold))
        painter.setPen(persp_col)
        painter.drawText(470, 50, persp_text)

        painter.setPen(QColor(56, 189, 248))
        painter.drawText(620, 50, f"📡 소스: {self.source_label}")

        # Dynamic Colored Tachometer Arc Bar
        bar_x = 24
        bar_y = 95
        bar_w = width - 48
        bar_h = 22

        painter.setBrush(QColor(25, 30, 40))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 6, 6)

        rpm_ratio = min(1.0, max(0.0, self.rpm / self.max_rpm))
        fill_w = int(bar_w * rpm_ratio)

        if fill_w > 0:
            gradient = QLinearGradient(bar_x, bar_y, bar_x + bar_w, bar_y)
            gradient.setColorAt(0.0, QColor(0, 180, 255))
            gradient.setColorAt(0.65, QColor(0, 255, 120))
            gradient.setColorAt(0.85, QColor(255, 190, 0))
            gradient.setColorAt(0.95, QColor(255, 30, 30))

            painter.setBrush(gradient)
            painter.drawRoundedRect(bar_x, bar_y, fill_w, bar_h, 6, 6)

        # Redline marker
        redline_x = bar_x + int(bar_w * 0.88)
        painter.setPen(QPen(QColor(255, 60, 60), 2))
        painter.drawLine(redline_x, bar_y - 3, redline_x, bar_y + bar_h + 3)


class ExhaustAppWindow(QMainWindow):
    """Main Application Window."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Supercar & Muscle Car Exhaust Cockpit (PCAN-USB Pro & Bluetooth Audio)")
        self.resize(1140, 920)
        self.setMinimumSize(1020, 820)

        # 1. Initialize Engines & Hardware Managers
        self.synth = ExhaustSoundSynthesizer(sample_rate=44100, buffer_size=1024)
        self.preset_mgr = PresetsManager()
        self.sim = VirtualVehicleSimulator()
        self.can_rx = CanReceiver()
        self.pcan_mgr = PcanManager()
        self.can_bridge = CanSignalBridge()
        self.fmod_mgr = FmodEngineManager()
        self.pd_bridge = PdBridgeManager()

        # Engine selection: "NATIVE_DSP", "FMOD", or "PURE_DATA"
        self.active_audio_engine = "NATIVE_DSP"
        self.current_mode = "TUNING"
        self.drive_source = "SIMULATOR"  # "SIMULATOR", "PCAN_PRO", or "GENERIC_CAN"

        self._init_ui()
        self._apply_dark_theme()
        self._setup_connections()

        # Refresh Audio Output Devices List (Bluetooth Car Audio)
        self._refresh_audio_devices()

        # Real-time UI refresh timer (30 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_ui_tick)
        self.timer.start(33)

        # Start default sound engine with Muscle V8 preset
        self.load_preset_to_ui("아메리칸 머슬카 V8 (6.2L Supercharged)")
        self.synth.start()
        self.btn_sound_toggle.setText("🔊 사운드 ON (작동중)")
        self.btn_sound_toggle.setChecked(True)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # 1. Top Header Bar (Global Sound, Bluetooth Audio Routing & Perspective)
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #171b22; border: 1px solid #2a313d; border-radius: 8px; padding: 6px;")
        header_layout = QHBoxLayout(header_frame)

        self.btn_sound_toggle = QPushButton("🔊 사운드 ON")
        self.btn_sound_toggle.setCheckable(True)
        self.btn_sound_toggle.setStyleSheet("""
            QPushButton { background-color: #00875a; color: white; font-weight: bold; font-size: 13px; padding: 8px 14px; border-radius: 6px; }
            QPushButton:!checked { background-color: #4b5563; }
        """)

        # Perspective Switcher
        persp_label = QLabel("관점:")
        persp_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.btn_persp_exterior = QPushButton("🏎️ 실외")
        self.btn_persp_exterior.setCheckable(True)
        self.btn_persp_exterior.setChecked(True)
        self.btn_persp_exterior.setStyleSheet("""
            QPushButton { background-color: #059669; color: white; font-weight: bold; padding: 6px 12px; border-radius: 6px; font-size: 11px; }
            QPushButton:!checked { background-color: #27272a; color: #9ca3af; }
        """)

        self.btn_persp_cabin = QPushButton("💺 운전석 실내")
        self.btn_persp_cabin.setCheckable(True)
        self.btn_persp_cabin.setStyleSheet("""
            QPushButton { background-color: #8b5cf6; color: white; font-weight: bold; padding: 6px 12px; border-radius: 6px; font-size: 11px; }
            QPushButton:!checked { background-color: #27272a; color: #9ca3af; }
        """)

        self.btn_persp_exterior.clicked.connect(lambda: self._set_perspective("exterior"))
        self.btn_persp_cabin.clicked.connect(lambda: self._set_perspective("cabin"))

        # Audio Output Device Selector (Bluetooth Car Audio)
        dev_label = QLabel("출력 장치:")
        dev_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.combo_audio_dev = QComboBox()
        self.combo_audio_dev.setMinimumWidth(240)
        self.combo_audio_dev.currentIndexChanged.connect(self._on_audio_device_changed)

        btn_refresh_dev = QPushButton("🔄")
        btn_refresh_dev.setToolTip("오디오/블루투스 출력 장치 새로고침")
        btn_refresh_dev.clicked.connect(self._refresh_audio_devices)

        # Buffer size selector (for Bluetooth latency/jitter tuning)
        self.combo_buffer_size = QComboBox()
        self.combo_buffer_size.addItems(["1024 샘플 (기본)", "512 샘플 (초저지연)", "2048 샘플 (블루투스 안정)", "4096 샘플 (최대 버퍼)"])
        self.combo_buffer_size.currentIndexChanged.connect(self._on_buffer_size_changed)

        # Volume
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(90)
        self.vol_slider.setFixedWidth(100)
        self.lbl_vol_val = QLabel("90%")

        self.lbl_model_badge = QLabel("아메리칸 머슬카 V8 (6.2L Supercharged)")
        self.lbl_model_badge.setStyleSheet("color: #00e5ff; font-weight: bold; font-size: 13px; background-color: #0d2838; padding: 5px 12px; border-radius: 6px; border: 1px solid #00a0b0;")

        header_layout.addWidget(self.btn_sound_toggle)
        header_layout.addSpacing(10)
        header_layout.addWidget(persp_label)
        header_layout.addWidget(self.btn_persp_exterior)
        header_layout.addWidget(self.btn_persp_cabin)
        header_layout.addSpacing(12)
        header_layout.addWidget(dev_label)
        header_layout.addWidget(self.combo_audio_dev)
        header_layout.addWidget(btn_refresh_dev)
        header_layout.addWidget(self.combo_buffer_size)
        header_layout.addSpacing(10)
        header_layout.addWidget(QLabel("볼륨:"))
        header_layout.addWidget(self.vol_slider)
        header_layout.addWidget(self.lbl_vol_val)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_model_badge)

        main_layout.addWidget(header_frame)

        # 2. Cockpit Tachometer Display
        self.tachometer = ModernTachometer(max_rpm=6800)
        main_layout.addWidget(self.tachometer)

        # 3. Waveform Oscilloscope Display
        self.waveform_widget = WaveformWidget()
        main_layout.addWidget(self.waveform_widget)

        # 4. Mode Selection Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #2b303c; background-color: #161920; border-radius: 8px; }
            QTabBar::tab { background: #20242f; color: #a0aec0; padding: 10px 24px; font-weight: bold; font-size: 13px; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 4px; }
            QTabBar::tab:selected { background: #0284c7; color: white; }
        """)

        self.tab_tuning = QWidget()
        self.tab_drive = QWidget()
        self.tab_pcan = QWidget()
        self.tab_engine_choice = QWidget()

        self._build_tuning_tab()
        self._build_drive_tab()
        self._build_pcan_tab()
        self._build_engine_choice_tab()

        self.tabs.addTab(self.tab_tuning, "🎛️ 튜닝 모드 (Tuning)")
        self.tabs.addTab(self.tab_drive, "🏎️ 드라이브 모드 (Drive)")
        self.tabs.addTab(self.tab_pcan, "🔌 PCAN-USB Pro 연동 (차량 연결)")
        self.tabs.addTab(self.tab_engine_choice, "⚙️ 오디오 엔진 설정 (FMOD / Pure Data)")

        main_layout.addWidget(self.tabs, stretch=1)

    def _build_tuning_tab(self):
        layout = QVBoxLayout(self.tab_tuning)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        # Top Row: Preset Selection & Quick Switch Buttons
        preset_box = QGroupBox("슈퍼카 & 머슬카 프리셋 선택 & 관리")
        preset_layout = QHBoxLayout(preset_box)

        self.combo_presets = QComboBox()
        self.combo_presets.addItems(self.preset_mgr.list_preset_names())
        self.combo_presets.setMinimumWidth(280)

        btn_load_preset = QPushButton("프리셋 적용")
        btn_load_preset.clicked.connect(self._on_preset_selected)

        self.txt_new_preset = QLineEdit()
        self.txt_new_preset.setPlaceholderText("새 프리셋 이름 입력...")
        btn_save_preset = QPushButton("현재 세팅 저장")
        btn_save_preset.clicked.connect(self._on_save_preset)

        preset_layout.addWidget(QLabel("프리셋:"))
        preset_layout.addWidget(self.combo_presets)
        preset_layout.addWidget(btn_load_preset)
        preset_layout.addSpacing(25)
        preset_layout.addWidget(self.txt_new_preset)
        preset_layout.addWidget(btn_save_preset)
        layout.addWidget(preset_box)

        # Quick Cars Row (5 Iconic Engines)
        quick_layout = QHBoxLayout()
        quick_cars = [
            ("아메리칸 머슬카 V8 (6.2L Supercharged)", "#b91c1c"),
            ("포르쉐 911 GT3 (Flat-6)", "#0284c7"),
            ("페라리 F8 / 458 (Flat-plane V8)", "#dc2626"),
            ("마세라티 그란투리스모 (Cross-plane V8)", "#059669"),
            ("람보르기니 우라칸 (V10)", "#d97706"),
        ]
        for name, color in quick_cars:
            btn = QPushButton(f"⚡ {name}")
            btn.setStyleSheet(f"background-color: {color}; color: white; font-weight: bold; padding: 7px 10px; border-radius: 6px; font-size: 11px;")
            btn.clicked.connect(lambda checked=False, n=name: self.load_preset_to_ui(n))
            quick_layout.addWidget(btn)
        layout.addLayout(quick_layout)

        # Middle: RPM Slider & Dynamic Accelerator Pedal
        control_grid = QGridLayout()

        # RPM Slider
        lbl_rpm = QLabel("가상 RPM 제어 (Tuning Slider):")
        lbl_rpm.setFont(QFont("Arial", 11, QFont.Bold))
        self.slider_rpm = QSlider(Qt.Horizontal)
        self.slider_rpm.setRange(500, 9500)
        self.slider_rpm.setValue(780)
        self.lbl_rpm_disp = QLabel("780 RPM")
        self.lbl_rpm_disp.setFont(QFont("Consolas", 12, QFont.Bold))
        self.lbl_rpm_disp.setStyleSheet("color: #00e5ff;")

        control_grid.addWidget(lbl_rpm, 0, 0)
        control_grid.addWidget(self.slider_rpm, 0, 1)
        control_grid.addWidget(self.lbl_rpm_disp, 0, 2)

        # Throttle Slider
        lbl_throttle = QLabel("가상 부하 / 스로틀 (Engine Load):")
        lbl_throttle.setFont(QFont("Arial", 11, QFont.Bold))
        self.slider_throttle = QSlider(Qt.Horizontal)
        self.slider_throttle.setRange(0, 100)
        self.slider_throttle.setValue(0)
        self.lbl_throttle_disp = QLabel("0 %")
        self.lbl_throttle_disp.setFont(QFont("Consolas", 12, QFont.Bold))

        control_grid.addWidget(lbl_throttle, 1, 0)
        control_grid.addWidget(self.slider_throttle, 1, 1)
        control_grid.addWidget(self.lbl_throttle_disp, 1, 2)

        # Dynamic Pedal Button
        self.btn_pedal = QPushButton("🏎️ 가상 가속 페달 (누르고 있으면 풀악셀 급상승, 떼면 팝앤뱅/백파이어 폭발!)")
        self.btn_pedal.setStyleSheet("""
            QPushButton { background-color: #2563eb; color: white; font-weight: bold; font-size: 14px; padding: 12px; border-radius: 8px; }
            QPushButton:pressed { background-color: #ef4444; }
        """)
        self.btn_pedal.pressed.connect(self._on_pedal_down)
        self.btn_pedal.released.connect(self._on_pedal_up)
        control_grid.addWidget(self.btn_pedal, 2, 0, 1, 3)

        layout.addLayout(control_grid)

        # Bottom: Detailed Acoustic Parameters
        tuning_params_box = QGroupBox("배기음 물리/음향 & GTA 실사 3D 공간 음향 세부 튜닝")
        t_layout = QGridLayout(tuning_params_box)

        # EQ Low / Mid / High
        t_layout.addWidget(QLabel("저음 서브 럼블 (Bass Rumble):"), 0, 0)
        self.slider_bass = QSlider(Qt.Horizontal)
        self.slider_bass.setRange(20, 300)
        self.slider_bass.setValue(170)
        self.lbl_bass_disp = QLabel("1.7x")
        t_layout.addWidget(self.slider_bass, 0, 1)
        t_layout.addWidget(self.lbl_bass_disp, 0, 2)

        t_layout.addWidget(QLabel("중음 배기 맥동 (Mid Body):"), 1, 0)
        self.slider_mid = QSlider(Qt.Horizontal)
        self.slider_mid.setRange(20, 250)
        self.slider_mid.setValue(130)
        self.lbl_mid_disp = QLabel("1.3x")
        t_layout.addWidget(self.slider_mid, 1, 1)
        t_layout.addWidget(self.lbl_mid_disp, 0, 2)

        t_layout.addWidget(QLabel("고음 비명 / 밸브 (High Screamer):"), 2, 0)
        self.slider_treble = QSlider(Qt.Horizontal)
        self.slider_treble.setRange(20, 250)
        self.slider_treble.setValue(80)
        self.lbl_treble_disp = QLabel("0.8x")
        t_layout.addWidget(self.slider_treble, 2, 1)
        t_layout.addWidget(self.lbl_treble_disp, 2, 2)

        # 3D Game & Cabin Special Controls
        t_layout.addWidget(QLabel("흡기 인덕션 로어 (Intake Roar):"), 0, 3)
        self.slider_intake = QSlider(Qt.Horizontal)
        self.slider_intake.setRange(0, 250)
        self.slider_intake.setValue(120)
        self.lbl_intake_disp = QLabel("1.2x")
        t_layout.addWidget(self.slider_intake, 0, 4)
        t_layout.addWidget(self.lbl_intake_disp, 0, 5)

        t_layout.addWidget(QLabel("GTA 3D 스테레오 입체폭 (Stereo Width):"), 1, 3)
        self.slider_stereo = QSlider(Qt.Horizontal)
        self.slider_stereo.setRange(0, 200)
        self.slider_stereo.setValue(130)
        self.lbl_stereo_disp = QLabel("1.3x")
        t_layout.addWidget(self.slider_stereo, 1, 4)
        t_layout.addWidget(self.lbl_stereo_disp, 1, 5)

        t_layout.addWidget(QLabel("실내 섀시 진동 붐 (Chassis Boom):"), 2, 3)
        self.slider_chassis = QSlider(Qt.Horizontal)
        self.slider_chassis.setRange(0, 250)
        self.slider_chassis.setValue(140)
        self.lbl_chassis_disp = QLabel("1.4x")
        t_layout.addWidget(self.slider_chassis, 2, 4)
        t_layout.addWidget(self.lbl_chassis_disp, 2, 5)

        # Toggles
        t_layout.addWidget(QLabel("배기관 거친 질감 (Saturation):"), 3, 0)
        self.slider_dist = QSlider(Qt.Horizontal)
        self.slider_dist.setRange(0, 100)
        self.slider_dist.setValue(45)
        self.lbl_dist_disp = QLabel("45%")
        t_layout.addWidget(self.slider_dist, 3, 1)
        t_layout.addWidget(self.lbl_dist_disp, 3, 2)

        toggles_layout = QHBoxLayout()
        self.chk_valve = QCheckBox("가변 배기 밸브 OPEN")
        self.chk_valve.setChecked(True)
        self.chk_valve.setFont(QFont("Arial", 10, QFont.Bold))

        self.chk_supercharger = QCheckBox("슈퍼차저 휘슬 (Whine)")
        self.chk_supercharger.setChecked(True)
        self.chk_supercharger.setFont(QFont("Arial", 10, QFont.Bold))

        self.chk_pop = QCheckBox("팝앤뱅 / 백파이어")
        self.chk_pop.setChecked(True)
        self.chk_pop.setFont(QFont("Arial", 10, QFont.Bold))

        self.slider_pop_intensity = QSlider(Qt.Horizontal)
        self.slider_pop_intensity.setRange(0, 250)
        self.slider_pop_intensity.setValue(150)
        self.slider_pop_intensity.setFixedWidth(90)

        toggles_layout.addWidget(self.chk_valve)
        toggles_layout.addSpacing(15)
        toggles_layout.addWidget(self.chk_supercharger)
        toggles_layout.addSpacing(15)
        toggles_layout.addWidget(self.chk_pop)
        toggles_layout.addWidget(QLabel("강도:"))
        toggles_layout.addWidget(self.slider_pop_intensity)
        toggles_layout.addStretch()

        t_layout.addLayout(toggles_layout, 3, 3, 1, 3)
        layout.addWidget(tuning_params_box)

    def _build_drive_tab(self):
        layout = QVBoxLayout(self.tab_drive)
        layout.setSpacing(14)
        layout.setContentsMargins(14, 14, 14, 14)

        # Drive Source Selector
        source_box = QGroupBox("드라이브 모드 입력 소스 선택")
        source_layout = QHBoxLayout(source_box)

        self.btn_src_sim = QPushButton("🎮 가상 주행 시뮬레이터 (내장 가상 DCT 7단)")
        self.btn_src_sim.setCheckable(True)
        self.btn_src_sim.setChecked(True)
        self.btn_src_sim.setStyleSheet("""
            QPushButton { background-color: #0284c7; color: white; font-weight: bold; font-size: 13px; padding: 10px 14px; border-radius: 6px; }
            QPushButton:!checked { background-color: #374151; color: #9ca3af; }
        """)

        self.btn_src_pcan = QPushButton("🔌 PEAK PCAN-USB Pro (실제 차량 CAN 포트)")
        self.btn_src_pcan.setCheckable(True)
        self.btn_src_pcan.setStyleSheet("""
            QPushButton { background-color: #059669; color: white; font-weight: bold; font-size: 13px; padding: 10px 14px; border-radius: 6px; }
            QPushButton:!checked { background-color: #374151; color: #9ca3af; }
        """)

        self.btn_src_can = QPushButton("🚗 기타 일반 CAN (Virtual / SLCAN / Serial)")
        self.btn_src_can.setCheckable(True)
        self.btn_src_can.setStyleSheet("""
            QPushButton { background-color: #d97706; color: white; font-weight: bold; font-size: 13px; padding: 10px 14px; border-radius: 6px; }
            QPushButton:!checked { background-color: #374151; color: #9ca3af; }
        """)

        self.btn_src_sim.clicked.connect(lambda: self._set_drive_source("SIMULATOR"))
        self.btn_src_pcan.clicked.connect(lambda: self._set_drive_source("PCAN_PRO"))
        self.btn_src_can.clicked.connect(lambda: self._set_drive_source("GENERIC_CAN"))

        source_layout.addWidget(self.btn_src_sim)
        source_layout.addWidget(self.btn_src_pcan)
        source_layout.addWidget(self.btn_src_can)
        layout.addWidget(source_box)

        # Virtual Driving Simulator Controls
        self.panel_sim = QGroupBox("가상 차량 주행 조작 콘솔 (DCT 7단 자동 변속)")
        sim_layout = QGridLayout(self.panel_sim)

        sim_layout.addWidget(QLabel("가속 페달 (Gas):"), 0, 0)
        self.sim_slider_gas = QSlider(Qt.Horizontal)
        self.sim_slider_gas.setRange(0, 100)
        self.sim_slider_gas.setValue(0)
        self.lbl_sim_gas = QLabel("0%")
        sim_layout.addWidget(self.sim_slider_gas, 0, 1)
        sim_layout.addWidget(self.lbl_sim_gas, 0, 2)

        sim_layout.addWidget(QLabel("브레이크 (Brake):"), 1, 0)
        self.sim_slider_brake = QSlider(Qt.Horizontal)
        self.sim_slider_brake.setRange(0, 100)
        self.sim_slider_brake.setValue(0)
        self.lbl_sim_brake = QLabel("0%")
        sim_layout.addWidget(self.sim_slider_brake, 1, 1)
        sim_layout.addWidget(self.lbl_sim_brake, 1, 2)

        sim_btn_layout = QHBoxLayout()
        self.btn_sim_full_gas = QPushButton("🔥 풀 악셀 가속 (Launch / WOT)")
        self.btn_sim_full_gas.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; padding: 12px; border-radius: 6px;")
        self.btn_sim_full_gas.pressed.connect(lambda: self.sim_slider_gas.setValue(100))
        self.btn_sim_full_gas.released.connect(lambda: self.sim_slider_gas.setValue(0))

        self.btn_sim_coasting = QPushButton("💨 엑셀 오프 (Coasting & Crackle)")
        self.btn_sim_coasting.setStyleSheet("background-color: #4b5563; color: white; font-weight: bold; padding: 12px; border-radius: 6px;")
        self.btn_sim_coasting.clicked.connect(lambda: self.sim_slider_gas.setValue(0))

        self.btn_sim_neutral = QPushButton("⚙️ N단 후까시 / 주행 모드 전환")
        self.btn_sim_neutral.setCheckable(True)
        self.btn_sim_neutral.setStyleSheet("""
            QPushButton { background-color: #6366f1; color: white; font-weight: bold; padding: 12px; border-radius: 6px; }
            QPushButton:checked { background-color: #a855f7; }
        """)
        self.btn_sim_neutral.toggled.connect(self._on_sim_neutral_toggled)

        sim_btn_layout.addWidget(self.btn_sim_full_gas)
        sim_btn_layout.addWidget(self.btn_sim_coasting)
        sim_btn_layout.addWidget(self.btn_sim_neutral)
        sim_layout.addLayout(sim_btn_layout, 2, 0, 1, 3)

        layout.addWidget(self.panel_sim)

        # Real Vehicle Status Panel
        self.panel_veh_status = QGroupBox("실제 차량 CAN 수신 텔레메트리 상태")
        veh_layout = QVBoxLayout(self.panel_veh_status)
        self.lbl_veh_info = QLabel("연결 상태: 대기 중 ('PCAN-USB Pro 연동' 탭에서 연결을 시작하세요)")
        self.lbl_veh_info.setStyleSheet("color: #38bdf8; font-size: 13px; font-weight: bold;")
        self.lbl_veh_telemetry = QLabel("수신 프레임: 0 msgs | RPM: 0 | 스로틀: 0% | 차속: 0 km/h")
        self.lbl_veh_telemetry.setFont(QFont("Consolas", 12))
        veh_layout.addWidget(self.lbl_veh_info)
        veh_layout.addWidget(self.lbl_veh_telemetry)
        layout.addWidget(self.panel_veh_status)

        layout.addStretch()

    def _build_pcan_tab(self):
        """Dedicated PEAK PCAN-USB Pro management & live packet sniffer tab."""
        layout = QVBoxLayout(self.tab_pcan)
        layout.setSpacing(12)
        layout.setContentsMargins(14, 14, 14, 14)

        # 1. Informational Banner explaining Read-Only 10ms Mode
        info_banner = QLabel(
            "⚡ <b>10ms(100Hz) 초고속 Read-Only 무명령 패시브 모드 (Listen-Only)</b><br>"
            "차량 CAN 버스에 TX 요청을 보내지 않고, ECU가 계기판/변속기용으로 브로드캐스트하는 프레임을 순수 수신합니다.<br>"
            "• <b>핵심 장점</b>: 지연 0ms(OBD 대비 3~5배 빠름), 차량 ECU 간섭 0%, <b>OBD2 미연결 상태에서도 프로그램 절대 다운 없음</b>"
        )
        info_banner.setStyleSheet("background-color: #0d2818; color: #34d399; border: 1px solid #059669; border-radius: 6px; padding: 10px; font-size: 12px; line-height: 1.4;")
        layout.addWidget(info_banner)

        box_pcan = QGroupBox("PEAK PCAN-USB Pro 어댑터 연결 및 프로토콜 설정")
        p_layout = QGridLayout(box_pcan)
        p_layout.setSpacing(10)

        # Row 0: Channel & Scan
        p_layout.addWidget(QLabel("PCAN 채널:"), 0, 0)
        self.combo_pcan_ch = QComboBox()
        self.combo_pcan_ch.addItems(list(PCAN_CHANNELS.keys()))
        p_layout.addWidget(self.combo_pcan_ch, 0, 1)

        btn_rescan_pcan = QPushButton("🔍 하드웨어 검색")
        btn_rescan_pcan.clicked.connect(self._scan_pcan_devices)
        p_layout.addWidget(btn_rescan_pcan, 0, 2)

        # Row 1: Baudrate
        p_layout.addWidget(QLabel("통신 속도:"), 1, 0)
        self.combo_pcan_baud = QComboBox()
        self.combo_pcan_baud.addItems(["500000 (500 kbps - 차량 고속 CAN 표준)", "250000 (250 kbps)", "1000000 (1 Mbps)"])
        p_layout.addWidget(self.combo_pcan_baud, 1, 1, 1, 2)

        # Row 2: Protocol Mode (Read-Only Preset as Default)
        p_layout.addWidget(QLabel("프로토콜 모드:"), 2, 0)
        self.combo_pcan_mode = QComboBox()
        self.combo_pcan_mode.addItems([
            "READ_ONLY_PRESET (완성차 제조사 10ms 패시브 스니핑 - 권장)",
            "READ_ONLY_AUTO (자동 탐지 - 10~20ms RPM 프레임 자동 감지)",
            "READ_ONLY_CUSTOM (사용자 지정 CAN ID 패시브)",
            "OBD2_POLL (표준 능동 쿼리 PID 0x0C - 차 시동 켜짐 필요)"
        ])
        self.combo_pcan_mode.currentIndexChanged.connect(self._on_pcan_mode_changed)
        p_layout.addWidget(self.combo_pcan_mode, 2, 1, 1, 2)

        # Row 3: Automaker Broadcast Presets
        p_layout.addWidget(QLabel("제조사 프리셋:"), 3, 0)
        self.combo_pcan_preset = QComboBox()
        for p_name, p_info in CAR_BROADCAST_PRESETS.items():
            self.combo_pcan_preset.addItem(f"{p_name} - {p_info['description']}", userData=p_name)
        p_layout.addWidget(self.combo_pcan_preset, 3, 1, 1, 2)

        # Row 4: Custom CAN ID Config (Hidden/Disabled unless CUSTOM mode selected)
        p_layout.addWidget(QLabel("커스텀 ID 설정:"), 4, 0)
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("ID(Hex):"))
        self.spin_custom_can_id = QLineEdit("0x316")
        self.spin_custom_can_id.setMaximumWidth(70)
        self.spin_custom_can_id.setEnabled(False)
        custom_layout.addWidget(self.spin_custom_can_id)

        custom_layout.addWidget(QLabel("RPM바이트:"))
        self.spin_custom_rpm_byte = QSpinBox()
        self.spin_custom_rpm_byte.setRange(0, 6)
        self.spin_custom_rpm_byte.setValue(2)
        self.spin_custom_rpm_byte.setEnabled(False)
        custom_layout.addWidget(self.spin_custom_rpm_byte)

        custom_layout.addWidget(QLabel("스로틀바이트:"))
        self.spin_custom_th_byte = QSpinBox()
        self.spin_custom_th_byte.setRange(0, 7)
        self.spin_custom_th_byte.setValue(4)
        self.spin_custom_th_byte.setEnabled(False)
        custom_layout.addWidget(self.spin_custom_th_byte)
        custom_layout.addStretch()

        p_layout.addLayout(custom_layout, 4, 1, 1, 2)

        # Row 5: Action Buttons
        btn_pcan_layout = QHBoxLayout()
        self.btn_pcan_connect = QPushButton("🔌 PCAN-USB Pro 연결")
        self.btn_pcan_connect.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 10px 20px; border-radius: 6px;")
        self.btn_pcan_connect.clicked.connect(self._on_pcan_connect_clicked)

        self.btn_pcan_disconnect = QPushButton("연결 해제")
        self.btn_pcan_disconnect.setStyleSheet("background-color: #4b5563; color: white; padding: 10px 20px; border-radius: 6px;")
        self.btn_pcan_disconnect.clicked.connect(self._on_pcan_disconnect_clicked)
        self.btn_pcan_disconnect.setEnabled(False)

        btn_pcan_layout.addWidget(self.btn_pcan_connect)
        btn_pcan_layout.addWidget(self.btn_pcan_disconnect)
        btn_pcan_layout.addStretch()
        p_layout.addLayout(btn_pcan_layout, 5, 0, 1, 3)

        layout.addWidget(box_pcan)

        # Live Raw CAN Packet Monitor
        box_sniffer = QGroupBox("실시간 CAN 버스 패킷 모니터 (Raw Frame Sniffer)")
        s_layout = QVBoxLayout(box_sniffer)
        self.txt_pcan_log = QTextEdit()
        self.txt_pcan_log.setReadOnly(True)
        self.txt_pcan_log.setMaximumHeight(180)
        self.txt_pcan_log.setFont(QFont("Consolas", 10))
        self.txt_pcan_log.setStyleSheet("background-color: #0d1117; color: #38bdf8; border: 1px solid #30363d;")

        btn_clear_log = QPushButton("로그 지우기")
        btn_clear_log.clicked.connect(lambda: self.txt_pcan_log.clear())

        s_layout.addWidget(self.txt_pcan_log)
        s_layout.addWidget(btn_clear_log)
        layout.addWidget(box_sniffer)

        layout.addStretch()

    def _build_engine_choice_tab(self):
        """Audio Engine Selector: High-End Native DSP, FMOD Core, or Pure Data."""
        layout = QVBoxLayout(self.tab_engine_choice)
        layout.setSpacing(14)
        layout.setContentsMargins(14, 14, 14, 14)

        choice_box = QGroupBox("오디오 렌더링 백엔드 엔진 선택")
        c_layout = QVBoxLayout(choice_box)

        self.combo_audio_backend = QComboBox()
        self.combo_audio_backend.addItems([
            "⚡ High-End Native DSP (3D 입체 음장 & 실내/실외 뷰 지원 - 권장)",
            "🎮 FMOD Core API (AAA 상용 레이싱 게임 오디오 엔진)",
            "🎛️ Pure Data (Pd-vanilla - 오픈소스 모듈러 패치)",
        ])
        self.combo_audio_backend.currentIndexChanged.connect(self._on_audio_backend_changed)
        c_layout.addWidget(self.combo_audio_backend)

        self.lbl_backend_status = QLabel("현재 엔진: High-End Native DSP (실시간 물리 음향 합성 및 차량 블루투스 다이렉트 출력)")
        self.lbl_backend_status.setStyleSheet("color: #10b981; font-weight: bold; font-size: 13px;")
        c_layout.addWidget(self.lbl_backend_status)
        layout.addWidget(choice_box)

        # Pure Data connection box
        self.box_pd_ctrl = QGroupBox("Pure Data (Pd-vanilla) FUDI 소켓 연동 (포트 3000)")
        pd_l = QHBoxLayout(self.box_pd_ctrl)
        pd_l.addWidget(QLabel("Pd-vanilla에서 exhaust_synth.pd 파일을 연 뒤 아래 연결 버튼을 누르세요."))
        self.btn_pd_connect = QPushButton("Pure Data 소켓 연결")
        self.btn_pd_connect.clicked.connect(self._on_pd_connect_clicked)
        pd_l.addWidget(self.btn_pd_connect)
        layout.addWidget(self.box_pd_ctrl)

        # FMOD Core status box
        self.box_fmod_ctrl = QGroupBox("FMOD Core API 상태 및 라이브러리 연동")
        fmod_l = QVBoxLayout(self.box_fmod_ctrl)
        fmod_l.setSpacing(8)

        self.lbl_fmod = QLabel(self.fmod_mgr.get_status_message())
        self.lbl_fmod.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 12px; line-height: 1.4;")
        fmod_l.addWidget(self.lbl_fmod)

        btn_rescan_fmod = QPushButton("🔄 FMOD DLL 다시 확인 (새로고침)")
        btn_rescan_fmod.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 6px 14px; border-radius: 4px;")
        btn_rescan_fmod.clicked.connect(self._refresh_fmod_status)
        fmod_l.addWidget(btn_rescan_fmod)

        layout.addWidget(self.box_fmod_ctrl)

        layout.addStretch()

    def _setup_connections(self):
        # Sound toggle
        self.btn_sound_toggle.toggled.connect(self._on_sound_toggled)
        self.vol_slider.valueChanged.connect(self._on_volume_changed)

        # Tuning Controls
        self.slider_rpm.valueChanged.connect(self._on_tuning_rpm_changed)
        self.slider_throttle.valueChanged.connect(self._on_tuning_throttle_changed)
        self.slider_bass.valueChanged.connect(self._on_acoustic_params_changed)
        self.slider_mid.valueChanged.connect(self._on_acoustic_params_changed)
        self.slider_treble.valueChanged.connect(self._on_acoustic_params_changed)
        self.slider_dist.valueChanged.connect(self._on_acoustic_params_changed)
        self.slider_intake.valueChanged.connect(self._on_acoustic_params_changed)
        self.slider_stereo.valueChanged.connect(self._on_acoustic_params_changed)
        self.slider_chassis.valueChanged.connect(self._on_acoustic_params_changed)
        self.chk_valve.toggled.connect(self._on_acoustic_params_changed)
        self.chk_supercharger.toggled.connect(self._on_acoustic_params_changed)
        self.chk_pop.toggled.connect(self._on_acoustic_params_changed)
        self.slider_pop_intensity.valueChanged.connect(self._on_acoustic_params_changed)

        # Simulator inputs
        self.sim_slider_gas.valueChanged.connect(self._on_sim_input_changed)
        self.sim_slider_brake.valueChanged.connect(self._on_sim_input_changed)

        # Tab switch
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Hardware & Telemetry Callbacks (Thread-safe via CanSignalBridge)
        self.pcan_mgr.on_telemetry_update = lambda r, t, s: self.can_bridge.sig_telemetry.emit(r, t, s)
        self.pcan_mgr.on_status_change = lambda msg, succ: self.can_bridge.sig_status.emit(msg, succ)
        self.pcan_mgr.on_can_log = lambda log: self.can_bridge.sig_log.emit(log)

        self.can_bridge.sig_telemetry.connect(self._on_telemetry_received)
        self.can_bridge.sig_status.connect(self._on_pcan_status_changed)
        self.can_bridge.sig_log.connect(self._on_pcan_log_received)

        self.can_rx.on_data_received = lambda r, t, s: self.can_bridge.sig_generic_can.emit(r, t, s)
        self.can_bridge.sig_generic_can.connect(self._on_generic_can_received)

        self.pd_bridge.on_status_change = lambda msg, succ: self.lbl_backend_status.setText(msg)

        # Simulator callback (Thread-safe via CanSignalBridge)
        self.sim.start(lambda r, t, s, g: self.can_bridge.sig_sim_tick.emit(r, t, s, g))
        self.can_bridge.sig_sim_tick.connect(self._on_sim_physics_tick)

    def _refresh_audio_devices(self):
        """Enumerates audio output devices and populates combo box (Bluetooth prioritized)."""
        self.combo_audio_dev.blockSignals(True)
        self.combo_audio_dev.clear()

        devices = ExhaustSoundSynthesizer.get_output_devices()
        selected_idx = 0

        for i, d in enumerate(devices):
            self.combo_audio_dev.addItem(d["label"], userData=d["index"])
            if d.get("is_bluetooth"):
                selected_idx = i  # Auto-select Bluetooth car audio if found
            elif d.get("is_default") and selected_idx == 0:
                selected_idx = i

        if devices:
            self.combo_audio_dev.setCurrentIndex(selected_idx)
            dev_id = self.combo_audio_dev.currentData()
            self.synth.set_output_device(dev_id)

        self.combo_audio_dev.blockSignals(False)

    def _on_audio_device_changed(self):
        dev_id = self.combo_audio_dev.currentData()
        self.synth.set_output_device(dev_id)

    def _on_buffer_size_changed(self, idx: int):
        sizes = [1024, 512, 2048, 4096]
        sz = sizes[idx] if idx < len(sizes) else 1024
        self.synth.set_buffer_size(sz)

    def _refresh_fmod_status(self):
        """Re-scans FMOD DLL and updates GUI status display."""
        loaded = self.fmod_mgr.reload()
        msg = self.fmod_mgr.get_status_message()
        self.lbl_fmod.setText(msg)
        color = "#34d399" if loaded else "#f87171"
        self.lbl_fmod.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px; line-height: 1.4;")
        if loaded:
            QMessageBox.information(self, "FMOD 연동 성공", "64비트 FMOD Core 라이브러리가 성공적으로 감지되었습니다!")
        else:
            QMessageBox.warning(self, "FMOD 연동 안내", msg)

    def _on_audio_backend_changed(self, idx: int):
        backends = ["NATIVE_DSP", "FMOD", "PURE_DATA"]
        self.active_audio_engine = backends[idx]
        if self.active_audio_engine == "NATIVE_DSP":
            self.lbl_backend_status.setText("현재 엔진: High-End Native DSP (3D 공간 음향 & 블루투스 다이렉트 출력)")
            self.synth.start()
        elif self.active_audio_engine == "FMOD":
            self.lbl_backend_status.setText("현재 엔진: FMOD Core API")
            if not self.fmod_mgr.is_available():
                msg = self.fmod_mgr.get_status_message()
                QMessageBox.information(self, "FMOD Core API 안내", msg)
        elif self.active_audio_engine == "PURE_DATA":
            self.lbl_backend_status.setText("현재 엔진: Pure Data (Pd-vanilla FUDI 소켓)")

    def _scan_pcan_devices(self):
        devices = PcanManager.scan_pcan_hardware()
        info_lines = [d["label"] for d in devices]
        QMessageBox.information(self, "PCAN-USB Pro 스캔 결과", "\n".join(info_lines) if info_lines else "PCANBasic 드라이버를 감지할 수 없습니다.")

    def _on_pcan_mode_changed(self, idx: int):
        mode_text = self.combo_pcan_mode.currentText()
        is_preset = "READ_ONLY_PRESET" in mode_text
        is_custom = "READ_ONLY_CUSTOM" in mode_text

        self.combo_pcan_preset.setEnabled(is_preset)
        self.spin_custom_can_id.setEnabled(is_custom)
        self.spin_custom_rpm_byte.setEnabled(is_custom)
        self.spin_custom_th_byte.setEnabled(is_custom)

    def _on_pcan_connect_clicked(self):
        ch_raw = self.combo_pcan_ch.currentText()
        ch_name = PCAN_CHANNELS.get(ch_raw, "PCAN_USBBUS1")
        baud = int(self.combo_pcan_baud.currentText().split()[0])
        mode_str = self.combo_pcan_mode.currentText().split()[0]
        preset_name = self.combo_pcan_preset.currentData() or self.combo_pcan_preset.currentText().split(" - ")[0]

        if mode_str == "READ_ONLY_CUSTOM":
            try:
                hex_str = self.spin_custom_can_id.text().strip()
                self.pcan_mgr.custom_can_id = int(hex_str, 16)
                self.pcan_mgr.rpm_start_byte = self.spin_custom_rpm_byte.value()
                self.pcan_mgr.throttle_start_byte = self.spin_custom_th_byte.value()
            except Exception:
                pass

        success = self.pcan_mgr.connect(
            channel=ch_name,
            bitrate=baud,
            mode=mode_str,
            preset_name=preset_name
        )
        if success:
            self.btn_pcan_connect.setEnabled(False)
            self.btn_pcan_disconnect.setEnabled(True)
            self._set_drive_source("PCAN_PRO")

    def _on_pcan_disconnect_clicked(self):
        self.pcan_mgr.disconnect()
        self.btn_pcan_connect.setEnabled(True)
        self.btn_pcan_disconnect.setEnabled(False)

    def _on_pcan_status_changed(self, msg: str, success: bool):
        col = "#10b981" if success else "#ef4444"
        self.lbl_veh_info.setText(f"PCAN 상태: {msg}")
        self.lbl_veh_info.setStyleSheet(f"color: {col}; font-size: 13px; font-weight: bold;")

    def _on_pcan_log_received(self, log_line: str):
        self.txt_pcan_log.append(log_line)

    def _on_pd_connect_clicked(self):
        succ = self.pd_bridge.connect()
        if not succ:
            QMessageBox.warning(self, "Pure Data 연결 실패", "Pure Data (Pd-vanilla)를 실행하고 exhaust_synth.pd 패치를 먼저 열어주세요.")

    def _set_perspective(self, perspective: str):
        if perspective == "exterior":
            self.btn_persp_exterior.setChecked(True)
            self.btn_persp_cabin.setChecked(False)
        else:
            self.btn_persp_exterior.setChecked(False)
            self.btn_persp_cabin.setChecked(True)

        self.synth.set_perspective(perspective)
        self.tachometer.set_perspective(perspective)

    def _set_drive_source(self, source: str):
        self.drive_source = source
        self.btn_src_sim.setChecked(source == "SIMULATOR")
        self.btn_src_pcan.setChecked(source == "PCAN_PRO")
        self.btn_src_can.setChecked(source == "GENERIC_CAN")
        self.panel_sim.setEnabled(source == "SIMULATOR")

        labels = {
            "SIMULATOR": "가상 시뮬레이터",
            "PCAN_PRO": "PCAN-USB Pro (실제 차량)",
            "GENERIC_CAN": "일반 CAN 어댑터"
        }
        self.tachometer.set_source(labels.get(source, "시뮬레이터"))

    def _on_tab_changed(self, index: int):
        if index == 0:
            self.current_mode = "TUNING"
            self.synth.set_rpm(self.slider_rpm.value())
            self.synth.set_throttle(self.slider_throttle.value() / 100.0)
        elif index == 1:
            self.current_mode = "DRIVE"
            if self.drive_source == "SIMULATOR":
                self.synth.set_rpm(self.sim.rpm)
                self.synth.set_throttle(self.sim.throttle)

    def _on_sim_neutral_toggled(self, checked: bool):
        self.sim.set_inputs(self.sim.throttle, self.sim.brake, neutral=checked)
        self.btn_sim_neutral.setText("⚙️ N단 후까시 모드 (활성화됨)" if checked else "⚙️ N단 후까시 / 주행 모드 전환")

    def _on_sim_input_changed(self):
        gas = self.sim_slider_gas.value() / 100.0
        brake = self.sim_slider_brake.value() / 100.0
        self.lbl_sim_gas.setText(f"{self.sim_slider_gas.value()}%")
        self.lbl_sim_brake.setText(f"{self.sim_slider_brake.value()}%")
        self.sim.set_inputs(gas, brake)

    def _on_sim_physics_tick(self, rpm: float, throttle: float, speed: float, gear: int):
        if self.current_mode == "DRIVE" and self.drive_source == "SIMULATOR":
            self._update_all_engines(rpm, throttle, speed, gear)

    def _on_telemetry_received(self, rpm: float, throttle: float, speed: float):
        if self.current_mode == "DRIVE" and self.drive_source == "PCAN_PRO":
            self._update_all_engines(rpm, throttle, speed, 1)

    def _on_generic_can_received(self, rpm: float, throttle: float, speed: float):
        if self.current_mode == "DRIVE" and self.drive_source == "GENERIC_CAN":
            self._update_all_engines(rpm, throttle, speed, 1)

    def _update_all_engines(self, rpm: float, throttle: float, speed: float, gear: int):
        self.synth.set_rpm(rpm)
        self.synth.set_throttle(throttle)
        self.tachometer.set_data(rpm, throttle, speed, gear)

        # Update FMOD & Pure Data if active
        if self.fmod_mgr.is_running:
            self.fmod_mgr.update_telemetry(rpm, throttle)
        if self.pd_bridge.is_connected:
            self.pd_bridge.update_telemetry(rpm, throttle)

    def _on_sound_toggled(self, checked: bool):
        if checked:
            self.synth.start()
            self.btn_sound_toggle.setText("🔊 사운드 ON (작동중)")
        else:
            self.synth.stop()
            self.btn_sound_toggle.setText("🔈 사운드 OFF")

    def _on_volume_changed(self, val: int):
        self.lbl_vol_val.setText(f"{val}%")
        self.synth.set_tuning(volume=(val / 100.0))

    def _on_tuning_rpm_changed(self, val: int):
        self.lbl_rpm_disp.setText(f"{val} RPM")
        if self.current_mode == "TUNING":
            self.synth.set_rpm(val)
            self.tachometer.set_data(val, self.synth.throttle, 0.0, 0)
            if self.pd_bridge.is_connected:
                self.pd_bridge.update_telemetry(val, self.synth.throttle)

    def _on_tuning_throttle_changed(self, val: int):
        self.lbl_throttle_disp.setText(f"{val} %")
        if self.current_mode == "TUNING":
            self.synth.set_throttle(val / 100.0)
            self.tachometer.set_data(self.synth.rpm, val / 100.0, 0.0, 0)

    def _on_pedal_down(self):
        self.slider_throttle.setValue(100)
        target = min(int(self.synth.current_model.redline_rpm - 300), self.slider_rpm.value() + 4500)
        self.slider_rpm.setValue(target)

    def _on_pedal_up(self):
        self.slider_throttle.setValue(0)
        self.slider_rpm.setValue(int(self.synth.current_model.idle_rpm))

    def _on_acoustic_params_changed(self):
        bass = self.slider_bass.value() / 100.0
        mid = self.slider_mid.value() / 100.0
        treble = self.slider_treble.value() / 100.0
        dist = self.slider_dist.value() / 100.0
        intake = self.slider_intake.value() / 100.0
        stereo = self.slider_stereo.value() / 100.0
        chassis = self.slider_chassis.value() / 100.0
        pop_int = self.slider_pop_intensity.value() / 100.0
        valve = self.chk_valve.isChecked()
        sc = self.chk_supercharger.isChecked()
        pop_en = self.chk_pop.isChecked()

        self.lbl_bass_disp.setText(f"{bass:.1f}x")
        self.lbl_mid_disp.setText(f"{mid:.1f}x")
        self.lbl_treble_disp.setText(f"{treble:.1f}x")
        self.lbl_dist_disp.setText(f"{int(dist * 100)}%")
        self.lbl_intake_disp.setText(f"{intake:.1f}x")
        self.lbl_stereo_disp.setText(f"{stereo:.1f}x")
        self.lbl_chassis_disp.setText(f"{chassis:.1f}x")

        self.synth.set_tuning(
            bass=bass,
            mid=mid,
            treble=treble,
            distortion=dist,
            valve_open=valve,
            supercharger=sc,
            pop_enabled=pop_en,
            pop_intensity=pop_int,
            intake_roar=intake,
            stereo_width=stereo,
            chassis_vibe=chassis,
        )

    def load_preset_to_ui(self, preset_name: str):
        preset = self.preset_mgr.get_preset(preset_name)
        model_key = preset.get("model_key", "muscle_v8")

        self.synth.set_model(model_key)
        self.lbl_model_badge.setText(preset_name)

        max_rpm = preset.get("max_rpm", 7000)
        self.tachometer.set_max_rpm(max_rpm)
        self.slider_rpm.setMaximum(int(max_rpm))
        self.slider_rpm.setValue(int(preset.get("idle_rpm", 780)))

        persp = preset.get("perspective", "exterior")
        self._set_perspective(persp)

        self.slider_bass.setValue(int(preset.get("bass_boost", 1.5) * 100))
        self.slider_mid.setValue(int(preset.get("mid_punch", 1.2) * 100))
        self.slider_treble.setValue(int(preset.get("treble_scream", 1.0) * 100))
        self.slider_dist.setValue(int(preset.get("distortion", 0.45) * 100))
        self.slider_intake.setValue(int(preset.get("intake_roar", 1.2) * 100))
        self.slider_stereo.setValue(int(preset.get("stereo_width", 1.3) * 100))
        self.slider_chassis.setValue(int(preset.get("chassis_vibe", 1.4) * 100))
        self.chk_valve.setChecked(preset.get("valve_open", True))
        self.chk_supercharger.setChecked(preset.get("supercharger", (model_key == "muscle_v8")))
        self.chk_pop.setChecked(preset.get("pop_and_bang", True))
        self.slider_pop_intensity.setValue(int(preset.get("pop_intensity", 1.5) * 100))
        self.vol_slider.setValue(int(preset.get("master_volume", 0.90) * 100))

        idx = self.combo_presets.findText(preset_name)
        if idx >= 0:
            self.combo_presets.setCurrentIndex(idx)

        self._on_acoustic_params_changed()

    def _on_preset_selected(self):
        name = self.combo_presets.currentText()
        self.load_preset_to_ui(name)

    def _on_save_preset(self):
        name = self.txt_new_preset.text().strip()
        if not name:
            QMessageBox.warning(self, "경고", "프리셋 이름을 입력하세요.")
            return

        settings = {
            "model_key": self.synth.current_model_key,
            "description": f"사용자 커스텀 세팅 ({name})",
            "idle_rpm": int(self.synth.current_model.idle_rpm),
            "max_rpm": int(self.synth.current_model.redline_rpm),
            "cylinders": self.synth.current_model.cylinders,
            "perspective": self.synth.perspective,
            "bass_boost": self.slider_bass.value() / 100.0,
            "mid_punch": self.slider_mid.value() / 100.0,
            "treble_scream": self.slider_treble.value() / 100.0,
            "intake_roar": self.slider_intake.value() / 100.0,
            "stereo_width": self.slider_stereo.value() / 100.0,
            "chassis_vibe": self.slider_chassis.value() / 100.0,
            "valve_open": self.chk_valve.isChecked(),
            "supercharger": self.chk_supercharger.isChecked(),
            "pop_and_bang": self.chk_pop.isChecked(),
            "pop_intensity": self.slider_pop_intensity.value() / 100.0,
            "distortion": self.slider_dist.value() / 100.0,
            "master_volume": self.vol_slider.value() / 100.0,
        }

        self.preset_mgr.set_preset(name, settings)
        if self.combo_presets.findText(name) == -1:
            self.combo_presets.addItem(name)
        self.combo_presets.setCurrentText(name)
        QMessageBox.information(self, "성공", f"'{name}' 프리셋이 안전하게 저장되었습니다!")

    def _on_ui_tick(self):
        self.waveform_widget.update_waveform(self.synth.latest_waveform)

        if self.pcan_mgr.is_connected:
            self.lbl_veh_telemetry.setText(
                f"수신 프레임: {self.pcan_mgr.messages_count} msgs | "
                f"현재 RPM: {int(self.pcan_mgr.current_rpm)} | "
                f"현재 스로틀: {int(self.pcan_mgr.current_throttle * 100)}% | "
                f"차속: {self.pcan_mgr.current_speed:.1f} km/h"
            )

        if self.current_mode == "TUNING":
            self.tachometer.set_data(self.synth.rpm, self.synth.throttle, 0.0, 0)

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0d1117; color: #e6edf3; }
            QWidget { background-color: #0d1117; color: #e6edf3; font-family: 'Segoe UI', Arial, sans-serif; }
            QGroupBox { border: 1px solid #30363d; border-radius: 8px; margin-top: 10px; font-weight: bold; color: #58a6ff; font-size: 13px; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 6px; }
            QLabel { color: #c9d1d9; }
            QSlider::groove:horizontal { border: 1px solid #30363d; height: 8px; background: #21262d; border-radius: 4px; }
            QSlider::sub-page:horizontal { background: #1f6feb; border-radius: 4px; }
            QSlider::handle:horizontal { background: #58a6ff; border: 1px solid #1f6feb; width: 18px; margin-top: -5px; margin-bottom: -5px; border-radius: 9px; }
            QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox { background-color: #21262d; border: 1px solid #30363d; border-radius: 6px; color: #f0f6fc; padding: 5px 8px; font-size: 12px; }
            QComboBox:hover, QLineEdit:hover { border-color: #58a6ff; }
            QPushButton { background-color: #21262d; border: 1px solid #30363d; border-radius: 6px; color: #f0f6fc; padding: 7px 14px; font-size: 12px; font-weight: 500; }
            QPushButton:hover { background-color: #30363d; border-color: #8b949e; }
            QCheckBox { color: #c9d1d9; spacing: 8px; }
            QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 1px solid #30363d; background: #21262d; }
            QCheckBox::indicator:checked { background-color: #1f6feb; border-color: #58a6ff; }
        """)

    def closeEvent(self, event):
        self.pcan_mgr.disconnect()
        self.pd_bridge.disconnect()
        self.fmod_mgr.release()
        self.sim.stop()
        self.can_rx.disconnect()
        self.synth.stop()
        event.accept()


def main():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)
    window = ExhaustAppWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
