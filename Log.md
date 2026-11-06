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


## 2026-11-06 20:50 — FMOD DLL 감지 실패 원인 진단 및 64비트 로딩 지원

[DONE]
1. 수정 파일:
   - fmod_engine.py : `check_dll_arch`, `_load_fmod_dll`, `get_status_message`, `reload` : 32비트/64비트 PE 아키텍처 자동 판별 및 상세 진단 메시지, ctypes 핸들 정상화
   - app_gui.py : `_build_engine_choice_tab`, `_on_audio_backend_changed`, `_refresh_fmod_status` : FMOD DLL 32비트 불일치 안내문 표시 및 실시간 새로고침 버튼 추가
2. 검증:
   - `python -c "from fmod_engine import FmodEngineManager; f = FmodEngineManager(); print(f.get_status_message())"` → 현재 배치된 fmod.dll이 32비트(x86)임을 감지하고 64비트 경로 안내 원문 정상 출력
   - `python -c "from app_gui import ExhaustAppWindow; ..."` → 오프스크린 GUI에서 FMOD 진단 라벨 및 새로고침 버튼 정상 연동 확인
3. 미해결 / 제안:
   - FMOD 다운로드 폴더의 `api/core/lib/x64/fmod.dll` 파일을 복사하여 프로젝트 폴더에 덮어쓴 뒤 GUI의 새로고침 버튼 클릭 권장


## 2026-11-06 21:10 — 계산된 엔진 부하값(Calculated Engine Load) 연동 및 명확화

[DONE]
1. 수정 파일:
   - pcan_manager.py : `_obd_poll_worker`, `_rx_worker`, `__init__` : OBD-II PID 0x04 (Calculated Engine Load) 폴링 및 C-CAN 패킷 부하값 매핑 지원
   - app_gui.py : `_build_drive_mode_tab`, `_on_ui_tick` : 텔레메트리 표시를 '엔진 부하(Load)'로 명확화
2. 검증:
   - `python -c "from pcan_manager import PcanManager; ..."` → OBD-II PID 0x04 (Calculated Engine Load 50.2%) 및 PID 0x0C (RPM 3000) 정상 디코딩 확인
   - `python -m py_compile pcan_manager.py app_gui.py` → 정상 컴파일 확인
3. 미해결 / 제안:
   - 없음
