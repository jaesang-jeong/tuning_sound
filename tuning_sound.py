import json
import os
import streamlit as st

# 저장 파일 경로
PRESET_FILE = "engine_presets.json"


def load_presets():
    if os.path.exists(PRESET_FILE):
        try:
            with open(PRESET_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_presets(presets):
    with open(PRESET_FILE, "w", encoding="utf-8") as f:
        json.dump(presets, f, ensure_ascii=False, indent=4)


st.set_page_config(
    page_title="가상 배기 & 엔진 튜닝 시뮬레이터",
    page_icon="🚗",
    layout="wide",
)

st.title("🚗 가상 배기 & 엔진 사운드 튜닝 시뮬레이터")
st.write(
    "엔진 스펙을 가상으로 튜닝하고, 배기 사운드 톤을 커스터마이징한 뒤 나만의 세팅으로 저장해 보세요!"
)

# 세션 상태 기본값 초기화
if "presets" not in st.session_state:
    st.session_state.presets = load_presets()

default_settings = {
    "engine_type": "V8 자연흡기 (머슬카)",
    "displacement": 3000,
    "cylinders": 6,
    "compression": 10.5,
    "idle_rpm": 800,
    "exhaust_pitch": 200,
    "resonance": 0.5,
    "pop_and_bang": True,
}

for key, val in default_settings.items():
    if key not in st.session_state:
        st.session_state[key] = val

# 사이드바: 가상 엔진 튜닝 및 사운드 커스터마이징 입력
st.sidebar.header("🎛️ 가상 엔진 & 배기 튜닝")

st.sidebar.subheader("1. 엔진 스펙 튜닝")
engine_options = ["V8 자연흡기 (머슬카)", "I4 터보 (스포츠카)", "V6 트윈터보", "전기차 가상 사운드"]
cylinder_options = [4, 6, 8, 12]

engine_type = st.sidebar.selectbox(
    "엔진 형식",
    engine_options,
    index=engine_options.index(st.session_state.engine_type)
    if st.session_state.engine_type in engine_options
    else 0,
    key="engine_type",
)

displacement = st.sidebar.slider(
    "배기량 (cc)", 1000, 6500, step=500, format="%d cc", key="displacement"
)

cylinders = st.sidebar.selectbox(
    "기통 수",
    cylinder_options,
    index=cylinder_options.index(st.session_state.cylinders)
    if st.session_state.cylinders in cylinder_options
    else 1,
    key="cylinders",
)

compression = st.sidebar.slider(
    "엔진 압축비", 8.5, 14.0, step=0.1, key="compression"
)

st.sidebar.subheader("2. 배기 사운드 커스터마이징")
idle_rpm = st.sidebar.slider(
    "아이들링 RPM", 600, 1200, step=50, key="idle_rpm"
)
exhaust_pitch = st.sidebar.slider(
    "배기음 톤 (Pitch / Hz)", 50, 500, step=10, key="exhaust_pitch"
)
resonance = st.sidebar.slider(
    "머플러 저음 공명 (Resonance)", 0.0, 1.0, step=0.1, key="resonance"
)
pop_and_bang = st.sidebar.checkbox(
    "팝앤뱅 (백파이어 사운드) 활성화", key="pop_and_bang"
)

# 메인 화면 구성
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 현재 튜닝 상태 요약")
    st.markdown(f"""
    - **엔진 타입:** `{engine_type}`
    - **배기량 / 기통:** `{displacement}cc / {cylinders}기통`
    - **압축비:** `{compression}`
    - **아이들 RPM:** `{idle_rpm} RPM`
    - **배기 주파수 톤:** `{exhaust_pitch} Hz`
    - **공명음 강도:** `{resonance}`
    - **팝앤뱅 효과:** `{'활성화 🔥' if pop_and_bang else '비활성화'}`
    """)

with col2:
    st.subheader("💾 튜닝 프리셋 저장 & 불러오기")
    preset_name = st.text_input("프리셋 이름 입력", "나만의 드림카 세팅")

    if st.button("현재 세팅 저장하기"):
        st.session_state.presets[preset_name] = {
            "engine_type": engine_type,
            "displacement": displacement,
            "cylinders": cylinders,
            "compression": compression,
            "idle_rpm": idle_rpm,
            "exhaust_pitch": exhaust_pitch,
            "resonance": resonance,
            "pop_and_bang": pop_and_bang,
        }
        save_presets(st.session_state.presets)
        st.success(f"'{preset_name}' 세팅이 안전하게 저장되었습니다!")

    # 저장된 프리셋 목록 불러오기
    if st.session_state.presets:
        st.markdown("---")
        selected_preset = st.selectbox(
            "저장된 프리셋 목록", list(st.session_state.presets.keys())
        )
        if st.button("선택한 프리셋 불러오기"):
            p = st.session_state.presets[selected_preset]
            # 세션 상태 갱신 후 화면 리로드
            for k, v in p.items():
                st.session_state[k] = v
            st.rerun()