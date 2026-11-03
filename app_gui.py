"""
Supercar & Muscle Car Exhaust Sound Simulator & Cockpit (PySide6)
Professional Desktop GUI with Cockpit (Cabin) Interior & Exterior Views,
Intake Induction Roar, and GTA / Real-Game 3D Stereo Spatial Audio.
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
    QProgressBar,
    QFrame,
    QMessageBox,
)

from sound_engine import ExhaustSoundSynthesizer
from can_interface import VirtualVehicleSimulator, CanReceiver
from presets_manager import PresetsManager


class WaveformWidget(QFrame):
    """Real-time sound waveform visualizer."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(75)
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
        self.setMinimumHeight(160)

    def set_max_rpm(self, max_rpm: float):
        self.max_rpm = max_rpm
        self.update()

    def set_perspective(self, perspective: str):
        self.perspective = perspective
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
        font_rpm = QFont("Consolas", 36, QFont.Bold)
        painter.setFont(font_rpm)
        painter.drawText(24, 60, f"{int(self.rpm):05d}")

        painter.setFont(QFont("Arial", 12))
        painter.setPen(QColor(140, 150, 170))
        painter.drawText(170, 48, "RPM")

        # Gear Display Badge
        gear_rect_x = width - 110
        painter.setBrush(QColor(30, 36, 48))
        painter.setPen(QPen(QColor(60, 75, 100), 2))
        painter.drawRoundedRect(gear_rect_x, 16, 85, 75, 10, 10)

        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.setPen(QColor(120, 140, 170))
        painter.drawText(gear_rect_x + 28, 36, "GEAR")

        painter.setFont(QFont("Consolas", 28, QFont.Bold))
        painter.setPen(QColor(255, 180, 0))
        gear_str = "N" if self.gear == 0 else str(self.gear)
        painter.drawText(gear_rect_x + 32, 75, gear_str)

        # Speed and Throttle Stats
        painter.setFont(QFont("Consolas", 22, QFont.Bold))
        painter.setPen(QColor(0, 230, 255))
        painter.drawText(240, 58, f"{self.speed:5.1f} km/h")

        painter.setFont(QFont("Arial", 11))
        painter.setPen(QColor(150, 160, 180))
        painter.drawText(390, 56, f"부하(Load): {int(self.throttle * 100)}%")

        # Perspective status tag
        persp_text = "💺 운전석 실내 (Cabin)" if self.perspective == "cabin" else "🏎️ 실외 배기구 (Exterior)"
        persp_col = QColor(168, 85, 247) if self.perspective == "cabin" else QColor(34, 197, 94)
        painter.setFont(QFont("Arial", 11, QFont.Bold))
        painter.setPen(persp_col)
        painter.drawText(560, 56, persp_text)

        # Dynamic Colored Tachometer Arc Bar
        bar_x = 24
        bar_y = 105
        bar_w = width - 48
        bar_h = 24

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
        painter.drawLine(redline_x, bar_y - 4, redline_x, bar_y + bar_h + 4)


class ExhaustAppWindow(QMainWindow):
    """Main Application Window."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Supercar & Muscle Car Exhaust Sound Simulator & Cockpit (1단계 PC)")
        self.resize(1120, 890)
        self.setMinimumSize(1000, 800)

        # Initialize DSP, CAN & Presets
        self.synth = ExhaustSoundSynthesizer(sample_rate=44100, buffer_size=1024)
        self.preset_mgr = PresetsManager()
        self.sim = VirtualVehicleSimulator()
        self.can_rx = CanReceiver()

        # State
        self.current_mode = "TUNING"
        self.drive_source = "SIMULATOR"

        self._init_ui()
        self._apply_dark_theme()
        self._setup_connections()

        # Real-time UI refresh timer (30 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_ui_tick)
        self.timer.start(33)

        # Auto-start sound engine with Muscle V8 default preset
        self.load_preset_to_ui("아메리칸 머슬카 V8 (6.2L Supercharged)")
        self.synth.start()
        self.btn_sound_toggle.setText("🔊 사운드 엔진 ON (작동중)")
        self.btn_sound_toggle.setChecked(True)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        # 1. Top Header Bar (Global Sound, Master Volume & Perspective Toggle)
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #171b22; border: 1px solid #2a313d; border-radius: 8px; padding: 6px;")
        header_layout = QHBoxLayout(header_frame)

        self.btn_sound_toggle = QPushButton("🔊 사운드 엔진 ON")
        self.btn_sound_toggle.setCheckable(True)
        self.btn_sound_toggle.setStyleSheet("""
            QPushButton { background-color: #00875a; color: white; font-weight: bold; font-size: 13px; padding: 8px 16px; border-radius: 6px; }
            QPushButton:!checked { background-color: #4b5563; }
        """)

        # Perspective Switcher (실외 배기구 vs 운전석 실내)
        persp_label = QLabel("청음 관점:")
        persp_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.btn_persp_exterior = QPushButton("🏎️ 실외 배기구 (Exterior)")
        self.btn_persp_exterior.setCheckable(True)
        self.btn_persp_exterior.setChecked(True)
        self.btn_persp_exterior.setStyleSheet("""
            QPushButton { background-color: #059669; color: white; font-weight: bold; padding: 8px 14px; border-radius: 6px; font-size: 12px; }
            QPushButton:!checked { background-color: #27272a; color: #9ca3af; }
        """)

        self.btn_persp_cabin = QPushButton("💺 운전석 실내 (Cockpit Cabin)")
        self.btn_persp_cabin.setCheckable(True)
        self.btn_persp_cabin.setStyleSheet("""
            QPushButton { background-color: #8b5cf6; color: white; font-weight: bold; padding: 8px 14px; border-radius: 6px; font-size: 12px; }
            QPushButton:!checked { background-color: #27272a; color: #9ca3af; }
        """)

        self.btn_persp_exterior.clicked.connect(lambda: self._set_perspective("exterior"))
        self.btn_persp_cabin.clicked.connect(lambda: self._set_perspective("cabin"))

        vol_label = QLabel("마스터 볼륨:")
        vol_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(90)
        self.vol_slider.setFixedWidth(130)
        self.lbl_vol_val = QLabel("90%")
        self.lbl_vol_val.setFixedWidth(40)

        self.lbl_model_badge = QLabel("아메리칸 머슬카 V8 (6.2L Supercharged)")
        self.lbl_model_badge.setStyleSheet("color: #00e5ff; font-weight: bold; font-size: 14px; background-color: #0d2838; padding: 6px 12px; border-radius: 6px; border: 1px solid #00a0b0;")

        header_layout.addWidget(self.btn_sound_toggle)
        header_layout.addSpacing(15)
        header_layout.addWidget(persp_label)
        header_layout.addWidget(self.btn_persp_exterior)
        header_layout.addWidget(self.btn_persp_cabin)
        header_layout.addSpacing(15)
        header_layout.addWidget(vol_label)
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
            QTabBar::tab { background: #20242f; color: #a0aec0; padding: 10px 28px; font-weight: bold; font-size: 13px; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 4px; }
            QTabBar::tab:selected { background: #0284c7; color: white; }
        """)

        self.tab_tuning = QWidget()
        self.tab_drive = QWidget()
        self.tab_can = QWidget()

        self._build_tuning_tab()
        self._build_drive_tab()
        self._build_can_tab()

        self.tabs.addTab(self.tab_tuning, "🎛️ 튜닝 모드 (Tuning Mode)")
        self.tabs.addTab(self.tab_drive, "🏎️ 드라이브 모드 (Drive Mode)")
        self.tabs.addTab(self.tab_can, "📡 CAN 통신 연동 (CAN Settings)")

        main_layout.addWidget(self.tabs, stretch=1)

    def _build_tuning_tab(self):
        layout = QVBoxLayout(self.tab_tuning)
        layout.setSpacing(12)
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

        # Bottom: Detailed Acoustic Parameters (EQ, 3D Spatial, Intake Roar, Chassis)
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

        # Toggles: Valve, Pop and Bang, Supercharger Whine, Saturation
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
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Drive Source Selector
        source_box = QGroupBox("드라이브 모드 입력 소스 선택")
        source_layout = QHBoxLayout(source_box)

        self.btn_src_sim = QPushButton("🎮 가상 주행 시뮬레이터 (PC 내장 시뮬레이션)")
        self.btn_src_sim.setCheckable(True)
        self.btn_src_sim.setChecked(True)
        self.btn_src_sim.setStyleSheet("""
            QPushButton { background-color: #0284c7; color: white; font-weight: bold; font-size: 13px; padding: 10px 16px; border-radius: 6px; }
            QPushButton:!checked { background-color: #374151; color: #9ca3af; }
        """)

        self.btn_src_can = QPushButton("🚗 실제 차량 CAN Bus 수신 연동 (OBD-II / Custom CAN)")
        self.btn_src_can.setCheckable(True)
        self.btn_src_can.setStyleSheet("""
            QPushButton { background-color: #059669; color: white; font-weight: bold; font-size: 13px; padding: 10px 16px; border-radius: 6px; }
            QPushButton:!checked { background-color: #374151; color: #9ca3af; }
        """)

        self.btn_src_sim.clicked.connect(lambda: self._set_drive_source("SIMULATOR"))
        self.btn_src_can.clicked.connect(lambda: self._set_drive_source("CAN"))

        source_layout.addWidget(self.btn_src_sim)
        source_layout.addWidget(self.btn_src_can)
        layout.addWidget(source_box)

        # Sub-panel 1: Virtual Driving Simulator Controls
        self.panel_sim = QGroupBox("가상 차량 주행 조작 콘솔 (DCT 7단 자동 변속)")
        sim_layout = QGridLayout(self.panel_sim)

        # Gas pedal slider
        sim_layout.addWidget(QLabel("가속 페달 (Gas):"), 0, 0)
        self.sim_slider_gas = QSlider(Qt.Horizontal)
        self.sim_slider_gas.setRange(0, 100)
        self.sim_slider_gas.setValue(0)
        self.lbl_sim_gas = QLabel("0%")
        sim_layout.addWidget(self.sim_slider_gas, 0, 1)
        sim_layout.addWidget(self.lbl_sim_gas, 0, 2)

        # Brake pedal slider
        sim_layout.addWidget(QLabel("브레이크 (Brake):"), 1, 0)
        self.sim_slider_brake = QSlider(Qt.Horizontal)
        self.sim_slider_brake.setRange(0, 100)
        self.sim_slider_brake.setValue(0)
        self.lbl_sim_brake = QLabel("0%")
        sim_layout.addWidget(self.sim_slider_brake, 1, 1)
        sim_layout.addWidget(self.lbl_sim_brake, 1, 2)

        # Quick Drive Buttons
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

        # Sub-panel 2: CAN Live Status
        self.panel_can_status = QGroupBox("실시간 CAN Bus 데이터 수신 상태")
        can_status_layout = QVBoxLayout(self.panel_can_status)

        self.lbl_can_rx_info = QLabel("CAN 상태: 연결 대기 중 (CAN 설정 탭에서 연결을 시작하세요)")
        self.lbl_can_rx_info.setStyleSheet("color: #fbbf24; font-size: 13px; font-weight: bold;")
        self.lbl_can_stats = QLabel("수신 프레임: 0 msgs | 최근 RPM: 0 | 최근 Throttle: 0%")
        self.lbl_can_stats.setFont(QFont("Consolas", 12))

        can_status_layout.addWidget(self.lbl_can_rx_info)
        can_status_layout.addWidget(self.lbl_can_stats)
        layout.addWidget(self.panel_can_status)

        layout.addStretch()

    def _build_can_tab(self):
        layout = QVBoxLayout(self.tab_can)
        layout.setSpacing(14)
        layout.setContentsMargins(16, 16, 16, 16)

        conn_box = QGroupBox("1. CAN 하드웨어 인터페이스 설정")
        c_layout = QGridLayout(conn_box)

        c_layout.addWidget(QLabel("CAN 인터페이스:"), 0, 0)
        self.combo_can_iface = QComboBox()
        self.combo_can_iface.addItems(["virtual", "slcan (USB-CAN/CANable)", "pcan (PEAK-System)", "socketcan (Linux/RPi)", "serial"])
        c_layout.addWidget(self.combo_can_iface, 0, 1)

        c_layout.addWidget(QLabel("채널 / COM 포트:"), 0, 2)
        self.txt_can_channel = QLineEdit("0")
        self.txt_can_channel.setPlaceholderText("예: 0, COM3, can0...")
        c_layout.addWidget(self.txt_can_channel, 0, 3)

        c_layout.addWidget(QLabel("통신 속도 (Bitrate):"), 1, 0)
        self.combo_can_bitrate = QComboBox()
        self.combo_can_bitrate.addItems(["500000 (500 kbps)", "250000 (250 kbps)", "1000000 (1 Mbps)", "125000 (125 kbps)"])
        c_layout.addWidget(self.combo_can_bitrate, 1, 1)

        c_layout.addWidget(QLabel("프로토콜 모드:"), 1, 2)
        self.combo_can_mode = QComboBox()
        self.combo_can_mode.addItems(["OBD-II (표준 PID 0x0C / 0x11)", "CUSTOM (사용자 지정 CAN ID)"])
        c_layout.addWidget(self.combo_can_mode, 1, 3)

        btn_conn_layout = QHBoxLayout()
        self.btn_can_connect = QPushButton("🔌 CAN 버스 연결")
        self.btn_can_connect.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 10px 20px; border-radius: 6px;")
        self.btn_can_connect.clicked.connect(self._on_can_connect_clicked)

        self.btn_can_disconnect = QPushButton("연결 해제")
        self.btn_can_disconnect.setStyleSheet("background-color: #4b5563; color: white; padding: 10px 20px; border-radius: 6px;")
        self.btn_can_disconnect.clicked.connect(self._on_can_disconnect_clicked)
        self.btn_can_disconnect.setEnabled(False)

        btn_conn_layout.addWidget(self.btn_can_connect)
        btn_conn_layout.addWidget(self.btn_can_disconnect)
        btn_conn_layout.addStretch()
        c_layout.addLayout(btn_conn_layout, 2, 0, 1, 4)

        layout.addWidget(conn_box)

        # Custom CAN Frame Parsing Settings
        custom_box = QGroupBox("2. 커스텀 CAN 메시지 파싱 설정 (차종별 직접 스니핑용)")
        custom_layout = QGridLayout(custom_box)

        custom_layout.addWidget(QLabel("CAN 메시지 ID (Hex):"), 0, 0)
        self.txt_custom_id = QLineEdit("0x316")
        custom_layout.addWidget(self.txt_custom_id, 0, 1)

        custom_layout.addWidget(QLabel("RPM Start Byte:"), 0, 2)
        self.spin_rpm_byte = QSpinBox()
        self.spin_rpm_byte.setRange(0, 7)
        self.spin_rpm_byte.setValue(2)
        custom_layout.addWidget(self.spin_rpm_byte, 0, 3)

        custom_layout.addWidget(QLabel("RPM Length:"), 1, 0)
        self.spin_rpm_len = QSpinBox()
        self.spin_rpm_len.setRange(1, 4)
        self.spin_rpm_len.setValue(2)
        custom_layout.addWidget(self.spin_rpm_len, 1, 1)

        custom_layout.addWidget(QLabel("RPM Scale Factor:"), 1, 2)
        self.spin_rpm_scale = QDoubleSpinBox()
        self.spin_rpm_scale.setRange(0.01, 100.0)
        self.spin_rpm_scale.setValue(0.25)
        custom_layout.addWidget(self.spin_rpm_scale, 1, 3)

        custom_layout.addWidget(QLabel("Throttle Start Byte:"), 2, 0)
        self.spin_th_byte = QSpinBox()
        self.spin_th_byte.setRange(0, 7)
        self.spin_th_byte.setValue(4)
        custom_layout.addWidget(self.spin_th_byte, 2, 1)

        layout.addWidget(custom_box)

        # PC Simulation: Built-in Virtual OBD-II CAN Sender
        sim_can_box = QGroupBox("3. PC 시뮬레이션용 가상 CAN 송신기 (Virtual OBD-II Transmitter)")
        sc_layout = QHBoxLayout(sim_can_box)
        sc_layout.addWidget(QLabel("실제 CAN 하드웨어 없이도 'virtual' 채널을 통해 가상 OBD-II CAN 트래픽을 송출하여 드라이브 모드를 검증할 수 있습니다."))

        self.btn_virt_sender = QPushButton("📡 가상 CAN 트래픽 송출 시작")
        self.btn_virt_sender.setCheckable(True)
        self.btn_virt_sender.setStyleSheet("""
            QPushButton { background-color: #6366f1; color: white; font-weight: bold; padding: 10px 16px; border-radius: 6px; }
            QPushButton:checked { background-color: #10b981; }
        """)
        self.btn_virt_sender.toggled.connect(self._on_toggle_virtual_can_sender)
        sc_layout.addWidget(self.btn_virt_sender)

        layout.addWidget(sim_can_box)
        layout.addStretch()

        self.virt_sender_thread = None
        self.virt_sender_running = False

    def _setup_connections(self):
        # Sound toggle
        self.btn_sound_toggle.toggled.connect(self._on_sound_toggled)

        # Master Volume
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

        # CAN receiver callbacks
        self.can_rx.on_data_received = self._on_can_data_received
        self.can_rx.on_status_change = self._on_can_status_changed

        # Simulator callback
        self.sim.start(self._on_sim_physics_tick)

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
        if source == "SIMULATOR":
            self.btn_src_sim.setChecked(True)
            self.btn_src_can.setChecked(False)
            self.panel_sim.setEnabled(True)
        else:
            self.btn_src_sim.setChecked(False)
            self.btn_src_can.setChecked(True)
            self.panel_sim.setEnabled(False)

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
            self.synth.set_rpm(rpm)
            self.synth.set_throttle(throttle)
            self.tachometer.set_data(rpm, throttle, speed, gear)

    def _on_can_data_received(self, rpm: float, throttle: float, speed: float):
        if self.current_mode == "DRIVE" and self.drive_source == "CAN":
            self.synth.set_rpm(rpm)
            self.synth.set_throttle(throttle)
            self.tachometer.set_data(rpm, throttle, speed, 1)

    def _on_can_status_changed(self, msg: str, success: bool):
        color = "#10b981" if success else "#ef4444"
        self.lbl_can_rx_info.setText(f"CAN 상태: {msg}")
        self.lbl_can_rx_info.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")

    def _on_sound_toggled(self, checked: bool):
        if checked:
            self.synth.start()
            self.btn_sound_toggle.setText("🔊 사운드 엔진 ON (작동중)")
        else:
            self.synth.stop()
            self.btn_sound_toggle.setText("🔈 사운드 엔진 OFF")

    def _on_volume_changed(self, val: int):
        self.lbl_vol_val.setText(f"{val}%")
        self.synth.set_tuning(volume=(val / 100.0))

    def _on_tuning_rpm_changed(self, val: int):
        self.lbl_rpm_disp.setText(f"{val} RPM")
        if self.current_mode == "TUNING":
            self.synth.set_rpm(val)
            self.tachometer.set_data(val, self.synth.throttle, 0.0, 0)

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

        # Update tachometer max rpm
        max_rpm = preset.get("max_rpm", 7000)
        self.tachometer.set_max_rpm(max_rpm)
        self.slider_rpm.setMaximum(int(max_rpm))
        self.slider_rpm.setValue(int(preset.get("idle_rpm", 780)))

        # Perspective
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

    def _on_can_connect_clicked(self):
        raw_iface = self.combo_can_iface.currentText()
        iface = raw_iface.split()[0]
        channel = self.txt_can_channel.text().strip()
        bitrate_str = self.combo_can_bitrate.currentText().split()[0]
        bitrate = int(bitrate_str)
        mode = "OBD2" if "OBD-II" in self.combo_can_mode.currentText() else "CUSTOM"

        if mode == "CUSTOM":
            try:
                self.can_rx.custom_can_id = int(self.txt_custom_id.text().strip(), 16)
            except Exception:
                self.can_rx.custom_can_id = 0x316
            self.can_rx.rpm_start_byte = self.spin_rpm_byte.value()
            self.can_rx.rpm_length_bytes = self.spin_rpm_len.value()
            self.can_rx.rpm_scale = self.spin_rpm_scale.value()
            self.can_rx.throttle_start_byte = self.spin_th_byte.value()

        success = self.can_rx.connect(interface=iface, channel=channel, bitrate=bitrate, mode=mode)
        if success:
            self.btn_can_connect.setEnabled(False)
            self.btn_can_disconnect.setEnabled(True)

    def _on_can_disconnect_clicked(self):
        self.can_rx.disconnect()
        self.btn_can_connect.setEnabled(True)
        self.btn_can_disconnect.setEnabled(False)

    def _on_toggle_virtual_can_sender(self, checked: bool):
        if checked:
            self.virt_sender_running = True
            self.btn_virt_sender.setText("🛑 가상 CAN 송출 중단")
            self.virt_sender_thread = threading.Thread(target=self._virt_can_tx_loop, daemon=True)
            self.virt_sender_thread.start()
        else:
            self.virt_sender_running = False
            self.btn_virt_sender.setText("📡 가상 CAN 트래픽 송출 시작")

    def _virt_can_tx_loop(self):
        try:
            tx_bus = can.Bus(interface="virtual", channel="0")
            rpm = 1000.0
            direction = 1
            while self.virt_sender_running:
                rpm += direction * 70.0
                if rpm > 6500:
                    direction = -1
                elif rpm < 1000:
                    direction = 1

                raw = int(rpm * 4)
                a = (raw >> 8) & 0xFF
                b = raw & 0xFF
                msg = can.Message(arbitration_id=0x7E8, data=[0x04, 0x41, 0x0C, a, b, 0x00, 0x00, 0x00], is_extended_id=False)
                try:
                    tx_bus.send(msg)
                except Exception:
                    pass
                time.sleep(0.04)
            tx_bus.shutdown()
        except Exception as e:
            print("Virt CAN sender error:", e)

    def _on_ui_tick(self):
        self.waveform_widget.update_waveform(self.synth.latest_waveform)

        if self.can_rx.is_connected:
            self.lbl_can_stats.setText(
                f"수신 프레임: {self.can_rx.messages_received} msgs | "
                f"현재 RPM: {int(self.synth.rpm)} | "
                f"현재 스로틀: {int(self.synth.throttle * 100)}%"
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
            QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox { background-color: #21262d; border: 1px solid #30363d; border-radius: 6px; color: #f0f6fc; padding: 6px 10px; font-size: 13px; }
            QComboBox:hover, QLineEdit:hover { border-color: #58a6ff; }
            QPushButton { background-color: #21262d; border: 1px solid #30363d; border-radius: 6px; color: #f0f6fc; padding: 8px 16px; font-size: 13px; font-weight: 500; }
            QPushButton:hover { background-color: #30363d; border-color: #8b949e; }
            QCheckBox { color: #c9d1d9; spacing: 8px; }
            QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 1px solid #30363d; background: #21262d; }
            QCheckBox::indicator:checked { background-color: #1f6feb; border-color: #58a6ff; }
        """)

    def closeEvent(self, event):
        self.virt_sender_running = False
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
