# Daily Turkish Verb Bot

Sends one Turkish verb lesson per day to your Telegram (@dailyturkishverbsBot) at 9:00 PM Eastern, via GitHub Actions. No server, no hosting.

Each lesson: the verb with its English meaning, full conjugation tables for four tenses (present continuous, simple past, future, aorist), and two example sentences with translations. 153 verbs, ordered by frequency, cycling back to day 1 after the last one.

## One-time setup (about 5 minutes)

**1. Get your chat ID.** Open [t.me/dailyturkishverbsBot](https://t.me/dailyturkishverbsBot), press **Start**, and send it any message. Then open this URL in your browser (token already filled in):

```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```

Look for `"chat":{"id":123456789,...}` — that number is your chat ID.

**2. Create the GitHub repo and push this folder:**

```bash
cd daily-turkish-bot
git init && git add -A && git commit -m "Daily Turkish verb bot"
# create a repo named daily-turkish-bot on github.com, then:
git remote add origin https://github.com/<your-username>/daily-turkish-bot.git
git push -u origin main
```

(Or with GitHub CLI: `gh repo create daily-turkish-bot --private --source=. --push`)

**3. Add the two secrets.** In the repo: **Settings → Secrets and variables → Actions → New repository secret**:

- `TELEGRAM_BOT_TOKEN` — your bot token from @BotFather
- `TELEGRAM_CHAT_ID` — the number from step 1

**4. Test it.** Repo → **Actions** tab → *Daily Turkish Lesson* → **Run workflow**. You should get the day's lesson on Telegram within a minute. (Manual runs skip the time-of-day check.)

That's it. From now on it sends automatically every evening.

## How the scheduling works

GitHub cron only speaks UTC, and 9 PM Eastern is 01:00 UTC in summer but 02:00 UTC in winter. GitHub also starts scheduled runs late fairly often, and occasionally drops them entirely.

So the workflow fires **four times a night** (01:00–04:00 UTC) and `bot.py` decides whether to actually send, using two rules:

1. it must be at or after 21:00 local time, and
2. no lesson may already have been sent for today's local date.

Rule 2 is tracked in `state.json`, which the workflow commits back to the repo after each send. Any one of the four runs can deliver the lesson, and the rest exit quietly — so a late or dropped run costs nothing.

`python test_schedule.py` replays a full year of runs (through both DST switches, with random delays and dropped runs) and asserts exactly one lesson per day.

## Local preview

```bash
python bot.py --check              # explain tonight's send decision
python bot.py --day 12 --dry-run   # print day 12's lesson
python test_conjugator.py          # verify the conjugation engine
python test_schedule.py            # verify the delivery schedule
```

## If lessons stop arriving

Check the repo's **Actions** tab first — every nightly run logs its decision via `bot.py --check`, so you can see whether it fired and what it decided.

- **No scheduled runs listed at all** — the schedule isn't registered. Confirm the workflow file is on your **default branch**, and that Actions is enabled under Settings → Actions → General.
- **Runs listed, but each says "already sent today"** — `state.json` is ahead of the real date; delete it and it will resend tonight.
- **Nothing for 60+ days** — GitHub auto-disables schedules on repos with no activity. The daily `state.json` commit normally prevents this; re-enable it from the Actions tab.

## Customizing

- **Time**: change `SEND_HOUR` in `bot.py` and the two `cron` lines in `.github/workflows/daily-lesson.yml` (local hour + 4 and + 5, mod 24).
- **Verbs**: edit `verbs.json` — add entries anywhere; conjugations are generated automatically, including two-word compounds like *yardım etmek*.
- **Start date**: `START_DATE` in `bot.py` controls which day of the cycle today is.

## Security note

The bot token was pasted in a chat once — if you ever want a fresh one, send `/revoke` to @BotFather and update the `TELEGRAM_BOT_TOKEN` secret. Never commit the token to the repo itself.
