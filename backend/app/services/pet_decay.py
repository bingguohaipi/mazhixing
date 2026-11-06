"""Satiety / mood decay rules (testable pure functions)."""

from datetime import datetime, timedelta, timezone

SATIETY_DECAY_INTERVAL_MINUTES = 30
SATIETY_DECAY_AMOUNT = 5
MOOD_DECAY_NORMAL = 1
MOOD_DECAY_WHEN_STARVING = 3
MAX_DECAY_INTERVALS_PER_SYNC = 48


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def compute_decay(
    satiety: int,
    mood: int,
    last_decay_at: datetime,
    now: datetime,
) -> tuple[int, int, datetime]:
    """Return new satiety, mood, and updated last_decay_at after time-based decay."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    last = last_decay_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    elapsed = now - last
    intervals = int(elapsed.total_seconds() // (SATIETY_DECAY_INTERVAL_MINUTES * 60))
    if intervals <= 0:
        return satiety, mood, last_decay_at
    intervals = min(intervals, MAX_DECAY_INTERVALS_PER_SYNC)
    new_satiety = _clamp(satiety - SATIETY_DECAY_AMOUNT * intervals, 0, 100)
    mood_loss = MOOD_DECAY_NORMAL * intervals
    if new_satiety <= 0:
        mood_loss += MOOD_DECAY_WHEN_STARVING * intervals
    new_mood = _clamp(mood - mood_loss, 0, 100)
    new_last = last + timedelta(minutes=SATIETY_DECAY_INTERVAL_MINUTES * intervals)
    return new_satiety, new_mood, new_last
