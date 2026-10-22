"""A tiny cache with TTL (time to live) and LRU (least recently used) eviction."""
import time
from collections import OrderedDict


class TTLCache:
    def __init__(self, max_size=3, ttl_seconds=5):
        self.max_size = max_size          # how many items fit on the "desk"
        self.ttl = ttl_seconds            # how long an item stays trusted
        self.data = OrderedDict()         # key -> (value, expires_at); keeps order
        self.hits = 0
        self.misses = 0

    def get(self, key):
        if key not in self.data:
            self.misses += 1
            return None
        value, expires_at = self.data[key]
        if time.time() > expires_at:      # too old: throw it away
            del self.data[key]
            self.misses += 1
            return None
        self.data.move_to_end(key)        # mark as "recently used"
        self.hits += 1
        return value

    def set(self, key, value):
        self.data[key] = (value, time.time() + self.ttl)
        self.data.move_to_end(key)
        if len(self.data) > self.max_size:
            evicted, _ = self.data.popitem(last=False)   # oldest-used goes out
            print(f"  [evict] {evicted}")

    def hit_rate(self):
        total = self.hits + self.misses
        return 0 if total == 0 else self.hits / total


cache = TTLCache(max_size=3, ttl_seconds=5)


def slow_lookup(permit_id):
    """Pretend this is a slow database or API call."""
    time.sleep(1)
    return f"Permit {permit_id}: APPROVED"


def get_permit(permit_id):
    result = cache.get(permit_id)
    if result is not None:
        print(f"HIT   {permit_id}")
        return result
    print(f"MISS  {permit_id} (slow lookup...)")
    result = slow_lookup(permit_id)
    cache.set(permit_id, result)
    return result


if __name__ == "__main__":
    start = time.time()
    requests = ["P1", "P2", "P1", "P1", "P3", "P2", "P4", "P1", "P2", "P2"]
    for r in requests:
        get_permit(r)

    print("\nWaiting 6 seconds so everything expires...")
    time.sleep(6)
    get_permit("P2")

    print(f"\nHits: {cache.hits}  Misses: {cache.misses}  "
          f"Hit rate: {cache.hit_rate():.0%}")
    print(f"Total time: {time.time() - start:.1f}s "
          f"(without a cache: about {len(requests) + 1 + 6}s)")