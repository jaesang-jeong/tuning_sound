# 🚗 가상 슈퍼카 & 머슬카 배기 사운드 시뮬레이터 & 튜닝 콕핏 (1단계 PC 완성본)

가상으로 슈퍼카 및 머슬카 엔진 배기음을 실시간 물리 음향(Hyper-Realistic Acoustic DSP)으로 합성하고, **실외 배기구 및 운전석 실내(Cockpit Cabin) 관점 청음**, GTA 5 / Forza 스타일 **3D 스테레오 입체 음장**, 세부 튜닝 및 차량 CAN Bus 연동을 지원하는 시스템입니다.

---

## 🌟 주요 특징

### 1. 💺 운전석 실내 (Cockpit Cabin) vs 🏎️ 실외 배기구 (Exterior) 관점 선택
버튼 클릭 한 번으로 차량 외부와 운전석 실내 사운드를 실시간으로 즉시 전환하여 청음할 수 있습니다:
- **🏎️ 실외 배기구 관점 (Exterior Tailpipe)**:
  - 배기관 테일파이프 끝단에서 뿜어져 나오는 날카로운 가스 파열음, 금속 링잉, 직관 밸브의 찢어지는 고음(Raspiness) 및 선명한 백파이어 폭발음.
- **💺 운전석 실내 관점 (Cockpit Cabin Interior)**:
  - **차체 방음재 음향 감쇠 (Firewall / Glass Low-Pass Filter)**: 고주파가 차체에 흡수되어 부드럽고 묵직한 톤으로 변환.
  - **흡기 매니폴드 인덕션 로어 (Intake Induction Roar)**: 운전자 정면 엔진룸에서 스로틀을 밟았을 때 차체를 가득 채우는 "우와아앙!" 강력한 공기 흡입음.
  - **차체 섀시 구조 전달 진동 (Chassis Structure-borne Boom)**: 45~90Hz 서브우퍼급 차체 바닥 진동 쿵쾅거림.
  - **밀폐된 실내 공간 초기 반사음 (Cabin Acoustic Early Reflections)**: 좁은 실내 콕핏 특유의 두터운 공간감.

### 2. 🎮 GTA 5 / 실사 레이싱 게임 스타일 3D 입체 음장 & 펀치
- **3D 스테레오 입체 음장 (Stereo Spatializer)**: 단순 모노 사운드가 아닌, 좌우 듀얼 배기관 분리 및 양이 시간차(ITD), 실내 초기 반사음을 모델링하여 헤드폰/스피커에서 공간을 가득 채우는 입체 음장감 구현.
- **아날로그 웜스 & 라우드니스 맥시마이저 (Loudness Maximizer)**: 소리가 빈약하지 않고 꽉 찬 펀치력으로 스피커를 울려주는 다이내믹스 프로세싱.

### 3. 5대 전설적 엔진 음향 모델 탑재
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

### 4. 🎛️ 튜닝 모드 (Tuning Mode)
- **실시간 RPM 슬라이더**: 500 RPM (아이들) ~ 9,500 RPM (레드라인) 실시간 제어
- **가상 가속 페달 (Dynamic Pedal)**: 페달을 누르면 풀악셀로 RPM이 급상승하고, 떼면 엑셀 오프(Decel) 감속과 함께 **팝앤뱅(Pop & Bang / 백파이어) 폭발음** 연발!
- **음향 DSP 세부 튜닝**:
  - 저음 서브 럼블 (Bass Rumble)
  - 중음 배기 맥동 (Mid Body)
  - 고음 비명 / 밸브 (High Screamer)
  - 흡기 인덕션 로어 (Intake Roar)
  - GTA 3D 스테레오 입체폭 (Stereo Width)
  - 실내 섀시 진동 붐 (Chassis Boom)
  - 배기관 거친 질감 (Raspy Saturation)
  - 가변 배기 밸브 (Valve Open / Close 스포트 모드)
  - 슈퍼차저 휘슬 (Whine) On/Off
  - 팝앤뱅(백파이어) 활성화 및 폭발 강도 조절
- **프리셋 관리**: 커스텀 설정 저장 및 즉각 불러오기 지원 (`supercar_sound_presets.json`)

### 5. 🏎️ 드라이브 모드 (Drive Mode)
- **디지털 클러스터 계기판**: 대형 RPM 게이지, 속도계(km/h), 기어 단수(DCT 1~7단 & N단), 스로틀 부하(Load %), 현재 청음 관점(실외/실내) 시각화
- **실시간 오디오 오실로스코프 파형**: 스피커로 출력되는 배기 펄스 실시간 모니터링
- **두 가지 입력 소스**:
  1. **가상 주행 시뮬레이터 (Virtual Vehicle Simulator)**: 가속 페달, 브레이크, 자동 7단 변속기 및 N단 정차 후까시(Free Revving) 모사
  2. **실제 차량 CAN Bus 연동**: 차량 CAN 버스 신호를 받아 실제 차량 RPM/스로틀에 실시간 연동 재생

### 6. 📡 CAN 통신 연동 (CAN Settings)
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
