# Log — <프로젝트명>

> append-only. 기존 줄은 수정·삭제하지 않는다. 새 항목은 항상 파일 끝에.
> 형식: `## YYYY-MM-DD HH:MM — <작업 제목>` + [DONE] 블록

---


## 2026-11-06 20:27 — PCAN 미연결 크래시 해결 및 10ms 초고속 Read-Only 완성차 모드 구현

[DONE]
1. 수정 파일:
   - pcan_manager.py : `_rx_worker`, `connect` : 하드웨어 에러/상태 프레임(0x004) 필터링 및 Listen-Only 안정화
   - app_gui.py : `CanSignalBridge`, `_build_pcan_tab`, `_on_pcan_connect_clicked`, `_setup_connections` : Qt 크로스 스레드 크래시 방지 시그널 브릿지 및 Read-Only 완성차 프리셋 UI 연동
2. 검증:
   - `python -m py_compile app_gui.py pcan_manager.py` → 정상 컴파일(Exit code 0)
   - `python -c "from app_gui import ExhaustAppWindow; ..."` → 오프스크린 GUI에서 PCAN 미연결 연결 클릭 및 백그라운드 스레드 시그널 5회 수신 검증 정상 통과(No crash, No assertion error)
   - `python -c "from pcan_manager import PcanManager; ..."` → PCAN_USBBUS1 비활성 버스에서 READ_ONLY_PRESET 연결/해제 정상 확인
3. 미해결 / 제안:
   - 실제 차량의 OBD-II 포트 혹은 C-CAN 배선(차종별 핀아웃)에 직결하여 실차 주행 배기음 실시간 동기화 테스트 권장
