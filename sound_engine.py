"""
High-Fidelity Exhaust Sound DSP Engine
Hyper-realistic acoustic physical modeling of supercar & muscle car exhaust systems.
Models:
  - American Muscle V8 (6.2L Hemi / Big-Block with Cam Lope & Supercharger Whine)
  - Porsche 911 GT3 (4.0L Boxer Flat-6 Raspy Screamer)
  - Ferrari F8 / 458 (Flat-plane V8 High-pitch F1 Scream)
  - Maserati GranTurismo (Cross-plane V8 Deep Baritone Rumble)
  - Lamborghini Huracán (5.2L V10 Naturally Aspirated Beast Roar)

Acoustic Architecture:
  1. Crank-Synchronized Cylinder Blowdown Impulse Shockwaves (Crankshaft 720° Cycle)
  2. Engine-Specific Firing Angle Geometry & Unequal Bank Interference
  3. Cycle-to-Cycle Combustion Variability & Micro-Jitter (Removes 2D Synth / Game Tone)
  4. Acoustic Waveguide Pipe Delay & Comb Filtering (Hollow Metal Tailpipe Resonance)
  5. Helmholtz Muffler Resonator (Sub-bass Physical Punch 40Hz ~ 120Hz)
  6. High-Velocity Gas Flow Turbulence (Exhaust Hiss & Rasp)
  7. Muscle Car Rough Cam Idle Chop (Aggressive Valve Overlap)
  8. Mechanical Supercharger Whine (Roots / Twin-screw Blower Whistle)
  9. Non-linear Asymmetric Pipe Saturation & Exhaust Valve Bypass
  10. Deceleration Overrun Pop & Crackle Shockwaves (Backfire)
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
            # Cross-plane V8 irregular pulse intervals (90°-180°-270°-180° pattern)
            firing_angles=[0.0, 90.0, 270.0, 360.0, 450.0, 540.0, 630.0, 720.0][:8],
            pipe_delay_ms=13.5,         # Large bore dual 3-inch exhaust pipes (~595 samples)
            pipe_reflection=0.55,       # Strong chamber resonance
            helmholtz_freq=65.0,        # Massive sub-bass 65Hz chamber thud
            helmholtz_q=2.8,
            sub_rumble_gain=2.8,        # Heavy room-shaking rumble
            manifold_ring_freq=2.2,     # Low baritone manifold resonance
            valve_rasp=0.45,
            cam_lope_intensity=0.85,    # Aggressive cam lope chop (thump-thump-thump)
            has_supercharger=True,      # Roots blower whine
            description="6.2L V8 헤미/콜벳 빅블록. 불규칙한 캠 롭 찹(Cam Lope), 심장을 울리는 서브우퍼급 저음 럼블 및 슈퍼차저 휘슬.",
        ),
        "porsche_gt3": EngineProfile(
            key="porsche_gt3",
            name="포르쉐 911 GT3 (Flat-6)",
            cylinders=6,
            idle_rpm=850.0,
            redline_rpm=9000.0,
            # Boxer 6: 120° opposing cylinder firing
            firing_angles=[0.0, 120.0, 240.0, 360.0, 480.0, 600.0],
            pipe_delay_ms=9.8,          # Tuned equal-length headers (~430 samples)
            pipe_reflection=0.42,
            helmholtz_freq=135.0,       # Metallic boxer resonance
            helmholtz_q=4.2,
            sub_rumble_gain=1.3,
            manifold_ring_freq=4.5,     # High-pitched raspy metallic whine
            valve_rasp=0.85,            # Screaming raspy tone
            cam_lope_intensity=0.0,
            has_supercharger=False,
            description="수평대향 6기통 9,000 RPM. 앙칼지고 거친 금속성 고회전 비명과 독특한 박서 비트.",
        ),
        "ferrari_f8": EngineProfile(
            key="ferrari_f8",
            name="페라리 F8 / 458 (Flat-plane V8)",
            cylinders=8,
            idle_rpm=900.0,
            redline_rpm=9000.0,
            # Flat-plane V8: perfectly uniform 90° intervals (twin 4-cylinders)
            firing_angles=[0.0, 90.0, 180.0, 270.0, 360.0, 450.0, 540.0, 630.0],
            pipe_delay_ms=8.5,          # Short race headers (~375 samples)
            pipe_reflection=0.48,
            helmholtz_freq=180.0,       # F1 mid-high pipe pitch
            helmholtz_q=5.0,
            sub_rumble_gain=0.9,        # Clean low end, minimal rumble
            manifold_ring_freq=6.8,     # Extremely sharp F1 scream
            valve_rasp=0.95,
            cam_lope_intensity=0.0,
            has_supercharger=False,
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
            description="4.7L 크로스플레인 V8. 가슴을 울리는 깊고 웅장한 이탈리안 바리톤 저음과 폭발적인 디셀 버블.",
        ),
        "lamborghini_v10": EngineProfile(
            key="lamborghini_v10",
            name="람보르기니 우라칸 (V10)",
            cylinders=10,
            idle_rpm=850.0,
            redline_rpm=8800.0,
            # V10: 72° uniform firing intervals
            firing_angles=[0.0, 72.0, 144.0, 216.0, 288.0, 360.0, 432.0, 504.0, 576.0, 648.0],
            pipe_delay_ms=9.2,
            pipe_reflection=0.46,
            helmholtz_freq=145.0,
            helmholtz_q=4.0,
            sub_rumble_gain=1.5,
            manifold_ring_freq=5.2,     # Roaring odd-harmonic beast tone
            valve_rasp=0.90,
            cam_lope_intensity=0.0,
            has_supercharger=False,
            description="5.2L 자연흡기 V10. 맹렬하고 공격적인 맹수 울음소리와 날카로운 백파이어 팝.",
        ),
    }


class ExhaustSoundSynthesizer:
    """
    Hyper-Realistic Exhaust Sound DSP Engine.
    Combines physical cylinder shockwaves, acoustic pipe waveguides,
    combustion jitter, cam lope, and decel overrun backfires.
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
        self.rpm_velocity = 0.0

        # Crankshaft Angle (0.0 to 720.0 degrees)
        self.crank_angle_deg = 0.0
        self.supercharger_phase = 0.0
        self.cam_lope_phase = 0.0

        # Waveguide Pipe Delay Line (Circular Buffer for acoustic pipe reflections)
        self.pipe_max_len = int(sample_rate * 0.05) + 100  # Up to 50ms delay
        self.pipe_buffer = np.zeros(self.pipe_max_len, dtype=np.float32)
        self.pipe_write_idx = 0

        # Helmholtz Muffler Biquad Filter States
        self.muffler_x1 = 0.0
        self.muffler_x2 = 0.0
        self.muffler_y1 = 0.0
        self.muffler_y2 = 0.0

        # High-pass DC Blocker states
        self.dc_x1 = 0.0
        self.dc_y1 = 0.0

        # User Tuning Parameters
        self.master_volume = 0.85
        self.bass_boost = 1.0        # 0.2 ~ 3.0
        self.mid_punch = 1.0         # 0.2 ~ 3.0
        self.treble_scream = 1.0     # 0.2 ~ 3.0
        self.valve_open = True       # Straight-pipe bypass (Sport / Corsa mode)
        self.pop_and_bang_enabled = True
        self.pop_intensity_mod = 1.2 # 0.0 ~ 2.5
        self.distortion = 0.4        # 0.0 ~ 1.0 (raspy saturation)
        self.supercharger_enabled = True  # Toggle supercharger whine for muscle car

        # Decel Crackle State
        self.crackle_energy = 0.0

        # Audio Stream management
        self.stream = None
        self.is_running = False
        self.lock = threading.Lock()

        # Monitoring waveform buffer (for GUI oscilloscope)
        self.latest_waveform = np.zeros(buffer_size, dtype=np.float32)

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

    def _audio_callback(self, outdata, frames, time_info, status):
        """Ultra-low latency real-time physical DSP render callback."""
        try:
            with self.lock:
                # 1. Smooth dynamic physics transition
                rpm_smooth = self.rpm + (self.target_rpm - self.rpm) * 0.22
                throttle_smooth = self.throttle + (self.target_throttle - self.throttle) * 0.30
                rpm_delta = rpm_smooth - self.rpm
                self.rpm = rpm_smooth
                self.throttle = throttle_smooth

                # Detect deceleration overrun (throttle lifted from high load or revs dropping)
                is_decel = (self.prev_throttle > 0.14 and self.throttle < 0.08) or (rpm_delta < -25.0 and self.rpm > 2400)
                self.prev_throttle = self.throttle

                prof = self.profile

                # Crankshaft degrees per sample
                # (RPM / 60) * 360 deg/sec = RPM * 6.0 deg/sec
                deg_per_sample = (self.rpm * 6.0) / self.sample_rate

                # Crank angle vector for this buffer block
                sample_cranks = (self.crank_angle_deg + np.arange(frames, dtype=np.float32) * deg_per_sample) % 720.0
                self.crank_angle_deg = (self.crank_angle_deg + frames * deg_per_sample) % 720.0

                # 2. Cam Lope Modulation (Aggressive Muscle Car Idle Chop)
                if prof.cam_lope_intensity > 0.0 and self.rpm < 1300.0:
                    idle_blend = max(0.0, 1.0 - (self.rpm - prof.idle_rpm) / 500.0)
                    self.cam_lope_phase += 2.0 * np.pi * 5.8 * frames / self.sample_rate  # ~5.8 Hz rhythmic lope
                    lope_mod = (
                        0.40 * np.sin(self.cam_lope_phase)
                        + 0.25 * np.sin(self.cam_lope_phase * 0.5 + 0.8)
                    ) * prof.cam_lope_intensity * idle_blend
                else:
                    lope_mod = 0.0

                # 3. Synthesize Cylinder Blowdown Impulse Shockwaves
                # Sum individual cylinder exhaust valve opening (EVO) pressure waves
                shockwave = np.zeros(frames, dtype=np.float32)
                pulse_duration_deg = 180.0
                rise_deg = 18.0

                # Engine load widens and sharpens pressure wave
                load_punch = 0.55 + 1.25 * self.throttle
                valve_mult = 1.35 if self.valve_open else 0.85

                for idx, firing_angle in enumerate(prof.firing_angles):
                    # Angular offset past firing event
                    delta = (sample_cranks - firing_angle) % 720.0
                    mask = delta < pulse_duration_deg
                    if not np.any(mask):
                        continue

                    d = delta[mask]
                    p = np.zeros_like(d)

                    # Fast rise: sharp pressure expansion (acoustic shock)
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

                    # Cylinder-to-cylinder natural jitter & cam lope asymmetry
                    cyl_jitter = 1.0 + 0.06 * np.sin(idx * 2.39 + self.crank_angle_deg * 0.01)
                    if lope_mod != 0.0:
                        cyl_jitter += lope_mod * (0.6 if (idx % 2 == 0) else -0.6)

                    shockwave[mask] += p * cyl_jitter

                shockwave *= (load_punch * self.mid_punch)

                # 4. High-Velocity Turbulent Exhaust Flow Noise
                # Exhaust gas jetting from tailpipe (pink-tinted turbulence)
                flow_noise = np.random.normal(0.0, 0.05, frames).astype(np.float32)
                # Modulated by shockwave envelope and throttle
                flow_mod = np.abs(shockwave) * (0.2 + 0.8 * self.throttle)
                shockwave += flow_noise * flow_mod * 1.4

                # 5. Acoustic Waveguide Pipe Delay Line (Comb Filtering)
                # Simulates acoustic propagation down hollow exhaust headers and reflection at tailpipe
                pipe_delay_samples = int((prof.pipe_delay_ms / 1000.0) * self.sample_rate)
                pipe_delay_samples = max(64, min(pipe_delay_samples, self.pipe_max_len - 1))
                refl = prof.pipe_reflection * (1.1 if self.valve_open else 0.8)

                pipe_output = np.zeros(frames, dtype=np.float32)
                buf = self.pipe_buffer
                p_len = self.pipe_max_len
                w_ptr = self.pipe_write_idx

                # Fast circular buffer convolution
                for n in range(frames):
                    r_ptr = (w_ptr - pipe_delay_samples) % p_len
                    delayed_echo = buf[r_ptr]
                    # Inject input + acoustic reflection
                    cell = shockwave[n] + delayed_echo * refl
                    # Non-linear acoustic pipe compression
                    buf[w_ptr] = np.tanh(cell * 1.15) * 0.88
                    pipe_output[n] = buf[w_ptr]
                    w_ptr = (w_ptr + 1) % p_len

                self.pipe_write_idx = w_ptr

                # 6. Helmholtz Muffler Resonator (Deep Physical Sub-Bass Punch)
                # 2nd-order Biquad Bandpass filter extracting heavy bass rumble
                f0 = prof.helmholtz_freq
                q = prof.helmholtz_q
                w0 = 2.0 * np.pi * f0 / self.sample_rate
                alpha = np.sin(w0) / (2.0 * q)
                b0 = alpha
                b2 = -alpha
                a0 = 1.0 + alpha
                a1 = -2.0 * np.cos(w0)
                a2 = 1.0 - alpha

                b0 /= a0
                b2 /= a0
                a1 /= a0
                a2 /= a0

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

                # 7. Supercharger Whine (Optional for Muscle Car)
                supercharger_sound = np.zeros(frames, dtype=np.float32)
                if prof.has_supercharger and self.supercharger_enabled:
                    # Supercharger lobes spin at 2.4x engine RPM
                    sc_freq = (self.rpm / 60.0) * 2.4 * 4.0  # 4-lobe rotor whistle
                    t_vec = np.arange(frames, dtype=np.float32) / self.sample_rate
                    sc_phase_inc = 2.0 * np.pi * sc_freq / self.sample_rate
                    sc_phases = self.supercharger_phase + np.cumsum(np.full(frames, sc_phase_inc, dtype=np.float32))
                    self.supercharger_phase = (self.supercharger_phase + frames * sc_phase_inc) % (2.0 * np.pi * 1000.0)

                    # Supercharger screams louder under boost / throttle
                    sc_gain = (0.05 + 0.35 * (self.throttle ** 1.5)) * min(1.0, self.rpm / 3000.0)
                    supercharger_sound = (
                        np.sin(sc_phases)
                        + 0.35 * np.sin(sc_phases * 2.0)
                        + 0.15 * np.sin(sc_phases * 3.0)
                    ) * sc_gain * 0.45

                # 8. Deceleration Pops & Bangs (Overrun Backfire Shockwaves)
                crackle_burst = np.zeros(frames, dtype=np.float32)
                if self.pop_and_bang_enabled and (is_decel or (self.throttle < 0.05 and self.rpm > 2800.0)):
                    # Overrun fuel cut pop burst probability
                    pop_chance = 0.08 * self.pop_intensity_mod * (1.3 if self.current_key in ("muscle_v8", "maserati_gt") else 0.9)
                    if random.random() < pop_chance:
                        self.crackle_energy = 1.0

                if self.crackle_energy > 0.01:
                    t_crk = np.arange(frames, dtype=np.float32) / self.sample_rate
                    burst_noise = np.random.uniform(-1.0, 1.0, frames).astype(np.float32)
                    decay_env = np.exp(-t_crk * 30.0) * self.crackle_energy
                    # Pop = Heavy acoustic shockwave thud (65Hz) + sharp metallic crack
                    thud = np.sin(2.0 * np.pi * 65.0 * t_crk) * 1.6
                    sharp_crack = burst_noise * 1.2
                    crackle_burst = (thud + sharp_crack) * decay_env * 1.6 * self.pop_intensity_mod
                    self.crackle_energy *= 0.58

                # 9. Blend Acoustic Components
                # Combine:
                # - Hollow metal pipe reflection (pipe_output)
                # - Deep Helmholtz sub-bass rumble (muffler_rumble * bass_boost)
                # - High-frequency rasp and valve scream (treble_scream)
                # - Supercharger whine
                # - Decel overrun crackles
                total_bass = muffler_rumble * prof.sub_rumble_gain * self.bass_boost * 2.2
                total_mid = pipe_output * 0.85
                valve_scream = shockwave * prof.valve_rasp * self.treble_scream * valve_mult * 0.45

                blended = total_mid + total_bass + valve_scream + supercharger_sound + crackle_burst

                # 10. Exhaust Valve Rasp & Analog Saturation (Non-linear warm overdrive)
                drive = 1.0 + self.distortion * 2.2 * (0.8 + 0.6 * self.throttle)
                saturated = np.tanh(blended * drive * 0.55)

                # DC-blocking filter (removes any DC drift)
                out_block = np.zeros(frames, dtype=np.float32)
                dc_x1, dc_y1 = self.dc_x1, self.dc_y1
                for n in range(frames):
                    x = saturated[n]
                    y = x - dc_x1 + 0.995 * dc_y1
                    dc_x1 = x
                    dc_y1 = y
                    out_block[n] = y
                self.dc_x1, self.dc_y1 = dc_x1, dc_y1

                # 11. Master Volume & Safe Limiting
                final_out = out_block * self.master_volume * 0.88
                final_out = np.clip(final_out, -0.98, 0.98)

                # Output stereo
                outdata[:] = np.column_stack((final_out, final_out))
                self.latest_waveform[:] = final_out

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
    print("Testing upgraded High-Fidelity Exhaust DSP...")
    synth = ExhaustSoundSynthesizer()
    synth.set_model("muscle_v8")
    synth.start()
    print("Playing American Muscle V8 Idle with Cam Lope...")
    time.sleep(2.5)
    print("Muscle V8 Heavy Revving (4000 RPM)...")
    synth.set_rpm(4000)
    synth.set_throttle(0.9)
    time.sleep(2.0)
    print("Decel Throttle Lift (Overrun Pop & Crackle)...")
    synth.set_throttle(0.0)
    synth.set_rpm(1200)
    time.sleep(2.0)
    synth.stop()
    print("DSP Test complete!")
