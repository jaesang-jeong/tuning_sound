"""
PCAN-USB Pro Hardware Interface & High-Speed Read-Only CAN Manager
Supports:
  1. Safe Listen-Only (Read-Only) mode without transmission (Prevents bus-off / crashes when disconnected).
  2. Ultra-low latency (10ms / 100Hz) passive sniffing of broadcast frames (Hyundai/Kia, BMW, VAG, GM).
  3. Automatic OBD-II fallback polling with robust error recovery.
"""

import time
import threading
from typing import Callable, Optional, List, Dict, Any

try:
    import can
    from can.bus import BusState
    from can.interfaces.pcan.basic import (
        PCANBasic,
        PCAN_USBBUS1,
        PCAN_USBBUS2,
        PCAN_USBBUS3,
        PCAN_USBBUS4,
        PCAN_CHANNEL_AVAILABLE,
        PCAN_CHANNEL_OCCUPIED,
        PCAN_CHANNEL_CONDITION,
        PCAN_ERROR_OK,
    )
    PCAN_AVAILABLE = True
except Exception:
    PCAN_AVAILABLE = False


PCAN_CHANNELS = {
    "PCAN_USBBUS1 (채널 1)": "PCAN_USBBUS1",
    "PCAN_USBBUS2 (채널 2)": "PCAN_USBBUS2",
    "PCAN_USBBUS3 (채널 3)": "PCAN_USBBUS3",
    "PCAN_USBBUS4 (채널 4)": "PCAN_USBBUS4",
}

PCAN_CHANNEL_CONSTS = {
    "PCAN_USBBUS1": 0x51,
    "PCAN_USBBUS2": 0x52,
    "PCAN_USBBUS3": 0x53,
    "PCAN_USBBUS4": 0x54,
}

# Major Automaker High-Speed Broadcast Presets (10ms / 100Hz native ECU broadcast)
CAR_BROADCAST_PRESETS = {
    "현대 / 기아 / 제네시스 (0x316)": {
        "can_id": 0x316,
        "rpm_start_byte": 2,
        "rpm_length": 2,
        "rpm_scale": 0.25,
        "rpm_byteorder": "little",
        "throttle_start_byte": 4,
        "throttle_scale": 0.392,
        "description": "현대/기아 C-CAN 500k 표준 10ms 주기 엔진 텔레메트리"
    },
    "BMW (PT-CAN 0x0A5)": {
        "can_id": 0x0A5,
        "rpm_start_byte": 4,
        "rpm_length": 2,
        "rpm_scale": 0.25,
        "rpm_byteorder": "little",
        "throttle_start_byte": 2,
        "throttle_scale": 0.392,
        "description": "BMW PT-CAN 500k 10ms 주기 토크/RPM 프레임"
    },
    "폭스바겐 / 아우디 / 포르쉐 (VAG 0x280)": {
        "can_id": 0x280,
        "rpm_start_byte": 2,
        "rpm_length": 2,
        "rpm_scale": 0.25,
        "rpm_byteorder": "little",
        "throttle_start_byte": 5,
        "throttle_scale": 0.392,
        "description": "VAG Motor 1 고속 10ms 주기 엔진 브로드캐스트"
    },
    "GM / 쉐보레 (GMLAN 0x0C9)": {
        "can_id": 0x0C9,
        "rpm_start_byte": 1,
        "rpm_length": 2,
        "rpm_scale": 0.25,
        "rpm_byteorder": "big",
        "throttle_start_byte": 3,
        "throttle_scale": 0.392,
        "description": "GM 고속 Powertrain CAN 프레임"
    },
}


class PcanManager:
    """
    High-performance, crash-proof PCAN-USB Pro interface manager.
    Supports Read-Only (Listen-Only) passive sniffing and active OBD-II polling.
    """
    def __init__(self):
        self.bus: Optional[can.BusABC] = None
        self.is_connected = False
        self.running = False
        self.channel_name = "PCAN_USBBUS1"
        self.bitrate = 500000

        # Operational Modes:
        # 1) 'READ_ONLY_AUTO'   : Pure passive sniffing (No TX packets, never crashes without OBD2)
        # 2) 'READ_ONLY_PRESET' : Sniffing specific car preset (Hyundai/BMW/VAG/GM)
        # 3) 'READ_ONLY_CUSTOM' : User specified CAN ID
        # 4) 'OBD2_POLL'        : Active request PID 0x0C (Only when OBD2 is connected)
        self.mode = "READ_ONLY_PRESET"
        self.preset_name = "현대 / 기아 / 제네시스 (0x316)"

        # Custom Sniffing Config
        self.custom_can_id = 0x316
        self.rpm_start_byte = 2
        self.rpm_length = 2
        self.rpm_scale = 0.25
        self.rpm_offset = 0.0
        self.rpm_byteorder = "little"
        self.throttle_start_byte = 4
        self.throttle_scale = 0.392

        # Threading
        self.rx_thread: Optional[threading.Thread] = None
        self.poll_thread: Optional[threading.Thread] = None

        # Callbacks (Thread-safe signaling to GUI)
        self.on_telemetry_update: Optional[Callable[[float, float, float], None]] = None
        self.on_status_change: Optional[Callable[[str, bool], None]] = None
        self.on_can_log: Optional[Callable[[str], None]] = None

        # Telemetry Cache
        self.current_rpm = 0.0
        self.current_load = 0.0      # Calculated Engine Load (0.0 ~ 1.0)
        self.current_throttle = 0.0  # Throttle Position (0.0 ~ 1.0)
        self.current_speed = 0.0
        self.messages_count = 0
        self.last_msg_timestamp = 0.0

        # Auto-Discovery State (Tracks candidate IDs with RPM-like dynamic values)
        self.id_freq_map: Dict[int, int] = {}
        self.auto_detected_id: Optional[int] = None

    @staticmethod
    def scan_pcan_hardware() -> List[Dict[str, Any]]:
        """Scans for connected PEAK PCAN-USB / PCAN-USB Pro adapters."""
        results = []
        if not PCAN_AVAILABLE:
            return results

        try:
            pcan = PCANBasic()
            for ch_name, ch_code in PCAN_CHANNEL_CONSTS.items():
                res, status = pcan.GetValue(ch_code, PCAN_CHANNEL_CONDITION)
                if res == PCAN_ERROR_OK:
                    is_avail = (status == PCAN_CHANNEL_AVAILABLE)
                    is_occ = (status == PCAN_CHANNEL_OCCUPIED)
                    results.append({
                        "channel": ch_name,
                        "status_code": status,
                        "available": is_avail or is_occ,
                        "occupied": is_occ,
                        "label": f"{ch_name} - {'연결됨(준비완료)' if is_avail else ('사용중' if is_occ else '장치없음')}"
                    })
        except Exception:
            pass
        return results

    def connect(
        self,
        channel: str = "PCAN_USBBUS1",
        bitrate: int = 500000,
        mode: str = "READ_ONLY_PRESET",
        preset_name: str = "현대 / 기아 / 제네시스 (0x316)"
    ) -> bool:
        """
        Connects to PCAN-USB Pro.
        In READ_ONLY modes, sets hardware to Listen-Only (PASSIVE) so it NEVER crashes
        even if the OBD-II cable is completely disconnected or has no termination.
        """
        self.disconnect()
        self.channel_name = channel
        self.bitrate = bitrate
        self.mode = mode
        self.preset_name = preset_name

        # Load preset if chosen
        if preset_name in CAR_BROADCAST_PRESETS:
            cfg = CAR_BROADCAST_PRESETS[preset_name]
            self.custom_can_id = cfg["can_id"]
            self.rpm_start_byte = cfg["rpm_start_byte"]
            self.rpm_length = cfg["rpm_length"]
            self.rpm_scale = cfg["rpm_scale"]
            self.rpm_byteorder = cfg["rpm_byteorder"]
            self.throttle_start_byte = cfg["throttle_start_byte"]
            self.throttle_scale = cfg["throttle_scale"]

        try:
            # Use Listen-Only (PASSIVE) for all Read-Only modes
            is_read_only = (mode != "OBD2_POLL")
            bus_state = BusState.PASSIVE if is_read_only else BusState.ACTIVE

            # Cross-platform interface selection:
            # On Linux (Raspberry Pi), default to SocketCAN ('can0')
            # On Windows, default to PEAK PCAN ('pcan')
            if sys.platform.startswith("linux") or str(channel).lower().startswith("can"):
                target_interface = "socketcan"
                target_channel = channel if str(channel).lower().startswith("can") else "can0"
                self.bus = can.Bus(
                    interface=target_interface,
                    channel=target_channel
                )
            else:
                self.bus = can.Bus(
                    interface="pcan",
                    channel=channel,
                    bitrate=bitrate,
                    state=bus_state
                )
            self.is_connected = True
            self.running = True
            self.messages_count = 0
            self.id_freq_map.clear()
            self.auto_detected_id = None

            # Start RX loop
            self.rx_thread = threading.Thread(target=self._rx_worker, daemon=True)
            self.rx_thread.start()

            # Start OBD-II active polling loop ONLY if active mode is explicitly selected
            if mode == "OBD2_POLL":
                self.poll_thread = threading.Thread(target=self._obd_poll_worker, daemon=True)
                self.poll_thread.start()

            mode_label = "Read-Only 초고속 수신" if is_read_only else "OBD-II 요청 송출 모드"
            if self.on_status_change:
                self.on_status_change(f"PCAN 연결 성공 ({channel} @ {bitrate//1000}k, {mode_label})", True)
            return True

        except Exception as e:
            self.is_connected = False
            if self.on_status_change:
                self.on_status_change(f"PCAN 연결 실패: {str(e)}", False)
            return False

    def disconnect(self):
        """Safely disconnects PCAN adapter."""
        self.running = False
        if self.poll_thread:
            try:
                self.poll_thread.join(timeout=0.3)
            except Exception:
                pass
            self.poll_thread = None

        if self.rx_thread:
            try:
                self.rx_thread.join(timeout=0.3)
            except Exception:
                pass
            self.rx_thread = None

        if self.bus:
            try:
                self.bus.shutdown()
            except Exception:
                pass
            self.bus = None

        self.is_connected = False
        if self.on_status_change:
            self.on_status_change("PCAN-USB Pro 연결 해제됨", False)

    def _obd_poll_worker(self):
        """Active OBD-II PID polling: Engine RPM (0x0C), Calculated Engine Load (0x04), Throttle (0x11)."""
        rpm_query = can.Message(
            arbitration_id=0x7DF,
            data=[0x02, 0x01, 0x0C, 0x55, 0x55, 0x55, 0x55, 0x55],
            is_extended_id=False
        )
        load_query = can.Message(
            arbitration_id=0x7DF,
            data=[0x02, 0x01, 0x04, 0x55, 0x55, 0x55, 0x55, 0x55],
            is_extended_id=False
        )
        throttle_query = can.Message(
            arbitration_id=0x7DF,
            data=[0x02, 0x01, 0x11, 0x55, 0x55, 0x55, 0x55, 0x55],
            is_extended_id=False
        )

        poll_counter = 0
        consecutive_errors = 0

        while self.running and self.bus:
            try:
                # If OBD2 is not connected, bus.send will fail with ACK error.
                # Catch it safely so the thread NEVER crashes the application!
                self.bus.send(rpm_query, timeout=0.05)
                consecutive_errors = 0
                poll_counter += 1

                # Poll Calculated Load (PID 0x04) every 2nd cycle (~16Hz)
                if poll_counter % 2 == 0:
                    self.bus.send(load_query, timeout=0.05)
                # Poll Throttle (PID 0x11) every 4th cycle (~8Hz)
                elif poll_counter % 4 == 0:
                    self.bus.send(throttle_query, timeout=0.05)

                time.sleep(0.030)  # ~33Hz query

            except Exception:
                consecutive_errors += 1
                # Exponential backoff when disconnected to save CPU and avoid bus-off locks
                sleep_time = min(1.0, 0.1 * consecutive_errors)
                time.sleep(sleep_time)

    def _rx_worker(self):
        """High-speed zero-copy packet receiver."""
        log_timer = 0.0

        while self.running and self.bus:
            try:
                msg = self.bus.recv(timeout=0.05)
                if msg is None:
                    continue

                # Filter out hardware error frames and PCAN internal status frames (e.g. 0x004)
                if getattr(msg, "is_error_frame", False) or msg.arbitration_id < 0x010:
                    continue

                self.messages_count += 1
                now = time.time()
                self.last_msg_timestamp = now
                data = msg.data
                arb_id = msg.arbitration_id

                # Rate-limited UI logging (max 10 logs per second to prevent GUI lag)
                if self.on_can_log and (now - log_timer > 0.08):
                    log_timer = now
                    data_hex = " ".join(f"{b:02X}" for b in data)
                    self.on_can_log(f"ID: 0x{arb_id:03X}  DLC: {len(data)}  Data: {data_hex}")

                rpm = None
                throttle = None
                speed = None

                # 1. Read-Only Broadcast Sniffing (Preset or Custom CAN ID)
                if self.mode in ("READ_ONLY_PRESET", "READ_ONLY_CUSTOM"):
                    if arb_id == self.custom_can_id:
                        sb = self.rpm_start_byte
                        lb = self.rpm_length
                        if len(data) >= (sb + lb):
                            raw_rpm = int.from_bytes(data[sb : sb + lb], byteorder=self.rpm_byteorder)
                            val = raw_rpm * self.rpm_scale + self.rpm_offset
                            if 400.0 <= val <= 11000.0:
                                rpm = val
                                self.current_rpm = rpm

                        tb = self.throttle_start_byte
                        if len(data) > tb:
                            th_val = (data[tb] * self.throttle_scale) / 100.0
                            val_norm = max(0.0, min(1.0, th_val))
                            self.current_load = val_norm
                            self.current_throttle = val_norm
                            throttle = val_norm

                # 2. Auto-Discovery Mode (Scans all incoming IDs for RPM patterns)
                elif self.mode == "READ_ONLY_AUTO":
                    # Look for 10ms~20ms high-frequency frames with values between 600 and 7500
                    if len(data) >= 4:
                        # Test common 16-bit slots (bytes 1-2, 2-3, 3-4, 4-5)
                        for start_b in [1, 2, 3, 4]:
                            if len(data) >= start_b + 2:
                                for bo in ["little", "big"]:
                                    test_val = int.from_bytes(data[start_b : start_b + 2], byteorder=bo) * 0.25
                                    if 550.0 <= test_val <= 8500.0:
                                        rpm = test_val
                                        self.current_rpm = rpm
                                        self.auto_detected_id = arb_id
                                        break
                                if rpm is not None:
                                    break

                # 3. Active OBD-II response decoding (0x7E8 ~ 0x7EF)
                elif self.mode == "OBD2_POLL":
                    if 0x7E8 <= arb_id <= 0x7EF and len(data) >= 3:
                        service = data[1]
                        pid = data[2]
                        if service == 0x41:
                            if pid == 0x0C and len(data) >= 5:  # Engine RPM
                                raw_val = (data[3] << 8) | data[4]
                                rpm = raw_val / 4.0
                                self.current_rpm = rpm
                            elif pid == 0x04 and len(data) >= 4:  # Calculated Engine Load (0~100%)
                                load_val = data[3] / 255.0
                                self.current_load = load_val
                                self.current_throttle = load_val
                                throttle = load_val
                            elif pid == 0x11 and len(data) >= 4:  # Throttle Position (0~100%)
                                th_val = data[3] / 255.0
                                if self.current_load == 0.0:
                                    self.current_load = th_val
                                self.current_throttle = th_val
                                throttle = th_val
                            elif pid == 0x0D and len(data) >= 4:  # Speed
                                speed = float(data[3])
                                self.current_speed = speed

                if (rpm is not None or throttle is not None) and self.on_telemetry_update:
                    self.on_telemetry_update(self.current_rpm, self.current_throttle, self.current_speed)

            except Exception:
                pass


if __name__ == "__main__":
    print("Testing PCAN Read-Only Manager...")
    mgr = PcanManager()
    devices = mgr.scan_pcan_hardware()
    print(f"Detected {len(devices)} PCAN channels.")
    for d in devices:
        print(" -", d["label"])
