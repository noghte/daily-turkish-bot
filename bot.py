"""Daily Turkish verb lesson -> Telegram.

Picks one verb per day (sequential, most common first, cycles after the
last one), builds a lesson with conjugation tables and example sentences,
and sends it via the Telegram Bot API. Stdlib only — no dependencies.

Scheduling model
----------------
GitHub's scheduled runs are queued on shared infrastructure and often start
late — sometimes by well over an hour. So the workflow fires several times
each night and this script decides whether to actually send, using two rules:

  1. it must be at or after SEND_HOUR in the local timezone, and
  2. no lesson may already have been sent for today's local date.

Rule 2 is enforced with state.json, which the workflow commits back to the
repo. Together they give exactly one lesson per day even if some runs are
delayed or dropped entirely.

Env vars:
    TELEGRAM_BOT_TOKEN  bot token from @BotFather
    TELEGRAM_CHAT_ID    your chat id
    FORCE_SEND          "1" to bypass both rules (used by manual runs)

Usage:
    python bot.py              # send if due
    python bot.py --check      # explain today's decision, send nothing
    python bot.py --dry-run    # print the lesson instead of sending
    python bot.py --day 5      # preview a specific day
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from conjugator import conjugate

TIMEZONE = ZoneInfo("America/New_York")
SEND_HOUR = 21                   # 9 PM local
LATEST_HOUR = 23                 # don't send after 11:59 PM local
START_DATE = date(2026, 8, 3)    # day 1 of the cycle

HERE = Path(__file__).parent
VERBS_FILE = HERE / "verbs.json"
STATE_FILE = HERE / "state.json"


def load_verbs():
    return json.loads(VERBS_FILE.read_text(encoding="utf-8"))


def last_sent_date():
    """The local date of the most recent successful send, or None."""
    if not STATE_FILE.exists():
        return None
    try:
        raw = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return date.fromisoformat(raw["last_sent_date"])
    except (ValueError, KeyError, TypeError):
        return None


def record_sent(local_date, day_number):
    STATE_FILE.write_text(
        json.dumps({
            "last_sent_date": local_date.isoformat(),
            "last_day_number": day_number,
        }, indent=2) + "\n",
        encoding="utf-8",
    )


def should_send(now):
    """Return (send?, reason). `now` must be timezone-aware in TIMEZONE."""
    today = now.date()
    already = last_sent_date()
    if already == today:
        return False, f"already sent today ({today})"
    if now.hour < SEND_HOUR:
        return False, f"too early — {now:%H:%M} local, waiting for {SEND_HOUR}:00"
    if now.hour > LATEST_HOUR:
        return False, f"too late — {now:%H:%M} local, past the send window"
    return True, f"due — {now:%H:%M} local, nothing sent yet for {today}"


def build_lesson(day_number, verbs):
    """day_number is 1-based; cycles through the verb list."""
    entry = verbs[(day_number - 1) % len(verbs)]
    tables = conjugate(entry["verb"])

    lines = [
        f"🇹🇷 <b>Turkish Verb of the Day</b> — Day {day_number}",
        "",
        f"<b>{entry['verb']}</b> — {entry['en']}",
    ]
    for (tr_name, en_name), forms in tables.items():
        lines.append("")
        lines.append(f"<b>{tr_name}</b> ({en_name})")
        lines.append(f"ben {forms[0]} · sen {forms[1]} · o {forms[2]}")
        lines.append(f"biz {forms[3]} · siz {forms[4]} · onlar {forms[5]}")
    lines.append("")
    lines.append("<b>Örnekler</b> (examples)")
    for ex in entry["examples"]:
        lines.append(f"• {ex['tr']}")
        lines.append(f"   <i>{ex['en']}</i>")
    return "\n".join(lines)


def send(text, token, chat_id):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }).encode()
    with urllib.request.urlopen(url, data=data, timeout=30) as resp:
        body = json.loads(resp.read())
    if not body.get("ok"):
        raise RuntimeError(f"Telegram API error: {body}")


def day_number_for(local_date):
    return (local_date - START_DATE).days + 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="print the lesson instead of sending it")
    parser.add_argument("--check", action="store_true",
                        help="explain today's send decision and exit")
    parser.add_argument("--day", type=int, default=None,
                        help="preview a specific day number")
    args = parser.parse_args()

    now = datetime.now(TIMEZONE)
    forced = os.environ.get("FORCE_SEND") == "1"

    if args.check:
        send_now, reason = should_send(now)
        print(f"local time    : {now:%Y-%m-%d %H:%M %Z}")
        print(f"last sent     : {last_sent_date() or 'never'}")
        print(f"today is day  : {day_number_for(now.date())}")
        print(f"decision      : {'SEND' if send_now else 'skip'} — {reason}")
        return

    if args.day or args.dry_run:
        day_number = args.day or day_number_for(now.date())
        print(build_lesson(day_number, load_verbs()))
        return

    if not forced:
        send_now, reason = should_send(now)
        print(f"[{now:%Y-%m-%d %H:%M %Z}] {reason}")
        if not send_now:
            return
    else:
        print(f"[{now:%Y-%m-%d %H:%M %Z}] FORCE_SEND set — sending regardless.")

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        sys.exit("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars.")

    day_number = day_number_for(now.date())
    send(build_lesson(day_number, load_verbs()), token, chat_id)
    if forced:
        # A manual test run must not consume today's slot, or it would
        # suppress the real delivery later this evening.
        print(f"Sent day {day_number} lesson (manual run; state untouched).")
    else:
        record_sent(now.date(), day_number)
        print(f"Sent day {day_number} lesson.")


if __name__ == "__main__":
    main()
