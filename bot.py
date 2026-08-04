"""Daily Turkish verb lesson -> Telegram.

Picks one verb per day (sequential, most common first, cycles after the
last one), builds a lesson with conjugation tables and example sentences,
and sends it via the Telegram Bot API. Stdlib only — no dependencies.

Env vars:
    TELEGRAM_BOT_TOKEN  bot token from @BotFather
    TELEGRAM_CHAT_ID    your chat id
    FORCE_SEND          set to "1" to skip the 21:00 local-time gate

Usage:
    python bot.py             # send today's lesson (only at 21:00 local)
    python bot.py --dry-run   # print instead of sending
    python bot.py --day 5     # preview a specific day (implies no gate)
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
SEND_HOUR = 21          # 9 PM local
START_DATE = date(2026, 8, 3)   # day 1 of the cycle
VERBS_FILE = Path(__file__).parent / "verbs.json"


def load_verbs():
    return json.loads(VERBS_FILE.read_text(encoding="utf-8"))


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="print the lesson instead of sending it")
    parser.add_argument("--day", type=int, default=None,
                        help="preview a specific day number")
    args = parser.parse_args()

    now = datetime.now(TIMEZONE)
    force = os.environ.get("FORCE_SEND") == "1" or args.dry_run or args.day

    # The workflow fires at both 01:00 and 02:00 UTC so that one of them
    # is always 21:00 in New York regardless of DST; skip the other run.
    if not force and now.hour != SEND_HOUR:
        print(f"Local time is {now:%H:%M} (not {SEND_HOUR}:00), skipping.")
        return

    day_number = args.day or (now.date() - START_DATE).days + 1
    lesson = build_lesson(day_number, load_verbs())

    if args.dry_run or (args.day and not os.environ.get("TELEGRAM_BOT_TOKEN")):
        print(lesson)
        return

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        sys.exit("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars.")
    send(lesson, token, chat_id)
    print(f"Sent day {day_number} lesson.")


if __name__ == "__main__":
    main()
