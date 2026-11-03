"""
High-Fidelity Supercar & Muscle Car Exhaust Sound DSP Engine
Hyper-realistic acoustic physical modeling with Cockpit (Cabin) Interior & Exterior Tailpipe views.
GTA / Real-Game 3D Stereo Spatialization, Intake Induction Roar, and Punchy Loudness Maximizer.

Models:
  - American Muscle V8 (6.2L Hemi / Big-Block with Cam Lope & Supercharger Whine)
  - Porsche 911 GT3 (4.0L Boxer Flat-6 Raspy Screamer)
  - Ferrari F8 / 458 (Flat-plane V8 High-pitch F1 Scream)
  - Maserati GranTurismo (Cross-plane V8 Deep Baritone Rumble)
  - Lamborghini Huracán (5.2L V10 Naturally Aspirated Beast Roar)

Acoustic Perspectives:
  - 'exterior': Loud, raw, raspy tailpipe exhaust, sharp crackles, open-air propagation.
  - 'cabin': Cockpit interior view with acoustic insulation low-pass filtering,
             heavy chassis structure-borne vibration boom, driver-facing intake induction roar,
             and enclosed cabin early reflections.
"""

import math
import time
import random
import threading
import numpy as np
import sounddevice as sd


class EngineProfile:
    """Acoustic specification of an engine model."""
    def __init__(
        self,
        key: str,
        name: str,
        cylinders: int,
        idle_rpm: float,
        redline_rpm: float,
        firing_angles: list[float],
        pipe_delay_ms: float,        # Pipe acoustic transit delay in milliseconds (~8-16ms)
        pipe_reflection: float,      # Tailpipe acoustic reflection factor
        helmholtz_freq: float,       # Muffler chamber fundamental resonance Hz
        helmholtz_q: float,          # Resonance sharpness
        sub_rumble_gain: float,      # Deep sub-bass punch
        manifold_ring_freq: float,   # Exhaust header ringing frequency factor
        valve_rasp: float,           # High-frequency raspy valve distortion
        cam_lope_intensity: float,   # Idle cam chop intensity (for muscle cars)
        has_supercharger: bool,      # Supercharger whistle
        intake_freq: float,          # Intake airbox resonance Hz
        description: str,
    ):
        self.key = key
        self.name = name
        self.cylinders = cylinders
        self.idle_rpm = idle_rpm
        self.redline_rpm = redline_rpm
        self.firing_angles = np.array(firing_angles, dtype=np.float32)
        self.pipe_delay_ms = pipe_delay_ms
        self.pipe_reflection = pipe_reflection
        self.helmholtz_freq = helmholtz_freq
        self.helmholtz_q = helmholtz_q
        self.sub_rumble_gain = sub_rumble_gain
        self.manifold_ring_freq = manifold_ring_freq
        self.valve_rasp = valve_rasp
        self.cam_lope_intensity = cam_lope_intensity
        self.has_supercharger = has_supercharger
        self.intake_freq = intake_freq
        self.description = description


def get_engine_profiles() -> dict[str, EngineProfile]:
    """Factory creating acoustic profiles for 5 legendary engine architectures."""
    return {
        "muscle_v8": EngineProfile(
            key="muscle_v8",
            name="아메리칸 머슬카 V8 (6.2L Supercharged)",
            cylinders=8,
            idle_rpm=780.0,
            redline_rpm=6800.0,
            firing_angles=[0.0, 90.0, 270.0, 360.0, 450.0, 540.0, 630.0, 720.0][:8],
            pipe_delay_ms=13.5,
            pipe_reflection=0.55,
            helmholtz_freq=65.0,
            helmholtz_q=2.8,
            sub_rumble_gain=2.8,
            manifold_ring_freq=2.2,
            valve_rasp=0.45,
            cam_lope_intensity=0.85,
            has_supercharger=True,
            intake_freq=220.0,
            description="6.2L V8 헤미/콜벳 빅블록. 불규칙한 캠 롭 찹(Cam Lope), 심장을 울리는 서브우퍼급 저음 럼블 및 슈퍼차저 휘슬.",
        ),
        "porsche_gt3": EngineProfile(
            key="porsche_gt3",
            name="포르쉐 911 GT3 (Flat-6)",
            cylinders=6,
            idle_rpm=850.0,
            redline_rpm=9000.0,
            firing_angles=[0.0, 120.0, 240.0, 360.0, 480.0, 600.0],
            pipe_delay_ms=9.8,
            pipe_reflection=0.42,
            helmholtz_freq=135.0,
            helmholtz_q=4.2,
            sub_rumble_gain=1.3,
            manifold_ring_freq=4.5,
            valve_rasp=0.85,
            cam_lope_intensity=0.0,
            has_supercharger=False,
            intake_freq=380.0,
            description="수평대향 6기통 9,000 RPM. 앙칼지고 거친 금속성 고회전 비명과 독특한 박서 비트.",
        ),
        "ferrari_f8": EngineProfile(
            key="ferrari_f8",
            name="페라리 F8 / 458 (Flat-plane V8)",
            cylinders=8,
            idle_rpm=900.0,
            redline_rpm=9000.0,
            firing_angles=[0.0, 90.0, 180.0, 270.0, 360.0, 450.0, 540.0, 630.0],
            pipe_delay_ms=8.5,
            pipe_reflection=0.48,
            helmholtz_freq=180.0,
            helmholtz_q=5.0,
            sub_rumble_gain=0.9,
            manifold_ring_freq=6.8,
            valve_rasp=0.95,
            cam_lope_intensity=0.0,
            has_supercharger=False,
            intake_freq=440.0,
            description="180도 플랫 크랭크 8기통. F1 레이싱 머신처럼 날카롭게 찢어지는 초고주파 스크리머 톤.",
        ),
        "maserati_gt": EngineProfile(
            key="maserati_gt",
            name="마세라티 그란투리스모 (Cross-plane V8)",
            cylinders=8,
            idle_rpm=750.0,
            redline_rpm=7500.0,
            firing_angles=[0.0, 90.0, 270.0, 360.0, 450.0, 540.0, 630.0, 720.0][:8],
            pipe_delay_ms=12.0,
            pipe_reflection=0.50,
            helmholtz_freq=95.0,
            helmholtz_q=3.2,
            sub_rumble_gain=2.0,
            manifold_ring_freq=3.0,
            valve_rasp=0.60,
            cam_lope_intensity=0.25,
            has_supercharger=False,
            intake_freq=280.0,
            description="4.7L 크로스플레인 V8. 가슴을 울리는 깊고 웅장한 이탈리안 바리톤 저음과 폭발적인 디셀 버블.",
        ),
        "lamborghini_v10": EngineProfile(
            key="lamborghini_v10",
            name="람보르기니 우라칸 (V10)",
            cylinders=10,
            idle_rpm=850.0,
            redline_rpm=8800.0,
            firing_angles=[0.0, 72.0, 144.0, 216.0, 288.0, 360.0, 432.0, 504.0, 576.0, 648.0],
            pipe_delay_ms=9.2,
            pipe_reflection=0.46,
            helmholtz_freq=145.0,
            helmholtz_q=4.0,
            sub_rumble_gain=1.5,
            manifold_ring_freq=5.2,
            valve_rasp=0.90,
            cam_lope_intensity=0.0,
            has_supercharger=False,
            intake_freq=340.0,
            description="5.2L 자연흡기 V10. 맹렬하고 공격적인 맹수 울음소리와 날카로운 백파이어 팝.",
        ),
    }


class ExhaustSoundSynthesizer:
    """
    Hyper-Realistic Exhaust Sound DSP Engine.
    Combines physical cylinder shockwaves, acoustic pipe waveguides,
    intake induction roar, cockpit cabin insulation, and GTA-style 3D spatial sound.
    """
    def __init__(self, sample_rate: int = 44100, buffer_size: int = 1024):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size

        self.profiles = get_engine_profiles()
        self.current_key = "muscle_v8"
        self.profile = self.profiles[self.current_key]

        # Dynamic Engine Physical State
        self.rpm = 780.0
        self.target_rpm = 780.0
        self.throttle = 0.0          # 0.0 to 1.0 (engine load)
        self.target_throttle = 0.0
        self.prev_throttle = 0.0

        # Crankshaft Angle (0.0 to 720.0 degrees)
        self.crank_angle_deg = 0.0
        self.supercharger_phase = 0.0
        self.cam_lope_phase = 0.0
        self.intake_phase = 0.0

        # Acoustic Perspectives: 'exterior' (실외 배기구) or 'cabin' (운전석 실내)
        self.perspective = "exterior"

        # Waveguide Pipe Delay Line (Circular Buffer for acoustic pipe reflections)
        self.pipe_max_len = int(sample_rate * 0.05) + 100
        self.pipe_buffer = np.zeros(self.pipe_max_len, dtype=np.float32)
        self.pipe_write_idx = 0

        # Helmholtz Muffler Filter States
        self.muffler_x1 = 0.0
        self.muffler_x2 = 0.0
        self.muffler_y1 = 0.0
        self.muffler_y2 = 0.0

        # Cabin Low-pass Insulation Filter States
        self.cabin_lp_x1 = 0.0
        self.cabin_lp_x2 = 0.0
        self.cabin_lp_y1 = 0.0
        self.cabin_lp_y2 = 0.0

        # High-pass DC Blocker states
        self.dc_x1_l = 0.0
        self.dc_y1_l = 0.0
        self.dc_x1_r = 0.0
        self.dc_y1_r = 0.0

        # 3D Stereo Spatializer Delay Buffers (Haas effect & early reflections)
        self.spatial_buf_len = int(sample_rate * 0.04) + 64  # ~40ms
        self.spatial_buf_l = np.zeros(self.spatial_buf_len, dtype=np.float32)
        self.spatial_buf_r = np.zeros(self.spatial_buf_len, dtype=np.float32)
        self.spatial_ptr = 0

        # User Tuning Parameters
        self.master_volume = 0.90
        self.bass_boost = 1.0        # 0.2 ~ 3.5
        self.mid_punch = 1.0         # 0.2 ~ 3.5
        self.treble_scream = 1.0     # 0.2 ~ 3.5
        self.valve_open = True       # Straight-pipe bypass (Sport / Corsa mode)
        self.pop_and_bang_enabled = True
        self.pop_intensity_mod = 1.2 # 0.0 ~ 2.5
        self.distortion = 0.4        # 0.0 ~ 1.0 (raspy saturation)
        self.supercharger_enabled = True  # Toggle supercharger whine for muscle car

        # 3D Sound & Fullness parameters
        self.stereo_width = 1.2      # 0.0 ~ 2.0 (GTA 3D stereo width)
        self.intake_roar = 1.0       # 0.0 ~ 2.5 (Intake induction growl)
        self.chassis_vibe = 1.0      # 0.0 ~ 2.5 (Chassis boom in cabin)

        # Decel Crackle State
        self.crackle_energy = 0.0

        # Audio Stream management
        self.stream = None
        self.is_running = False
        self.lock = threading.Lock()

        # Monitoring waveform buffer (for GUI oscilloscope)
        self.latest_waveform = np.zeros(buffer_size, dtype=np.float32)

    def set_perspective(self, perspective: str):
        with self.lock:
            if perspective in ("exterior", "cabin"):
                self.perspective = perspective

    def set_model(self, model_key: str):
        with self.lock:
            if model_key in self.profiles:
                self.current_key = model_key
                self.profile = self.profiles[model_key]

    @property
    def current_model_key(self) -> str:
        return self.current_key

    @property
    def current_model(self) -> EngineProfile:
        return self.profile

    def set_rpm(self, rpm: float):
        self.target_rpm = max(400.0, min(float(rpm), 11000.0))

    def set_throttle(self, throttle: float):
        self.target_throttle = max(0.0, min(float(throttle), 1.0))

    def set_tuning(
        self,
        volume: float = None,
        bass: float = None,
        mid: float = None,
        treble: float = None,
        valve_open: bool = None,
        pop_enabled: bool = None,
        pop_intensity: float = None,
        distortion: float = None,
        supercharger: bool = None,
        perspective: str = None,
        intake_roar: float = None,
        stereo_width: float = None,
        chassis_vibe: float = None,
    ):
        with self.lock:
            if volume is not None:
                self.master_volume = max(0.0, min(volume, 1.5))
            if bass is not None:
                self.bass_boost = max(0.0, min(bass, 3.5))
            if mid is not None:
                self.mid_punch = max(0.0, min(mid, 3.5))
            if treble is not None:
                self.treble_scream = max(0.0, min(treble, 3.5))
            if valve_open is not None:
                self.valve_open = valve_open
            if pop_enabled is not None:
                self.pop_and_bang_enabled = pop_enabled
            if pop_intensity is not None:
                self.pop_intensity_mod = max(0.0, min(pop_intensity, 2.5))
            if distortion is not None:
                self.distortion = max(0.0, min(distortion, 1.0))
            if supercharger is not None:
                self.supercharger_enabled = supercharger
            if perspective is not None and perspective in ("exterior", "cabin"):
                self.perspective = perspective
            if intake_roar is not None:
                self.intake_roar = max(0.0, min(intake_roar, 3.0))
            if stereo_width is not None:
                self.stereo_width = max(0.0, min(stereo_width, 2.5))
            if chassis_vibe is not None:
                self.chassis_vibe = max(0.0, min(chassis_vibe, 3.0))

    def _audio_callback(self, outdata, frames, time_info, status):
        """Ultra-low latency real-time physical DSP render callback with 3D Spatial Audio."""
        try:
            with self.lock:
                # 1. Physics transition
                rpm_smooth = self.rpm + (self.target_rpm - self.rpm) * 0.22
                throttle_smooth = self.throttle + (self.target_throttle - self.throttle) * 0.30
                rpm_delta = rpm_smooth - self.rpm
                self.rpm = rpm_smooth
                self.throttle = throttle_smooth

                # Detect deceleration overrun
                is_decel = (self.prev_throttle > 0.14 and self.throttle < 0.08) or (rpm_delta < -25.0 and self.rpm > 2400)
                self.prev_throttle = self.throttle

                prof = self.profile

                # Crankshaft degrees per sample: (RPM / 60) * 360 deg/sec = RPM * 6.0 deg/sec
                deg_per_sample = (self.rpm * 6.0) / self.sample_rate

                sample_cranks = (self.crank_angle_deg + np.arange(frames, dtype=np.float32) * deg_per_sample) % 720.0
                self.crank_angle_deg = (self.crank_angle_deg + frames * deg_per_sample) % 720.0

                # 2. Cam Lope Modulation (Muscle Car Rough Idle Chop)
                if prof.cam_lope_intensity > 0.0 and self.rpm < 1300.0:
                    idle_blend = max(0.0, 1.0 - (self.rpm - prof.idle_rpm) / 500.0)
                    self.cam_lope_phase += 2.0 * np.pi * 5.8 * frames / self.sample_rate
                    lope_mod = (
                        0.40 * np.sin(self.cam_lope_phase)
                        + 0.25 * np.sin(self.cam_lope_phase * 0.5 + 0.8)
                    ) * prof.cam_lope_intensity * idle_blend
                else:
                    lope_mod = 0.0

                # 3. Cylinder Blowdown Impulse Shockwaves
                shockwave = np.zeros(frames, dtype=np.float32)
                pulse_duration_deg = 180.0
                rise_deg = 18.0

                load_punch = 0.55 + 1.25 * self.throttle
                valve_mult = 1.35 if self.valve_open else 0.85

                for idx, firing_angle in enumerate(prof.firing_angles):
                    delta = (sample_cranks - firing_angle) % 720.0
                    mask = delta < pulse_duration_deg
                    if not np.any(mask):
                        continue

                    d = delta[mask]
                    p = np.zeros_like(d)

                    # Fast rise
                    rise_mask = d < rise_deg
                    p[rise_mask] = np.sin((np.pi * 0.5 / rise_deg) * d[rise_mask])

                    # Exponential decay + Manifold acoustic ringing
                    decay_mask = ~rise_mask
                    d_dec = d[decay_mask] - rise_deg
                    ring_freq = prof.manifold_ring_freq
                    decay_rate = 0.024
                    p[decay_mask] = np.exp(-decay_rate * d_dec) * (
                        np.cos((ring_freq * np.pi / 180.0) * d_dec) - 0.22
                    )

                    # Jitter & cam lope
                    cyl_jitter = 1.0 + 0.06 * np.sin(idx * 2.39 + self.crank_angle_deg * 0.01)
                    if lope_mod != 0.0:
                        cyl_jitter += lope_mod * (0.6 if (idx % 2 == 0) else -0.6)

                    shockwave[mask] += p * cyl_jitter

                shockwave *= (load_punch * self.mid_punch)

                # 4. Turbulent Gas Flow Noise
                flow_noise = np.random.normal(0.0, 0.05, frames).astype(np.float32)
                flow_mod = np.abs(shockwave) * (0.2 + 0.8 * self.throttle)
                shockwave += flow_noise * flow_mod * 1.4

                # 5. Acoustic Waveguide Pipe Delay Line (Comb Filtering)
                pipe_delay_samples = int((prof.pipe_delay_ms / 1000.0) * self.sample_rate)
                pipe_delay_samples = max(64, min(pipe_delay_samples, self.pipe_max_len - 1))
                refl = prof.pipe_reflection * (1.1 if self.valve_open else 0.8)

                pipe_output = np.zeros(frames, dtype=np.float32)
                buf = self.pipe_buffer
                p_len = self.pipe_max_len
                w_ptr = self.pipe_write_idx

                for n in range(frames):
                    r_ptr = (w_ptr - pipe_delay_samples) % p_len
                    delayed_echo = buf[r_ptr]
                    cell = shockwave[n] + delayed_echo * refl
                    buf[w_ptr] = np.tanh(cell * 1.15) * 0.88
                    pipe_output[n] = buf[w_ptr]
                    w_ptr = (w_ptr + 1) % p_len

                self.pipe_write_idx = w_ptr

                # 6. Helmholtz Muffler Resonator (Sub-Bass Physical Punch)
                f0 = prof.helmholtz_freq
                q = prof.helmholtz_q
                w0 = 2.0 * np.pi * f0 / self.sample_rate
                alpha = np.sin(w0) / (2.0 * q)
                b0 = alpha
                b2 = -alpha
                a0 = 1.0 + alpha
                a1 = -2.0 * np.cos(w0)
                a2 = 1.0 - alpha

                b0 /= a0; b2 /= a0; a1 /= a0; a2 /= a0

                muffler_rumble = np.zeros(frames, dtype=np.float32)
                y1, y2 = self.muffler_y1, self.muffler_y2
                x1, x2 = self.muffler_x1, self.muffler_x2

                for n in range(frames):
                    x = shockwave[n]
                    y = b0 * x + b2 * x2 - a1 * y1 - a2 * y2
                    x2, x1 = x1, x
                    y2, y1 = y1, y
                    muffler_rumble[n] = y

                self.muffler_y1, self.muffler_y2 = y1, y2
                self.muffler_x1, self.muffler_x2 = x1, x2

                # 7. Intake Throttle Induction Growl (차체 내부를 채우는 묵직한 흡기 으르렁거림)
                # Powerful throttle body air suction formant (200~500Hz)
                intake_freq = prof.intake_freq * (1.0 + 0.3 * (self.rpm / prof.redline_rpm))
                intake_phase_inc = 2.0 * np.pi * intake_freq / self.sample_rate
                intake_phases = self.intake_phase + np.cumsum(np.full(frames, intake_phase_inc, dtype=np.float32))
                self.intake_phase = (self.intake_phase + frames * intake_phase_inc) % (2.0 * np.pi * 1000.0)

                # Intake roar increases drastically under heavy load
                intake_gain = (self.throttle ** 1.3) * (0.8 + 0.7 * (self.rpm / 4000.0)) * self.intake_roar
                # Formant pulse for intake
                intake_pulse = (
                    np.sin(intake_phases)
                    + 0.5 * np.sin(intake_phases * 2.0)
                    + 0.25 * np.sin(intake_phases * 3.0)
                ) * (0.3 + 0.7 * (np.abs(shockwave) > 0.3))
                intake_sound = intake_pulse * intake_gain * 1.5

                # 8. Supercharger Whine
                supercharger_sound = np.zeros(frames, dtype=np.float32)
                if prof.has_supercharger and self.supercharger_enabled:
                    sc_freq = (self.rpm / 60.0) * 2.4 * 4.0
                    sc_phase_inc = 2.0 * np.pi * sc_freq / self.sample_rate
                    sc_phases = self.supercharger_phase + np.cumsum(np.full(frames, sc_phase_inc, dtype=np.float32))
                    self.supercharger_phase = (self.supercharger_phase + frames * sc_phase_inc) % (2.0 * np.pi * 1000.0)

                    sc_gain = (0.05 + 0.35 * (self.throttle ** 1.5)) * min(1.0, self.rpm / 3000.0)
                    supercharger_sound = (
                        np.sin(sc_phases)
                        + 0.35 * np.sin(sc_phases * 2.0)
                        + 0.15 * np.sin(sc_phases * 3.0)
                    ) * sc_gain * 0.45

                # 9. Deceleration Pops & Bangs
                crackle_burst = np.zeros(frames, dtype=np.float32)
                if self.pop_and_bang_enabled and (is_decel or (self.throttle < 0.05 and self.rpm > 2800.0)):
                    pop_chance = 0.08 * self.pop_intensity_mod * (1.3 if self.current_key in ("muscle_v8", "maserati_gt") else 0.9)
                    if random.random() < pop_chance:
                        self.crackle_energy = 1.0

                if self.crackle_energy > 0.01:
                    t_crk = np.arange(frames, dtype=np.float32) / self.sample_rate
                    burst_noise = np.random.uniform(-1.0, 1.0, frames).astype(np.float32)
                    decay_env = np.exp(-t_crk * 30.0) * self.crackle_energy
                    thud = np.sin(2.0 * np.pi * 65.0 * t_crk) * 1.6
                    sharp_crack = burst_noise * 1.2
                    crackle_burst = (thud + sharp_crack) * decay_env * 1.6 * self.pop_intensity_mod
                    self.crackle_energy *= 0.58

                # 10. Blend Raw Audio Stems
                total_bass = muffler_rumble * prof.sub_rumble_gain * self.bass_boost * 2.2
                total_mid = pipe_output * 0.85
                valve_scream = shockwave * prof.valve_rasp * self.treble_scream * valve_mult * 0.45

                # Raw exhaust stem (Tailpipe sound)
                raw_exhaust = total_mid + total_bass + valve_scream + crackle_burst

                # 11. Perspective-Specific Acoustic Processing (Cabin vs Exterior)
                if self.perspective == "cabin":
                    # --- 운전석 실내 (Cabin / Cockpit Interior) ---
                    # 1) Acoustic Firewall & Glass Low-Pass Filter (Biquad 1200Hz LPF)
                    fc = 1100.0
                    w_c = 2.0 * np.pi * fc / self.sample_rate
                    q_c = 0.707
                    alpha_c = np.sin(w_c) / (2.0 * q_c)
                    cos_wc = np.cos(w_c)
                    b0_c = (1.0 - cos_wc) / 2.0
                    b1_c = 1.0 - cos_wc
                    b2_c = (1.0 - cos_wc) / 2.0
                    a0_c = 1.0 + alpha_c
                    a1_c = -2.0 * cos_wc
                    a2_c = 1.0 - alpha_c

                    b0_c /= a0_c; b1_c /= a0_c; b2_c /= a0_c
                    a1_c /= a0_c; a2_c /= a0_c

                    filtered_exhaust = np.zeros(frames, dtype=np.float32)
                    y1, y2 = self.cabin_lp_y1, self.cabin_lp_y2
                    x1, x2 = self.cabin_lp_x1, self.cabin_lp_x2

                    for n in range(frames):
                        x = raw_exhaust[n]
                        y = b0_c * x + b1_c * x1 + b2_c * x2 - a1_c * y1 - a2_c * y2
                        x2, x1 = x1, x
                        y2, y1 = y1, y
                        filtered_exhaust[n] = y

                    self.cabin_lp_y1, self.cabin_lp_y2 = y1, y2
                    self.cabin_lp_x1, self.cabin_lp_x2 = x1, x2

                    # 2) Heavy Chassis Structure-borne Vibration (Sub-bass boom ~52Hz)
                    chassis_boom = muffler_rumble * 1.8 * self.chassis_vibe * self.bass_boost

                    # 3) Prominent Driver-Facing Intake Induction Roar
                    # In cabin, intake sound sits directly in front of the driver
                    combined_mono = (
                        filtered_exhaust * 0.65
                        + chassis_boom * 1.3
                        + intake_sound * 1.6
                        + supercharger_sound * 1.2
                        + crackle_burst * 0.75  # Muffled cabin pop thud
                    )
                else:
                    # --- 실외 배기구 (Exterior Tailpipe) ---
                    # Raw, open, raspy, full-frequency sound
                    combined_mono = (
                        raw_exhaust
                        + intake_sound * 0.45
                        + supercharger_sound
                    )

                # 12. Non-linear Saturation & Analog Tube Warmth (Loudness Maximizer)
                drive = 1.0 + self.distortion * 2.2 * (0.8 + 0.6 * self.throttle)
                saturated = np.tanh(combined_mono * drive * 0.55)

                # 13. GTA / 3D Real-Game Stereo Spatializer (Binaural & Early Reflections)
                # Simulates dual-exhaust separation, cabin early reflections, and wide sound field
                p_len = self.spatial_buf_len
                ptr = self.spatial_ptr

                left_out = np.zeros(frames, dtype=np.float32)
                right_out = np.zeros(frames, dtype=np.float32)

                # Interaural time difference (ITD) delay for wide stereo (~0.7ms = 31 samples)
                delay_itd = int(0.00075 * self.sample_rate)
                # Cabin / Exhaust reflection delay (~18ms = 794 samples)
                delay_echo = int(0.016 * self.sample_rate)

                w_factor = self.stereo_width

                for n in range(frames):
                    inp = saturated[n]

                    # Push into stereo delay lines
                    self.spatial_buf_l[ptr] = inp
                    self.spatial_buf_r[ptr] = inp

                    # Read delayed samples
                    r_l = (ptr - delay_itd) % p_len
                    r_echo = (ptr - delay_echo) % p_len

                    delayed_sample = self.spatial_buf_l[r_l]
                    reverb_sample = self.spatial_buf_l[r_echo] * 0.22

                    # Mid/Side stereo widening
                    mid = inp
                    side = (inp - delayed_sample) * w_factor * 0.75

                    left_out[n] = (mid + side) + reverb_sample
                    right_out[n] = (mid - side) + reverb_sample * 0.85

                    ptr = (ptr + 1) % p_len

                self.spatial_ptr = ptr

                # 14. DC Blocking Filter & Master Limiting
                for n in range(frames):
                    # Left
                    xl = left_out[n]
                    yl = xl - self.dc_x1_l + 0.995 * self.dc_y1_l
                    self.dc_x1_l, self.dc_y1_l = xl, yl
                    left_out[n] = yl

                    # Right
                    xr = right_out[n]
                    yr = xr - self.dc_x1_r + 0.995 * self.dc_y1_r
                    self.dc_x1_r, self.dc_y1_r = xr, yr
                    right_out[n] = yr

                # Master Gain & Brickwall Limiter
                final_l = np.clip(left_out * self.master_volume * 0.92, -0.98, 0.98)
                final_r = np.clip(right_out * self.master_volume * 0.92, -0.98, 0.98)

                outdata[:, 0] = final_l
                outdata[:, 1] = final_r

                # Waveform monitor (mono average for visualizer)
                self.latest_waveform[:] = (final_l + final_r) * 0.5

        except Exception as e:
            outdata.fill(0)

    def start(self):
        """Start low-latency audio stream."""
        if self.is_running:
            return
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            blocksize=self.buffer_size,
            channels=2,
            dtype="float32",
            callback=self._audio_callback,
        )
        self.stream.start()
        self.is_running = True

    def stop(self):
        """Stop audio stream."""
        if not self.is_running:
            return
        self.is_running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None


if __name__ == "__main__":
    print("Testing upgraded High-Fidelity Exhaust DSP with Cabin & 3D Spatial Audio...")
    synth = ExhaustSoundSynthesizer()
    synth.set_model("muscle_v8")
    synth.start()

    print("1. Playing Exterior Tailpipe View...")
    synth.set_perspective("exterior")
    synth.set_rpm(3500)
    synth.set_throttle(0.8)
    time.sleep(2.0)

    print("2. Switching to Cockpit (Cabin) Interior View...")
    synth.set_perspective("cabin")
    time.sleep(2.5)

    print("3. Cabin Heavy Throttle (Intake Roar & Chassis Boom)...")
    synth.set_throttle(1.0)
    synth.set_rpm(5000)
    time.sleep(2.0)

    print("4. Decel Throttle Lift (Cabin Muffled Pop Thud)...")
    synth.set_throttle(0.0)
    synth.set_rpm(1200)
    time.sleep(2.0)

    synth.stop()
    print("DSP Test complete!")
