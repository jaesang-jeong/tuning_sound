# 🚗 가상 슈퍼카 & 머슬카 배기 사운드 시뮬레이터 & 튜닝 콕핏

노트북에서 **PEAK PCAN-USB Pro**를 통해 실제 차량 CAN 데이터를 수신하고, **차량 블루투스(A2DP) 무선 오디오**로 슈퍼카 & 머슬카 배기음을 출력할 수 있는 고성능 가상 사운드 시스템입니다.

---

## 🌟 최신 핵심 기능

### 1. 🔌 PEAK PCAN-USB Pro 인터페이스 완벽 지원
- **듀얼 채널(Dual-Channel) 지원**: `PCAN_USBBUS1 (채널 1)`, `PCAN_USBBUS2 (채널 2)`, `PCAN_USBBUS3`, `PCAN_USBBUS4`
- **하드웨어 자동 감지 & 진단**: `PCANBasic.dll` 기반으로 연결된 PCAN 어댑터를 자동 스캔
- **표준 차량 OBD-II 자동 쿼리**:
  - PID `0x0C` (엔진 RPM)를 33Hz 고속 주기로 자동 요청
  - PID `0x11` (스로틀 포지션) 및 PID `0x0D` (차량 속도) 동시 수신
- **커스텀 CAN 브로드캐스트 스니핑**: 현대/기아, BMW, 폭스바겐, GM 등 차종별 고유 CAN ID (예: `0x316`) 직접 디코딩
- **실시간 CAN 패킷 모니터 (Raw Frame Sniffer)**: 차량에서 들어오는 CAN ID, DLC, Data 바이트를 GUI 화면에서 실시간 육안 확인 가능

### 2. 📡 차량 블루투스(Bluetooth A2DP) 무선 오디오 라우팅
- **다이렉트 디바이스 라우팅**: 노트북을 차량 블루투스에 페어링하면, GUI 상단에서 **`🚗 [블루투스 차량] ...`** 장치를 직접 선택하여 배기 사운드를 차량 스피커로 출력
- **블루투스 지연 & 지터 끊김 방지 버퍼 조절**:
  - `512 샘플`: 초저지연 (유선 스피커 / AUX)
  - `1024 샘플`: 표준 밸런스
  - `2048 / 4096 샘플`: 블루투스 무선 패킷 손실 및 끊김 방지 최적화

### 3. ⚙️ 하이브리드 오디오 엔진 지원 (FMOD / Pure Data / Native DSP)
사용 목적에 따라 3가지 오디오 엔진을 선택할 수 있습니다:
1. **⚡ High-End Native DSP (기본 권장)**:
   - GTA 5 / Forza 스타일 3D 스테레오 입체 음장
   - **운전석 실내(Cockpit Cabin)** vs **실외 배기구(Exterior Tailpipe)** 청음 관점 실시간 전환
   - 흡기 인덕션 로어 (Intake Roar), 섀시 진동 붐 (Chassis Boom), 배기관 콤 필터
2. **🎮 FMOD Core API (`fmod_engine.py`)**:
   - 상용 레이싱 게임 표준 오디오 엔진 (fmod.dll 로드 시 활성화)
   - FMOD 전용 DSP 이펙트 체인 (Pitch, Lowpass, Distortion, Reverb)
3. **🎛️ Pure Data (Pd-vanilla, `exhaust_synth.pd`)**:
   - 오픈소스 모듈러 신시사이저 패치 연동
   - Python $\to$ TCP 포트 3000 FUDI 소켓으로 RPM/스로틀 실시간 전송

### 4. 🏎️ 5대 전설적 엔진 음향 라인업
- **아메리칸 머슬카 V8 (6.2L Supercharged)**: 묵직한 아이들 캠 롭(Cam Lope Chop), 서브우퍼급 저음 럼블, 슈퍼차저 휘슬
- **포르쉐 911 GT3 (Boxer Flat-6)**: 4.0L 수평대향 박서 9,000 RPM 앙칼진 금속성 고회전 비명
- **페라리 F8 / 458 (Flat-plane V8)**: 180도 플랫 크랭크 8기통, 찢어지는 F1 레이싱 머신 초고주파 스크리머
- **마세라티 그란투리스모 (Cross-plane V8)**: 4.7L 크로스플레인 V8 웅장한 바리톤 저음 & 디셀 팝콘
- **람보르기니 우라칸 (Naturally Aspirated V10)**: 5.2L 자연흡기 V10 맹수 포효 & 날카로운 백파이어

---

## 📁 주요 파일 구성

```
C:\agy\tuning_sound\
├── app_gui.py                    # PySide6 기반 디지털 콕핏 GUI 메인 애플리케이션
├── pcan_manager.py               # PEAK PCAN-USB Pro 전용 드라이버 및 OBD-II/CAN 매니저
├── sound_engine.py               # 3D 음향 물리 DSP 엔진 (블루투스 오디오 디바이스 라우팅 지원)
├── fmod_engine.py                # FMOD Core API C-API 연동 모듈
├── pd_bridge.py                  # Pure Data (Pd-vanilla) FUDI 소켓 통신 브릿지
├── exhaust_synth.pd              # Pure Data 배기 사운드 신시사이저 패치 파일
├── test_pcan_usb.py              # PCAN-USB Pro 하드웨어 상태 1초 진단 스크립트
├── presets_manager.py            # 슈퍼카 & 머슬카 사운드 프리셋 관리자
├── supercar_sound_presets.json   # 5대 엔진 기본 프리셋 데이터
├── start_simulator.bat           # 1클릭 실행 배치 파일
└── README.md                     # 본 설명서
```

---

## 🚀 빠른 시작 가이드 (노트북 + PCAN-USB Pro + 차량 블루투스)

### 1단계: 차량 블루투스 연결
1. 노트북의 Windows 블루투스 설정에서 차량 오디오를 페어링합니다.
2. 차량 인포테인먼트 화면에서 오디오 소스를 **Bluetooth Audio**로 선택합니다.

### 2단계: PCAN-USB Pro 하드웨어 연결 및 진단
1. 노트북 USB 포트에 **PCAN-USB Pro**를 꽂고, 차량 OBD-II 포트(또는 CAN High/Low 배선)에 연결합니다.
2. 콘솔에서 아래 명령으로 하드웨어 상태를 확인합니다:
   ```powershell
   $env:PYTHONPATH=""
   & "C:\Program Files\Python313\python.exe" test_pcan_usb.py
   ```

### 3단계: 애플리케이션 실행
`start_simulator.bat` 파일을 더블 클릭하거나 명령어를 실행합니다:
```powershell
$env:PYTHONPATH=""
& "C:\Program Files\Python313\python.exe" app_gui.py
```

### 4단계: GUI 조작법
1. **출력 장치 선택**: 상단 헤더의 `출력 장치` 드롭다운에서 **`🚗 [블루투스 차량] ...`** 을 선택합니다.
2. **PCAN 연결**: `🔌 PCAN-USB Pro 연동` 탭으로 이동하여 채널(`PCAN_USBBUS1`)을 고르고 **`🔌 PCAN-USB Pro 연결`** 버튼을 누릅니다.
3. 차량 시동을 걸고 가속 페달을 밟으면, 실제 RPM에 맞추어 차량 스피커에서 리얼한 배기음이 터져 나옵니다!
4. 상단의 **`🏎️ 실외`** / **`💺 운전석 실내`** 버튼으로 실내 콕핏 음향과 실외 직관 배기음을 자유롭게 전환할 수 있습니다.
