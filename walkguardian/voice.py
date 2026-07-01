"""
voice.py — 짧은 음성 출력 (오프라인 우선)

- 오프라인: pyttsx3 (Windows SAPI, 인터넷 불필요) → 기획서 '인터넷 미연결 대응' 충족
- 미설치 시: 콘솔 출력으로 폴백 (로직/데모는 그대로 동작)
- 방향(LEFT/RIGHT)은 현재 '단어'로 전달. 스테레오 좌/우 패닝은 향후 과제(비동기 wav 믹싱).

L1 은 진동 신호(vibrate 콜백)를 함께 트리거하도록 훅 제공.
"""
from __future__ import annotations
import sys


class Voice:
    def __init__(self, use_tts: bool = True, rate: int = 190, vibrate=None, echo: bool = True):
        self.vibrate = vibrate            # L1 시 호출할 콜백(진동). None 이면 무시.
        self.echo = echo                  # 콘솔에 발화 로그 출력 여부
        self.engine = None
        if use_tts:
            try:
                import pyttsx3
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", rate)
                # 한국어 보이스가 있으면 선택
                for v in self.engine.getProperty("voices"):
                    name = (getattr(v, "name", "") or "").lower()
                    langs = str(getattr(v, "languages", "")).lower()
                    if "korean" in name or "ko" in langs or "heami" in name:
                        self.engine.setProperty("voice", v.id)
                        break
            except Exception as e:
                print(f"[voice] pyttsx3 미사용({e}) → 콘솔 폴백", file=sys.stderr)
                self.engine = None

    def announce(self, alert):
        """alert: scheduler.Alert"""
        if self.echo:
            tag = {1: "🔴L1", 2: "🟠L2", 3: "🟡L3", 4: "⚪L4"}.get(alert.level, "")
            print(f"  {tag} 🔊 {alert.text}")
        if alert.level == 1 and self.vibrate:
            try:
                self.vibrate()
            except Exception:
                pass
        if self.engine is not None:
            self.engine.say(alert.text)
            self.engine.runAndWait()   # MVP: 블로킹. 실기기는 별도 스레드/큐 권장.

    def close(self):
        if self.engine is not None:
            try:
                self.engine.stop()
            except Exception:
                pass
