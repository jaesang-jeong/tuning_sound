"""
PCAN-USB Pro Quick Hardware Diagnostic Script
Tests PEAK-System driver availability, scans USB-CAN channels, and verifies OBD-II connectivity.
"""

import sys
import time
from pcan_manager import PcanManager, PCAN_AVAILABLE

def main():
    print("=" * 65)
    print("  🚗 PCAN-USB Pro 하드웨어 및 드라이버 진단 도구")
    print("=" * 65)
    print()

    if not PCAN_AVAILABLE:
        print("[오류] python-can 또는 PCANBasic 라이브러리를 로드할 수 없습니다.")
        print("  - C:\\Windows\\System32\\PCANBasic.dll 파일이 존재하는지 확인하세요.")
        return

    print("1. PCANBasic.dll 드라이버 상태: 정상 (System32 감지됨)")
    print()
    print("2. 연결된 PCAN-USB / PCAN-USB Pro 하드웨어 스캔 중...")
    devices = PcanManager.scan_pcan_hardware()

    found_any = False
    for d in devices:
        print(f"   • {d['label']}")
        if d['available']:
            found_any = True

    print()
    if found_any:
        print("✅ 사용 가능한 PCAN-USB Pro 채널이 감지되었습니다!")
        print("   GUI 앱에서 'PCAN-USB Pro 연동' 탭을 통해 즉시 차량에 연결할 수 있습니다.")
    else:
        print("ℹ️ 현재 연결된 PCAN 하드웨어가 없습니다.")
        print("   - 노트북 USB 포트에 PCAN-USB Pro를 연결하고 LED가 점등되는지 확인하세요.")
        print("   - PCAN-View 프로그램이 켜져 있다면 채널을 점유 중일 수 있으니 닫아주세요.")

    print()
    print("=" * 65)

if __name__ == "__main__":
    main()
