"""
Quick Auto-Demo Script for PC Listening
Automatically plays 5 supercar/muscle car engines, exterior vs cabin views,
acceleration revs, and decel overrun backfires through PC speakers in 20 seconds!
"""

import time
import sys
from sound_engine import ExhaustSoundSynthesizer

def run_demo():
    print("=" * 70)
    print("  🚗 PC 즉시 청음 데모 (Quick Sound Demo for PC Speakers)")
    print("=" * 70)
    print("스피커 또는 이어폰 볼륨을 적당히 맞춰주세요.\n")

    synth = ExhaustSoundSynthesizer(sample_rate=44100, buffer_size=1024)
    synth.master_volume = 0.90
    synth.start()

    demos = [
        ("muscle_v8", "아메리칸 머슬카 V8 (6.2L)", "exterior", 780, 0.0, 2.5, "1. 머슬카 V8 아이들 캠 롭 (Cam Lope 쿵쾅거림)"),
        ("muscle_v8", "아메리칸 머슬카 V8 (6.2L)", "exterior", 4200, 0.9, 2.5, "2. 머슬카 V8 풀악셀 가속 & 슈퍼차저 휘슬"),
        ("muscle_v8", "아메리칸 머슬카 V8 (6.2L)", "exterior", 1000, 0.0, 2.0, "3. 엑셀 오프! 디셀러레이션 팝앤뱅/백파이어 폭발"),
        ("muscle_v8", "아메리칸 머슬카 V8 (6.2L)", "cabin", 4500, 0.95, 2.5, "4. 💺 [운전석 실내 콕핏] 전방 흡기 인덕션 로어 & 섀시 진동 붐"),
        ("porsche_gt3", "포르쉐 911 GT3 (Flat-6)", "exterior", 8200, 1.0, 2.5, "5. 포르쉐 911 GT3 9,000 RPM 초고회전 박서 비명"),
        ("ferrari_f8", "페라리 F8 (Flat-plane V8)", "exterior", 8500, 1.0, 2.5, "6. 페라리 F8 180도 플랫 크랭크 날카로운 F1 스크리머"),
        ("lamborghini_v10", "람보르기니 우라칸 (V10)", "cabin", 7800, 0.95, 2.5, "7. 람보르기니 V10 실내 콕핏 맹수 포효 & 백파이어"),
    ]

    for model, name, persp, rpm, throttle, dur, desc in demos:
        print(f"▶ {desc}")
        synth.set_model(model)
        synth.set_perspective(persp)
        synth.set_rpm(rpm)
        synth.set_throttle(throttle)
        time.sleep(dur)

    print("\n데모 완료! 사운드 엔진을 종료합니다.")
    synth.stop()
    print("=" * 70)

if __name__ == "__main__":
    run_demo()
