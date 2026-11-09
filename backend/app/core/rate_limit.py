import math
import time

from fastapi import HTTPException, status
from limits import parse
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter

# render runs a single process, so counters in memory are enough. they reset when the
# instance restarts or sleeps; more than one instance would need a shared store (redis)
storage = MemoryStorage()
_limiter = MovingWindowRateLimiter(storage)


def enforce(limit: str, *key: str) -> None:
    rule = parse(limit)
    if _limiter.hit(rule, *key):
        return

    reset_at = _limiter.get_window_stats(rule, *key).reset_time
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="too many requests, please try again later",
        headers={"Retry-After": str(max(1, math.ceil(reset_at - time.time())))},
    )
