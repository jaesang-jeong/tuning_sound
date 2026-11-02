# 🚗 가상 슈퍼카 & 머슬카 배기 사운드 시뮬레이터 & 튜닝 콕핏 (1단계 PC 완성본)

가상으로 슈퍼카 및 머슬카 엔진 배기음을 실시간 물리 음향(Hyper-Realistic Acoustic DSP)으로 합성하고 세부 튜닝 및 차량 CAN Bus 연동을 지원하는 시스템입니다.

---

## 🌟 주요 특징

### 1. 현실감 극대화 물리 음향 합성 아키텍처 (DSP Sound Engine)
기존의 단순 신디사이저(정현파 합성) 톤을 탈피하고, 실제 차량 음향학(Automotive Acoustics) 메커니즘을 적용하여 현실적인 사운드를 구현했습니다:
- **실린더별 비대칭 압력 충격파 (Blowdown Shockwave)**: 크랭크 720도 사이클 내에서 각 실린더 배기 밸브 개방(EVO) 시 분출되는 고압 가스 충격파 모델링
- **연소 미세 변동성 (Cycle-to-Cycle Jitter)**: 신디사이저 2D 게임 톤을 없애기 위해 매 사이클마다 점화 압력에 자연스러운 기계적 흔들림(Jitter) 적용
- **음향 관 공명 콤 필터 (Acoustic Waveguide Comb Filter)**: 속이 빈 금속 배기관 내부를 가스가 통과하며 끝단에서 반사되는 음향 에코를 모사하여 실제 금속 파이프 특유의 울림 재현
- **헬름홀츠 공명기 (Helmholtz Resonator)**: 머플러 챔버의 40~120Hz 서브우퍼급 저주파 펀치
- **배기 난류 가스 분출음 (Exhaust Gas Jet Turbulence)**: 스로틀 부하에 따른 고속 배기가스 와류 노이즈

### 2. 5대 전설적 엔진 음향 모델 탑재
- **아메리칸 머슬카 V8 (6.2L Supercharged Big-Block)**:
  - 거친 밸브 오버랩의 아이들 캠 롭(Cam Lope Chop, 5.8Hz 쿵쾅거림)
  - 40~70Hz 대역의 심장을 때리는 서브우퍼급 극저음 럼블
  - 기계식 슈퍼차저 휘슬(Roots Blower Whine) 사운드 토글 지원
- **포르쉐 911 GT3 (Boxer Flat-6)**:
  - 4.0L 수평대향 6기통 9,000 RPM.
  - 앙칼지고 거친 금속성 고회전 비명과 독특한 박서 비트(Boxer Beat)
- **페라리 F8 / 458 Italia (Flat-plane V8)**:
  - 180도 플랫 크랭크의 균일한 90도 점화 펄스열
  - F1 레이싱 머신처럼 날카롭게 찢어지는 초고주파 스크리머 톤
- **마세라티 그란투리스모 (Cross-plane V8)**:
  - 4.7L 크로스플레인 V8 특유의 깊고 웅장한 이탈리안 바리톤 저음 및 묵직한 디셀 버블
- **람보르기니 우라칸 (Naturally Aspirated V10)**:
  - 5.2L 자연흡기 V10의 맹렬하고 공격적인 맹수 울음소리와 매서운 백파이어

### 3. 🎛️ 튜닝 모드 (Tuning Mode)
- **실시간 RPM 슬라이더**: 500 RPM (아이들) ~ 9,500 RPM (레드라인) 실시간 제어
- **가상 가속 페달 (Dynamic Pedal)**: 페달을 누르면 풀악셀로 RPM이 급상승하고, 떼면 엑셀 오프(Decel) 감속과 함께 **팝앤뱅(Pop & Bang / 백파이어) 폭발음** 연발!
- **음향 DSP 세부 튜닝**:
  - 저음 서브 럼블 (Bass Rumble)
  - 중음 배기 맥동 (Mid Body)
  - 고음 비명 / 밸브 (High Screamer)
  - 배기관 거친 질감 (Raspy Saturation)
  - 가변 배기 밸브 (Valve Open / Close 스포트 모드)
  - 슈퍼차저 휘슬 (Whine) On/Off
  - 팝앤뱅(백파이어) 활성화 및 폭발 강도 조절
- **프리셋 관리**: 커스텀 설정 저장 및 즉각 불러오기 지원 (`supercar_sound_presets.json`)

### 4. 🏎️ 드라이브 모드 (Drive Mode)
- **디지털 클러스터 계기판**: 대형 RPM 게이지, 속도계(km/h), 기어 단수(DCT 1~7단 & N단), 스로틀 부하(Load %) 시각화
- **실시간 오디오 오실로스코프 파형**: 스피커로 출력되는 배기 펄스 실시간 모니터링
- **두 가지 입력 소스**:
  1. **가상 주행 시뮬레이터 (Virtual Vehicle Simulator)**: 가속 페달, 브레이크, 자동 7단 변속기 및 N단 정차 후까시(Free Revving) 모사
  2. **실제 차량 CAN Bus 연동**: 차량 CAN 버스 신호를 받아 실제 차량 RPM/스로틀에 실시간 연동 재생

### 5. 📡 CAN 통신 연동 (CAN Settings)
- **다양한 CAN 하드웨어 지원**:
  - `virtual`: PC 내부 가상 CAN 채널 (내장 가상 OBD-II 송신기로 PC에서 즉시 테스트 가능)
  - `slcan`: CANable, USB-to-CAN 직렬 어댑터, STM32 기반 브릿지
  - `pcan`: PEAK-System PCAN-USB
  - `socketcan`: 리눅스 / 라즈베리파이 (2단계 이식 시 호환)
  - `serial`: 아두이노/시리얼 기반 CAN 모듈
- **프로토콜 모드**:
  - **표준 OBD-II 모드**: PID 0x0C (RPM) 및 PID 0x11 (스로틀) 디코딩
  - **커스텀 CAN 모드**: 차종별 고유 CAN ID (예: 0x316), 시작 바이트, 길이, 스케일 팩터 직접 설정 가능

---

## 🚀 실행 방법

### 방법 1. 배치 파일 더블 클릭
`start_simulator.bat` 파일을 더블 클릭하여 실행합니다.

### 방법 2. 명령 프롬프트 / 파워셸
```powershell
$env:PYTHONPATH=""
& "C:\Program Files\Python313\python.exe" app_gui.py
```
