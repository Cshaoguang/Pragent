import random
import time


def new_long_id() -> int:
    millis = int(time.time() * 1000)
    suffix = random.randint(1000, 9999)
    return millis * 10000 + suffix
