"""
PCAN-USB Pro Hardware Interface & Vehicle CAN Manager
Specialized for PEAK-System PCAN-USB Pro (Dual-Channel CAN/CAN-FD).
Handles hardware auto-detection, vehicle OBD-II polling, and custom broadcast sniffing.
"""

import time
import threading
from typing import Callable, Optional, List, Dict, Any

try:
    import can
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


class PcanManager:
    """
    High-performance PCAN-USB Pro interface manager.
    Supports active OBD-II PID querying and passive broadcast frame listening.
    """
    def __init__(self):
        self.bus: Optional[can.BusABC] = None
        self.is_connected = False
        self.running = False
        self.channel_name = "PCAN_USBBUS1"
        self.bitrate = 500000

        # Protocols: "OBD2_POLL" (Active PID request), "OBD2_PASSIVE", or "CUSTOM"
        self.protocol_mode = "OBD2_POLL"

        # Threading
        self.rx_thread: Optional[threading.Thread] = None
        self.poll_thread: Optional[threading.Thread] = None

        # Callbacks
        self.on_telemetry_update: Optional[Callable[[float, float, float], None]] = None  # rpm, throttle, speed
        self.on_status_change: Optional[Callable[[str, bool], None]] = None
        self.on_can_log: Optional[Callable[[str], None]] = None  # Raw frame log string

        # Custom Sniffing Config
        self.custom_can_id = 0x316
        self.rpm_start_byte = 2
        self.rpm_length = 2
        self.rpm_scale = 0.25
        self.rpm_offset = 0.0
        self.throttle_start_byte = 4
        self.throttle_scale = 0.392

        # Telemetry Cache
        self.current_rpm = 0.0
        self.current_throttle = 0.0
        self.current_speed = 0.0
        self.messages_count = 0
        self.last_msg_timestamp = 0.0

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
        mode: str = "OBD2_POLL"
    ) -> bool:
        """Connects to PCAN-USB Pro hardware."""
        self.disconnect()
        self.channel_name = channel
        self.bitrate = bitrate
        self.protocol_mode = mode

        try:
            self.bus = can.Bus(interface="pcan", channel=channel, bitrate=bitrate)
            self.is_connected = True
            self.running = True

            # Start RX loop
            self.rx_thread = threading.Thread(target=self._rx_worker, daemon=True)
            self.rx_thread.start()

            # Start OBD-II active query loop if mode is OBD2_POLL
            if mode == "OBD2_POLL":
                self.poll_thread = threading.Thread(target=self._obd_poll_worker, daemon=True)
                self.poll_thread.start()

            if self.on_status_change:
                self.on_status_change(f"PCAN-USB Pro 연결 성공 ({channel} @ {bitrate//1000}kbps)", True)
            return True

        except Exception as e:
            self.is_connected = False
            if self.on_status_change:
                self.on_status_change(f"PCAN 연결 실패: {str(e)}", False)
            return False

    def disconnect(self):
        """Disconnects PCAN adapter."""
        self.running = False
        if self.poll_thread:
            self.poll_thread.join(timeout=0.6)
            self.poll_thread = None
        if self.rx_thread:
            self.rx_thread.join(timeout=0.6)
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
        """Periodically queries standard OBD-II PID 0x0C (Engine RPM) and 0x11 (Throttle)."""
        # OBD-II functional broadcast request: CAN ID 0x7DF
        # [0x02, Service 0x01, PID, 0x55, 0x55, 0x55, 0x55, 0x55]
        rpm_query = can.Message(
            arbitration_id=0x7DF,
            data=[0x02, 0x01, 0x0C, 0x55, 0x55, 0x55, 0x55, 0x55],
            is_extended_id=False
        )
        throttle_query = can.Message(
            arbitration_id=0x7DF,
            data=[0x02, 0x01, 0x11, 0x55, 0x55, 0x55, 0x55, 0x55],
            is_extended_id=False
        )

        poll_counter = 0
        while self.running and self.bus:
            try:
                # Query RPM at ~33Hz (every 30ms)
                self.bus.send(rpm_query)
                poll_counter += 1

                # Query Throttle every 3 cycles (~11Hz)
                if poll_counter % 3 == 0:
                    self.bus.send(throttle_query)

                time.sleep(0.030)
            except Exception:
                time.sleep(0.050)

    def _rx_worker(self):
        """Receives and parses incoming CAN packets in real time."""
        while self.running and self.bus:
            try:
                msg = self.bus.recv(timeout=0.1)
                if msg is None:
                    continue

                self.messages_count += 1
                self.last_msg_timestamp = time.time()
                data = msg.data

                # Optional log callback
                if self.on_can_log and (self.messages_count % 5 == 0):
                    data_hex = " ".join(f"{b:02X}" for b in data)
                    self.on_can_log(f"ID: 0x{msg.arbitration_id:03X}  DLC: {len(data)}  Data: {data_hex}")

                rpm = None
                throttle = None
                speed = None

                # 1. Standard OBD-II response decoding (0x7E8 ~ 0x7EF)
                if 0x7E8 <= msg.arbitration_id <= 0x7EF and len(data) >= 3:
                    service = data[1]
                    pid = data[2]
                    if service == 0x41:  # Show Current Data response
                        if pid == 0x0C and len(data) >= 5:  # Engine RPM
                            raw_val = (data[3] << 8) | data[4]
                            rpm = raw_val / 4.0
                            self.current_rpm = rpm
                        elif pid == 0x11 and len(data) >= 4:  # Throttle Position
                            throttle = data[3] / 255.0
                            self.current_throttle = throttle
                        elif pid == 0x0D and len(data) >= 4:  # Vehicle Speed
                            speed = float(data[3])
                            self.current_speed = speed

                # 2. Custom CAN broadcast frame sniffing
                elif self.protocol_mode == "CUSTOM" and msg.arbitration_id == self.custom_can_id:
                    sb = self.rpm_start_byte
                    lb = self.rpm_length
                    if len(data) >= (sb + lb):
                        raw_rpm = int.from_bytes(data[sb : sb + lb], byteorder="little")
                        rpm = raw_rpm * self.rpm_scale + self.rpm_offset
                        self.current_rpm = rpm

                    tb = self.throttle_start_byte
                    if len(data) > tb:
                        throttle = (data[tb] * self.throttle_scale) / 100.0
                        self.current_throttle = throttle

                if (rpm is not None or throttle is not None) and self.on_telemetry_update:
                    self.on_telemetry_update(self.current_rpm, self.current_throttle, self.current_speed)

            except Exception:
                pass


if __name__ == "__main__":
    print("Testing PCAN hardware scan...")
    devices = PcanManager.scan_pcan_hardware()
    for d in devices:
        print(f" - {d['label']}")
