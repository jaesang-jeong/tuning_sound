"""
CAN Bus Interface & Virtual Vehicle Simulator Module
Supports both hardware CAN adapters (via python-can) and an advanced Virtual Vehicle Physics Simulator.
Compatible with standard OBD-II PIDs and custom vehicle CAN broadcast frames.
Easily portable to standalone embedded Linux / Raspberry Pi systems (SocketCAN / SLCAN).
"""

import time
import threading
from typing import Callable, Optional
import can


class VirtualVehicleSimulator:
    """
    Simulates realistic sports car physics, automatic DCT 7-speed transmission,
    RPM curve, throttle dynamics, speed, and decel overrun.
    """
    def __init__(self, idle_rpm: float = 850.0, redline_rpm: float = 9000.0):
        self.idle_rpm = idle_rpm
        self.redline_rpm = redline_rpm
        # Gear max speeds in km/h at redline
        self.gear_max_speeds = [65.0, 110.0, 160.0, 215.0, 270.0, 325.0, 360.0]

        # Dynamic State
        self.rpm = idle_rpm
        self.speed_kmh = 0.0
        self.current_gear = 1
        self.throttle = 0.0
        self.brake = 0.0
        self.is_neutral = False  # Neutral revving mode toggle

        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.callback: Optional[Callable[[float, float, float, int], None]] = None

    def start(self, callback: Callable[[float, float, float, int], None]):
        self.callback = callback
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None

    def set_inputs(self, throttle: float, brake: float, neutral: bool = None):
        self.throttle = max(0.0, min(float(throttle), 1.0))
        self.brake = max(0.0, min(float(brake), 1.0))
        if neutral is not None:
            self.is_neutral = neutral

    def _update_loop(self):
        dt = 0.033  # ~30Hz update rate
        while self.running:
            start_time = time.time()

            if self.is_neutral:
                # Free-revving in neutral
                target_rpm = self.idle_rpm + self.throttle * (self.redline_rpm - self.idle_rpm)
                if target_rpm > self.rpm:
                    self.rpm += (target_rpm - self.rpm) * 0.22  # Crisp throttle response
                else:
                    self.rpm += (target_rpm - self.rpm) * 0.12  # Natural rev drop
                # Speed bleeds off
                self.speed_kmh = max(0.0, self.speed_kmh - 2.5 * dt)
            else:
                # In Gear Drive
                max_spd = self.gear_max_speeds[self.current_gear - 1]
                gear_accel_factor = (len(self.gear_max_speeds) - self.current_gear + 2) / 3.0

                if self.throttle > 0.02:
                    accel = (self.throttle * 38.0 * gear_accel_factor) - (self.brake * 55.0)
                else:
                    # Engine braking & drag
                    accel = -6.5 - (self.speed_kmh * 0.04) - (self.brake * 60.0)

                self.speed_kmh = max(0.0, min(360.0, self.speed_kmh + accel * dt))

                # Upshift logic
                if self.speed_kmh >= (max_spd * 0.94) and self.current_gear < len(self.gear_max_speeds):
                    self.current_gear += 1
                # Downshift logic
                elif self.current_gear > 1:
                    prev_max_spd = self.gear_max_speeds[self.current_gear - 2]
                    if self.speed_kmh < (prev_max_spd * 0.65):
                        self.current_gear -= 1

                # Calculate RPM based on current gear's speed fraction
                curr_max_spd = self.gear_max_speeds[self.current_gear - 1]
                prev_ratio = 0.0 if self.current_gear == 1 else self.gear_max_speeds[self.current_gear - 2]
                speed_ratio = self.speed_kmh / curr_max_spd

                calculated_rpm = self.idle_rpm + speed_ratio * (self.redline_rpm - self.idle_rpm)

                # Idle revving if car is stationary and stopped
                if self.speed_kmh < 1.0 and self.throttle > 0.05:
                    target_rev = self.idle_rpm + self.throttle * 3500.0
                    self.rpm += (target_rev - self.rpm) * 0.2
                else:
                    self.rpm = min(self.redline_rpm, max(self.idle_rpm, calculated_rpm))

            if self.callback:
                self.callback(self.rpm, self.throttle, self.speed_kmh, self.current_gear)

            elapsed = time.time() - start_time
            sleep_time = max(0.001, dt - elapsed)
            time.sleep(sleep_time)


class CanReceiver:
    """
    CAN Bus receiver supporting OBD-II PID decoding and custom DBC-style frame parsing.
    Works seamlessly across Windows, Linux (Raspberry Pi SocketCAN), and USB-CAN bridges (slcan).
    """
    def __init__(self):
        self.bus: Optional[can.BusABC] = None
        self.is_connected = False
        self.running = False
        self.thread: Optional[threading.Thread] = None

        # Callbacks
        self.on_data_received: Optional[Callable[[float, float, float], None]] = None  # rpm, throttle, speed
        self.on_status_change: Optional[Callable[[str, bool], None]] = None

        # Decoding Configuration
        self.mode = "OBD2"  # "OBD2" or "CUSTOM"

        # Custom frame configuration
        self.custom_can_id = 0x316
        self.rpm_start_byte = 2
        self.rpm_length_bytes = 2
        self.rpm_scale = 0.25
        self.rpm_offset = 0.0
        self.rpm_byteorder = "little"  # "little" or "big"

        self.throttle_start_byte = 4
        self.throttle_scale = 0.392  # 100/255
        self.throttle_offset = 0.0

        # Stats
        self.messages_received = 0
        self.last_msg_time = 0.0

    def connect(
        self,
        interface: str = "virtual",
        channel: str = "0",
        bitrate: int = 500000,
        mode: str = "OBD2",
    ) -> bool:
        """
        Connect to CAN interface.
        Supported interfaces: 'virtual', 'slcan', 'pcan', 'socketcan', 'serial', etc.
        """
        self.disconnect()
        self.mode = mode

        try:
            kwargs = {"interface": interface, "bitrate": bitrate}
            if interface in ("virtual", "socketcan", "slcan", "serial"):
                kwargs["channel"] = channel

            self.bus = can.Bus(**kwargs)
            self.is_connected = True
            self.running = True

            self.thread = threading.Thread(target=self._rx_loop, daemon=True)
            self.thread.start()

            if self.on_status_change:
                self.on_status_change(f"연결 성공 ({interface}:{channel})", True)
            return True
        except Exception as e:
            self.is_connected = False
            if self.on_status_change:
                self.on_status_change(f"연결 실패: {str(e)}", False)
            return False

    def disconnect(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
        if self.bus:
            try:
                self.bus.shutdown()
            except Exception:
                pass
            self.bus = None
        self.is_connected = False
        if self.on_status_change:
            self.on_status_change("연결 해제됨", False)

    def _rx_loop(self):
        while self.running and self.bus:
            try:
                msg = self.bus.recv(timeout=0.1)
                if msg is None:
                    continue

                self.messages_received += 1
                self.last_msg_time = time.time()
                data = msg.data

                rpm = None
                throttle = None
                speed = 0.0

                if self.mode == "OBD2":
                    # Standard OBD-II Response CAN ID: 0x7E8 ~ 0x7EF
                    if 0x7E8 <= msg.arbitration_id <= 0x7EF and len(data) >= 3:
                        service = data[1]
                        pid = data[2]
                        if service == 0x41:  # Show Current Data response
                            if pid == 0x0C and len(data) >= 5:  # Engine RPM
                                raw_val = (data[3] << 8) | data[4]
                                rpm = raw_val / 4.0
                            elif pid == 0x11 and len(data) >= 4:  # Throttle Position
                                throttle = data[3] / 255.0
                            elif pid == 0x0D and len(data) >= 4:  # Vehicle Speed
                                speed = float(data[3])

                elif self.mode == "CUSTOM":
                    if msg.arbitration_id == self.custom_can_id:
                        # Extract RPM
                        sb = self.rpm_start_byte
                        lb = self.rpm_length_bytes
                        if len(data) >= (sb + lb):
                            slice_bytes = data[sb : sb + lb]
                            raw_rpm = int.from_bytes(slice_bytes, byteorder=self.rpm_byteorder)
                            rpm = raw_rpm * self.rpm_scale + self.rpm_offset

                        # Extract Throttle
                        tb = self.throttle_start_byte
                        if len(data) > tb:
                            raw_throttle = data[tb]
                            throttle = (raw_throttle * self.throttle_scale + self.throttle_offset) / 100.0

                if rpm is not None and self.on_data_received:
                    th = throttle if throttle is not None else 0.0
                    self.on_data_received(rpm, th, speed)

            except Exception:
                pass


if __name__ == "__main__":
    print("Testing VirtualVehicleSimulator...")
    sim = VirtualVehicleSimulator()
    sim.start(lambda rpm, th, spd, gear: print(f"RPM: {rpm:.1f} | Throttle: {th*100:.0f}% | Speed: {spd:.1f}km/h | Gear: {gear}"))
    print("Applying 70% throttle...")
    sim.set_inputs(throttle=0.7, brake=0.0)
    time.sleep(2.0)
    print("Releasing throttle (Decel)...")
    sim.set_inputs(throttle=0.0, brake=0.0)
    time.sleep(2.0)
    sim.stop()
    print("Simulator test finished!")
