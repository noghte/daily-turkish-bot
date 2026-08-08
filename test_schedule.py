"""Simulate a year of GitHub Actions runs against the send logic.

Replays every cron firing for 365 days — through both DST transitions —
under various lateness and drop patterns, and asserts that each local day
gets exactly one lesson.

The important scenario is `systematic` lateness: GitHub frequently runs
*every* scheduled job late by a similar amount for hours at a time. That
is what silently broke the original exact-hour version of this bot.

Run: python test_schedule.py
"""
import random
from collections import Counter
from datetime import datetime, timedelta, timezone

import bot

CRON_HOURS_UTC = [23, 0, 1, 2, 3, 4]
DAYS = 365
START_UTC = datetime(2026, 8, 8, tzinfo=timezone.utc)


class FakeState:
    """Stands in for state.json so the real file is never touched."""

    def __init__(self):
        self.last = None

    def install(self):
        bot.last_sent_date = lambda: self.last
        bot.record_sent = lambda d, n: setattr(self, "last", d)


def firings(delay_fn, drop_probability, rng):
    """Every scheduled run over the window, as absolute UTC datetimes."""
    out = []
    for day in range(DAYS + 1):
        base = START_UTC + timedelta(days=day)
        for hour in CRON_HOURS_UTC:
            if rng.random() < drop_probability:
                continue
            fired = base.replace(hour=hour) + timedelta(minutes=delay_fn(rng))
            out.append(fired)
    return sorted(out)


def simulate(delay_fn, drop_probability, seed):
    rng = random.Random(seed)
    state = FakeState()
    state.install()
    sends = Counter()

    for fired in firings(delay_fn, drop_probability, rng):
        now = fired.astimezone(bot.TIMEZONE)
        send_now, _ = bot.should_send(now)
        if send_now:
            sends[now.date()] += 1
            bot.record_sent(now.date(), bot.day_number_for(now.date()))
    return sends


def report(label, sends, min_rate=1.0):
    """A duplicate is always a failure. Delivery must meet min_rate."""
    dupes = {str(d): c for d, c in sends.items() if c > 1}
    span = {(START_UTC + timedelta(days=i)).astimezone(bot.TIMEZONE).date()
            for i in range(1, DAYS)}
    missed = sorted(d for d in span if d not in sends)
    rate = (len(span) - len(missed)) / len(span)

    ok = not dupes and rate >= min_rate
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    print(f"        delivered  : {len(span) - len(missed)}/{len(span)} days "
          f"({rate:.1%}, need {min_rate:.0%})")
    print(f"        duplicates : {dupes or 'none'}")
    if missed:
        print(f"        missed     : {len(missed)}"
              f"  e.g. {[str(d) for d in missed[:3]]}")
    return ok


def main():
    all_ok = True

    # No drops: delivery must be perfect at every level of lateness.
    scenarios = [
        ("punctual, nothing dropped", lambda r: 0, 0.0, 1, 1.0),
        ("random lateness 0-90 min", lambda r: r.randint(0, 90), 0.0, 2, 1.0),
        ("systematic 60 min late", lambda r: 60, 0.0, 3, 1.0),
        ("systematic 90 min late", lambda r: 90, 0.0, 4, 1.0),
        ("systematic 2h late", lambda r: 120, 0.0, 5, 1.0),
        ("systematic 3h late", lambda r: 180, 0.0, 6, 1.0),
        # With runs also being dropped outright, occasional misses are
        # unavoidable — but duplicates never are.
        ("random 0-3h late + 5% dropped",
         lambda r: r.randint(0, 180), 0.05, 7, 0.99),
        ("random 0-3h late + 30% dropped",
         lambda r: r.randint(0, 180), 0.30, 8, 0.92),
        ("random 0-3h late + 50% dropped",
         lambda r: r.randint(0, 180), 0.50, 9, 0.80),
    ]
    for label, delay_fn, drop, seed, min_rate in scenarios:
        all_ok &= report(label, simulate(delay_fn, drop, seed), min_rate)

    # The old exact-hour gate, under the same systematic lateness.
    print("\n  previous exact-hour logic, under systematic lateness:")
    for delay in (0, 30, 45, 60, 90, 120, 180):
        delivered = set()
        for day in range(DAYS + 1):
            base = START_UTC + timedelta(days=day)
            for hour in (1, 2):
                local = (base.replace(hour=hour)
                         + timedelta(minutes=delay)).astimezone(bot.TIMEZONE)
                if local.hour == bot.SEND_HOUR:
                    delivered.add(local.date())
        pct = 100 * len(delivered) // (DAYS + 1)
        print(f"      {delay:>3} min late : {len(delivered):>3} days ({pct}%)"
              + ("   <-- silent failure" if pct == 0 else ""))

    raise SystemExit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
