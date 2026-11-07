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


## 2026-11-06 21:34 — 라즈베리파이 3B 독립 장치 이식 (헤드리스 데몬 & systemd 서비스)

[DONE]
1. 수정 파일:
   - pcan_manager.py : `connect` : 리눅스/라즈베리파이 커널 내장 SocketCAN(can0) 자동 감지 및 크로스 플랫폼 연결 지원
   - headless_engine.py : 전체 : 라즈베리파이 3B용 경량 헤드리스 사운드 실행 데몬 구현
   - config_standalone.json : 전체 : 독립 장치 자동 부팅 시 적용할 사운드 모델/차종 프리셋 설정 파일 생성
   - tuning_sound.service : 전체 : 차량 시동 시 자동 실행 systemd 서비스 유닛 파일 생성
   - setup_rpi.sh : 전체 : 라즈베리파이 OS 환경 패키지 설치 및 SocketCAN 500k 원클릭 설정 스크립트 작성
2. 검증:
   - `python -m py_compile headless_engine.py pcan_manager.py` → 정상 컴파일 확인
   - `python -c "from headless_engine import HeadlessExhaustDaemon, load_config; ..."` → 헤드리스 데몬 시작, 오디오 스트림 오픈, CAN 대기, 종료 루틴 정상 확인
   - `python -c "from headless_engine import ...; test_sweep=True"` → 벤치 시뮬레이션 RPM 스윕 모드 정상 동작 확인
3. 미해결 / 제안:
   - 라즈베리파이 3B에 라즈베리파이 OS 설치 후 `bash setup_rpi.sh` 실행 권장


## 2026-11-07 05:04 — 라즈베리파이 3B 원본 환경 복구 스크립트(revert_rpi.sh) 작성

[DONE]
1. 수정 파일:
   - revert_rpi.sh : 전체 : systemd 서비스 정지 및 삭제, can0 네트워크 설정 복원, 파이썬/시스템 패키지 정리 스크립트 작성
   - setup_rpi.sh : 안내문 : 복구 명령어 가이드 추가
2. 검증:
   - `bash -n revert_rpi.sh` (구문 검증) 및 파일 생성 확인 완료
   - Git 커밋 `6721672` 원격 저장소 푸시 완료
3. 미해결 / 제안:
   - 없음


## 2026-11-07 09:47 — 라즈베리파이 차량 블루투스(A2DP) 페어링 및 부팅 시 자동 재연결 도우미 구현

[DONE]
1. 수정 파일:
   - bt_car_connect.sh : 전체 : 블루투스 검색, 차량 페어링, 신뢰 등록 및 부팅 시 자동 재연결 서비스(`bt_car_reconnect.service`) 원터치 스크립트 작성
   - setup_rpi.sh : [1/4] : 블루투스 A2DP 오디오 스택(bluez, libspa-0.2-bluetooth) 패키지 자동 설치 추가
   - revert_rpi.sh : [1/4] : 복구 시 블루투스 재연결 서비스 정리 로직 추가
2. 검증:
   - `bash -n bt_car_connect.sh` 구문 검증 완료
   - Git 커밋 `a3c6339` 원격 저장소 푸시 완료
3. 미해결 / 제안:
   - 차량 내비게이션 기기등록 대기 상태에서 `bash bt_car_connect.sh` 실행 권장


## 2026-11-07 10:02 — 라즈베리파이 3B 부팅 시간 초고속 단축(4~6초) 최적화

[DONE]
1. 수정 파일:
   - tuning_sound.service : `[Unit]`, `[Service]` : 네트워크 대기(network.target) 의존성 제거 및 실시간 스케줄링(RR/Nice -20) 적용
   - optimize_boot.sh : 전체 : 네트워크 온라인 대기 비활성화, 펌웨어 딜레이 제거, 불필요 서비스 비활성화, 파이썬 바이트코드 사전 컴파일 스크립트 작성
   - revert_rpi.sh : [1/4] : 복구 시 unmask network-wait-online 로직 추가
2. 검증:
   - `bash -n optimize_boot.sh` 구문 검증 완료
   - Git 커밋 `9bdb5bd` 원격 저장소 푸시 완료 (`https://github.com/jaesang-jeong/tuning_sound.git`)
3. 미해결 / 제안:
   - 라즈베리파이에서 `bash optimize_boot.sh` 실행 후 `sudo reboot` 및 `systemd-analyze` 측정 권장


## 2026-11-07 21:20 — 라즈베리파이(192.168.45.158) 원격 tuning_sound 배포 및 서비스 실행 완료

[DONE]
1. 수정 파일:
   - 원격 라즈베리파이(`/home/jsjeong/active_sound` 및 심볼릭 링크 `~/jsjeong/active_sound`)에 tuning_sound 배포
   - 계정 암호 `170213` 동기화 완료
   - 시스템 의존성(PortAudio, can-utils, bluez, sounddevice, python-can) 설치 및 SocketCAN(500k Listen-Only) 설정 완료
   - `tuning_sound.service` 등록 및 활성화(부팅 속도 최적화 제외)
2. 검증:
   - `ssh jsjeong@192.168.45.158` (암호 170213) 정상 인증 확인
   - `systemctl status tuning_sound.service` → Active: active (running) 정상 구동 확인
3. 미해결 / 제안:
   - 차량 CAN 포트 또는 PCAN-USB Pro를 라즈베리파이에 연결하여 실차 10ms 배기음 동기화 테스트 권장
