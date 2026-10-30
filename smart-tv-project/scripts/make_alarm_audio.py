"""Generates app/audio/alarm.wav, a soft looping chime, with the standard library only."""
import math
import os
import struct
import wave

RATE = 16000
SECONDS = 4
NOTES = [(0.0, 523.25), (0.5, 659.25), (1.0, 783.99), (1.5, 1046.5)]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app", "audio", "alarm.wav")

samples = [0.0] * (RATE * SECONDS)
for start, freq in NOTES:
    begin = int(start * RATE)
    for i in range(int(1.4 * RATE)):
        t = i / RATE
        envelope = min(t / 0.01, 1) * math.exp(-t * 3)
        samples[begin + i] += 0.28 * envelope * math.sin(2 * math.pi * freq * t)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with wave.open(OUT, "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(RATE)
    w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, s)) * 32767)) for s in samples))
