import math

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_angle(a, b, t):
    diff = (b - a) % (2 * math.pi)
    if diff > math.pi:
        diff -= 2 * math.pi
    return a + diff * t

def smoothstep(edge0, edge1, x):
    if edge0 == edge1:
        return 0.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)

def small_hash_to_phase_amp(s):
    h = 0
    for ch in s:
        h = (h * 31 + ord(ch)) & 0xffffffff
    phase = float((h % 1000)) / 1000.0 * math.pi * 2.0
    amp = 0.7 + ((h >> 10) % 50) / 100.0
    return phase, amp
