"""
Pure Data (Pd-vanilla) FUDI Socket Bridge
Streams real-time CAN RPM & Throttle telemetry from Python to Pure Data via TCP port 3000.
"""

import time
import socket
import threading
from typing import Optional, Callable


class PdBridgeManager:
    """Manages FUDI socket client connection to Pure Data (Pd-vanilla)."""
    def __init__(self, host: str = "127.0.0.1", port: int = 3000):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self.is_connected = False
        self.running = False
        self.thread: Optional[threading.Thread] = None

        self.rpm = 850.0
        self.throttle = 0.0

        self.on_status_change: Optional[Callable[[str, bool], None]] = None

    def connect(self) -> bool:
        """Connects to Pure Data netreceive socket."""
        self.disconnect()
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(1.5)
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(None)
            self.is_connected = True
            self.running = True

            self.thread = threading.Thread(target=self._tx_worker, daemon=True)
            self.thread.start()

            if self.on_status_change:
                self.on_status_change(f"Pure Data 연결됨 ({self.host}:{self.port})", True)
            return True
        except Exception as e:
            self.is_connected = False
            if self.on_status_change:
                self.on_status_change(f"Pure Data 연결 실패 (Pd에서 exhaust_synth.pd를 열어주세요): {e}", False)
            return False

    def disconnect(self):
        """Disconnects socket from Pure Data."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)
            self.thread = None
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        self.is_connected = False
        if self.on_status_change:
            self.on_status_change("Pure Data 연결 해제됨", False)

    def update_telemetry(self, rpm: float, throttle: float):
        """Updates internal target values."""
        self.rpm = rpm
        self.throttle = throttle

    def _tx_worker(self):
        """Streams FUDI formatted messages to Pure Data at ~30Hz."""
        while self.running and self.sock:
            try:
                # FUDI syntax: "selector arg1 arg2 ... ;\n"
                msg = f"rpm {self.rpm:.1f};\nthrottle {self.throttle:.2f};\n"
                self.sock.sendall(msg.encode("ascii"))
                time.sleep(0.033)
            except Exception:
                self.is_connected = False
                break
        self.disconnect()


if __name__ == "__main__":
    print("Testing PdBridgeManager...")
    bridge = PdBridgeManager()
    success = bridge.connect()
    print("Connected:", success)
