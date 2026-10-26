"""
KALLO NEXUS — Render-ready Telegram bot
VIP boxed UI · looping single-mode · cloudscraper engine.
"""
import asyncio
import html
import json
import logging
import os
import random
import re
import secrets
import string
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import cloudscraper
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest, NetworkError, RetryAfter, TimedOut
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, ContextTypes,
    MessageHandler, filters,
)
from telegram.request import HTTPXRequest

# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "8404717126:AAF6untl8TV-DyEM-2FgnjLfeaYUAliiZX0").strip()

OWNER_USER_ID = int(os.getenv("OWNER_USER_ID", "8635902333"))
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "mva_kallo").lstrip("@")
SUPPORT_CHAT = os.getenv("SUPPORT_CHAT", "mva_kallo").lstrip("@")
CHANNEL = os.getenv("CHANNEL", "kallo404").lstrip("@")
BOT_NAME = "KALLO"

NEW_USER_CREDITS = 20
SINGLE_CHECK_COST = 1
BULK_CHECK_COST = 1
REFERRER_BONUS = 10
REFERRED_BONUS = 5
DB_FILE = Path(os.getenv("DB_FILE", "data/kallo_db.json"))

HISTORY_CAP = 800
LOG_CAP = 400
LIST_PAGE = 25

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("kallo")

# ── BRAND (VIP BOXED EDITION) ────────────────────────────────
BRAND      = "ᴋᴀʟʟᴏ ɴᴇxᴜꜱ"
SIGN       = "ᴀꜱɪᴀᴛɪᴄ · ꜱᴄᴀɴ ᴄᴏʀᴇ"
TAGLINE    = "ᴘʀᴇᴄɪꜱɪᴏɴ · ꜱᴘᴇᴇᴅ · ᴘᴏᴡᴇʀ"
MARK_STAMP = f"❖ {BRAND} ❖"

TL, TR, BL, BR = "╭", "╮", "╰", "╯"
H, V = "─", "│"
DIV = "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈"
DIV_HEAVY = "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰"

BADGE_FREE    = "○ ꜰʀᴇᴇ"
BADGE_TAKEN   = "◉ ᴛᴀᴋᴇɴ"
BADGE_UNKNOWN = "◎ ᴜɴᴋɴᴏᴡɴ"
BADGE_PREMIUM = "♛ ᴘʀᴇᴍɪᴜᴍ"
BADGE_ADMIN   = "♦ ᴀᴅᴍɪɴ"
BADGE_OWNER   = "♛ ᴏᴡɴᴇʀ"

CROWN   = "♛"
DIAMOND = "◈"
SPARK   = "✦"
ARROW   = "▸"
BOX_W   = 23


def box_title(title, width=BOX_W):
    inner = f" {title} "
    pad = max(0, width - len(inner))
    left = pad // 2
    right = pad - left
    return f"<b>{TL}{H * (left + 2)} {title} {H * (right + 2)}{TR}</b>"


def box_close(width=BOX_W):
    return f"<b>{BL}{H * width}{BR}</b>"


def box_line(content):
    return f"<b>{V}</b> {content}"


def box_full(title, body_lines, width=BOX_W):
    out = [box_title(title, width)]
    for line in body_lines:
        out.append(box_line(line))
    out.append(box_close(width))
    return "\n".join(out)


# ──────────────────────────────────────────────────────────────
# CHECK ENGINE
# ──────────────────────────────────────────────────────────────
SUPPORTED_DOMAINS = ["hi2.in", "telegmail.com"]
RECAPTCHA_SITEKEY = "6LfEUPkgAAAAAKTgbMoewQkWBEQhO2VPL4QviKct"
RECAPTCHA_CO = "aHR0cHM6Ly9oaTIuaW46NDQz"
RECAPTCHA_V = "XrIDux0s7SoNe6_IHkjGC92W"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",
]

DEFAULT_COOKIES = {
    "__eoi": "ID=84791c9b377760ae:T=1785815548:RT=1792303549:S=AA-AfjbAwxHu8AEDm58GilHT3t8P",
    "__gads": "ID=d35d042016429679:T=1785815548:RT=1792303548:S=ALNI_MZSbvQNM9tUxE_CmZnXbUQWGG3kdQ",
    "__gpi": "UID=0000145fbef21f84:T=1785815548:RT=1792303549:S=ALNI_MY_LJgZNcPDvOPq2U5kNuOWvCQotQ",
    "_ga": "GA1.1.1815008449.1785815546",
    "_ga_02VF9D5F26": "GS2.1.s1792303540$o18$g0$t1792303540$j60$l0$h0",
}

SPINNER = ["◜", "◠", "◝", "◞", "◡", "◟"]
GLITCH = ["◈", "◇", "◆", "◇"]
SCAN_PHASES = [
    "ʙᴏᴏᴛɪɴɢ ᴄᴏʀᴇ",
    "ʀᴇꜱᴏʟᴠɪɴɢ ᴛᴀʀɢᴇᴛ",
    "ꜱᴏʟᴠɪɴɢ ʜᴀɴᴅꜱʜᴀᴋᴇ",
    "Qᴜᴇʀʏɪɴɢ ʀᴇɢɪꜱᴛʀʏ",
    "ᴄʀᴏꜱꜱ-ᴄʜᴇᴄᴋɪɴɢ",
    "ꜰɪɴᴀʟɪꜱɪɴɢ ᴠᴇʀᴅɪᴄᴛ",
]
VERDICT = {
    "taken":     ("◉", "ᴛᴀᴋᴇɴ",    "ʀᴇɢɪꜱᴛᴇʀᴇᴅ · ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ"),
    "not_taken": ("○", "ꜰʀᴇᴇ",     "ᴜɴʀᴇɢɪꜱᴛᴇʀᴇᴅ · ᴀᴠᴀɪʟᴀʙʟᴇ"),
    "unknown":   ("◎", "ᴜɴᴋɴᴏᴡɴ", "ꜱɪʟᴇɴᴛ · ʀᴇᴛʀʏ ᴀᴅᴠɪꜱᴇᴅ"),
}
MARK = {"taken": "◉", "not_taken": "○", "unknown": "◎"}


def _marquee(i, width=11):
    span = 2 * (width - 1)
    pos = i % span
    if pos >= width:
        pos = span - pos
    return "·" * pos + "◉" + "·" * (width - pos - 1)


def _bar(done, total, width=14):
    filled = int(width * done / total) if total else 0
    filled = max(0, min(width, filled))
    return "▰" * filled + "▱" * (width - filled)


def scan_id():
    return secrets.token_hex(3).upper()


def stamp():
    return datetime.now(timezone.utc).strftime("%d.%m · %H:%M UTC")


def short_ts():
    return datetime.now(timezone.utc).strftime("%d.%m %H:%M")


def build_session(seed_cookies=True):
    s = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
    )
    s.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    })
    if seed_cookies:
        for k, v in DEFAULT_COOKIES.items():
            s.cookies.set(k, v, domain="hi2.in")
    return s


def solve_recaptcha_hi2(session):
    try:
        anchor = (
            "https://www.google.com/recaptcha/api2/anchor?ar=1"
            f"&k={RECAPTCHA_SITEKEY}&co={RECAPTCHA_CO}&hl=en"
            f"&v={RECAPTCHA_V}&size=invisible"
        )
        r = session.get(
            anchor, timeout=12,
            headers={"User-Agent": random.choice(USER_AGENTS), "Referer": "https://hi2.in/"},
        )
        if 'recaptcha-token" value="' not in r.text:
            return None
        token = r.text.split('recaptcha-token" value="')[1].split('"')[0]

        payload = (
            f"v={RECAPTCHA_V}&reason=q&c={token}&k={RECAPTCHA_SITEKEY}"
            f"&co={RECAPTCHA_CO}&hl=en&size=invisible"
        )
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Referer": anchor,
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.google.com",
        }
        d = session.post(
            "https://www.google.com/recaptcha/enterprise/reload",
            data=payload, headers=headers, timeout=12,
        )
        if 'resp","' not in d.text:
            return None
        return d.text.split('resp","')[1].split('"')[0]
    except Exception as e:
        log.debug("recaptcha solve failed: %s", e)
        return None


def check_hi2_email(email):
    if "@" not in email:
        return "unknown"
    prefix, domain = email.split("@", 1)
    domain = domain.lower()

    session = build_session()
    recaptcha = solve_recaptcha_hi2(session)
    if not recaptcha:
        return "unknown"

    headers = {
        "User-Agent": session.headers["User-Agent"],
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic bnVsbA==",
        "Origin": "https://hi2.in",
        "Referer": "https://hi2.in/",
    }
    data = {"domain": domain, "prefix": prefix, "recaptcha": recaptcha}

    try:
        r = session.post("https://hi2.in/api/custom", headers=headers, data=data, timeout=20)
        if r.status_code == 403 and "Just a moment" in r.text:
            log.warning("Cloudflare blocked the request.")
            return "unknown"
        body = r.text.lower()
        if "already taken" in body or "taken" in body:
            return "taken"
        if "available" in body or "success" in body:
            return "not_taken"
        return "unknown"
    except Exception as e:
        log.debug("hi2 check error: %s", e)
        return "unknown"


# ──────────────────────────────────────────────────────────────
# ANIMATED SCAN ROUTINES
# ──────────────────────────────────────────────────────────────
async def _tick(fut, seconds=1.05):
    try:
        await asyncio.wait_for(asyncio.shield(fut), timeout=seconds)
    except asyncio.TimeoutError:
        pass


async def scan_single_animated(msg, email):
    t0 = time.monotonic()
    fut = asyncio.ensure_future(asyncio.to_thread(check_hi2_email, email))
    target = None
    i = 0
    while not fut.done():
        phase = SCAN_PHASES[min(i // 2, len(SCAN_PHASES) - 1)]
        frame = SPINNER[i % len(SPINNER)]
        track = _marquee(i)
        dots = "." * (i % 4)
        elapsed = time.monotonic() - t0
        text = (
            f"{box_title('❖ ꜱᴄᴀɴ ᴄᴏʀᴇ ❖')}\n"
            f"{box_line(f'<i>ʟɪᴠᴇ ᴘʀᴏᴄᴇꜱꜱɪɴɢ</i>')}\n"
            f"{box_close()}\n"
            f"\n"
            f"<b>{TL}{H * BOX_W}{TR}</b>\n"
            f"<b>{V}</b>   {track}   <b>{V}</b>\n"
            f"<b>{BL}{H * BOX_W}{BR}</b>\n"
            f"\n"
            f"{box_full('◈ ᴛᴀʀɢᴇᴛ', [f'<code>{html.escape(email)}</code>'])}\n"
            f"\n"
            f"{box_full('✦ ꜱᴛᴀᴛᴜꜱ', [f'{frame} {phase}{dots}', f'ᴇʟᴀᴘꜱᴇᴅ ‣ {elapsed:.1f}s'])}\n"
            f"\n"
            f"{DIV}\n"
            f"  <i>ᴀᴡᴀɪᴛɪɴɢ ᴠᴇʀᴅɪᴄᴛ …</i>"
        )
        try:
            if target is None:
                target = await msg.reply_text(text, parse_mode="HTML")
            else:
                await target.edit_text(text, parse_mode="HTML")
        except (BadRequest, NetworkError, TimedOut):
            pass
        i += 1
        await _tick(fut)
    return fut.result(), time.monotonic() - t0, target


async def scan_bulk_animated(msg, emails, status_msg):
    t0 = time.monotonic()
    total = len(emails)
    lines = []

    for idx, email in enumerate(emails, 1):
        fut = asyncio.ensure_future(asyncio.to_thread(check_hi2_email, email))
        i = 0
        while not fut.done():
            done = idx - 1
            body = [
                f"{box_title('❖ ʙᴜʟᴋ ᴄᴏʀᴇ ❖')}",
                box_line(f"⟦{_bar(done, total)}⟧  <b>{int(100 * done / total)}%</b>"),
                box_line(f"{SPINNER[i % len(SPINNER)]}  <code>{html.escape(email)}</code>"),
                box_close(),
                "",
            ]
            if lines:
                body += lines[-6:]
            try:
                await status_msg.edit_text("\n".join(body), parse_mode="HTML")
            except (BadRequest, NetworkError, TimedOut):
                pass
            i += 1
            await _tick(fut)

        result = fut.result()
        mark, label, _ = VERDICT.get(result, VERDICT["unknown"])
        lines.append(f"  {mark}  <code>{html.escape(email)}</code>  ‣  {label}")
        await asyncio.sleep(0.2)

    return lines, time.monotonic() - t0


def single_report(email, result, elapsed, uid, u):
    mark, label, note = VERDICT.get(result, VERDICT["unknown"])
    node = email.split("@", 1)[1] if "@" in email else "hi2.in"

    if result == "not_taken":
        verdict_lines = ["<b>○ ᴀᴠᴀɪʟᴀʙʟᴇ</b>", "ᴜɴʀᴇɢɪꜱᴛᴇʀᴇᴅ"]
    elif result == "taken":
        verdict_lines = ["<b>◉ ᴜɴᴀᴠᴀɪʟᴀʙʟᴇ</b>", "ʀᴇɢɪꜱᴛᴇʀᴇᴅ"]
    else:
        verdict_lines = ["<b>◎ ᴜɴᴋɴᴏᴡɴ</b>", "ꜱɪʟᴇɴᴛ"]

    telemetry_lines = [
        f"ɴᴏᴅᴇ    ‣ {html.escape(node)}",
        f"ʟᴀᴛᴇɴᴄʏ ‣ {elapsed:.2f}s",
        f"ꜱᴄᴀɴ ɪᴅ ‣ #{scan_id()}",
        f"ꜱᴛᴀᴍᴘ   ‣ {stamp()}",
    ]

    return (
        f"{box_title('❖ ᴠᴇʀᴅɪᴄᴛ ❖')}\n"
        f"{box_line(f'<i>{BRAND}</i>')}\n"
        f"{box_close()}\n"
        f"\n"
        f"{box_full('◈ ʀᴇꜱᴜʟᴛ', verdict_lines)}\n"
        f"\n"
        f"{box_full('✦ ᴛᴀʀɢᴇᴛ', [f'<code>{html.escape(email)}</code>'])}\n"
        f"\n"
        f"{box_full('◈ ᴛᴇʟᴇᴍᴇᴛʀʏ', telemetry_lines)}\n"
        f"\n"
        f"{box_full('♛ ᴡᴀʟʟᴇᴛ', [f'<b>{html.escape(credits_label(uid, u))}</b>'])}\n"
        f"\n"
        f"{DIV}\n"
        f"  <i>{SIGN}</i>"
    )


def bulk_report_chunks(lines, valid_count, elapsed):
    free = sum(1 for l in lines if "ꜰʀᴇᴇ" in l)
    taken = sum(1 for l in lines if "ᴛᴀᴋᴇɴ" in l)
    unknown = valid_count - free - taken

    header = (
        f"{box_title('❖ ʀᴇᴘᴏʀᴛ ❖')}\n"
        f"{box_line('<i>ʙᴜʟᴋ ꜱᴄᴀɴ ᴄᴏᴍᴘʟᴇᴛᴇ</i>')}\n"
        f"{box_close()}\n"
        f"\n"
        f"<b>{TL}{H * BOX_W}{TR}</b>\n"
        f"<b>{V}</b> {_bar(valid_count, valid_count)} <b>{V}</b>\n"
        f"<b>{V}</b>  <b>100%</b> · {valid_count} ᴛᴀʀɢᴇᴛꜱ    <b>{V}</b>\n"
        f"<b>{BL}{H * BOX_W}{BR}</b>\n"
        f"\n"
    )

    summary_lines = [
        f"○ ꜰʀᴇᴇ     ‣ <b>{free}</b>",
        f"◉ ᴛᴀᴋᴇɴ    ‣ <b>{taken}</b>",
        f"◎ ᴜɴᴋɴᴏᴡɴ  ‣ <b>{unknown}</b>",
        f"▪ ᴛᴏᴛᴀʟ    ‣ <b>{valid_count}</b>",
        f"⏱ ᴛɪᴍᴇ    ‣ <b>{elapsed:.2f}s</b>",
    ]
    footer = (
        f"\n{box_full('◈ ꜱᴜᴍᴍᴀʀʏ', summary_lines)}\n"
        f"\n"
        f"{box_title('❖ ᴇɴᴅ ❖')}\n"
        f"{box_line(f'<i>{stamp()}</i>')}\n"
        f"{box_close()}\n"
        f"\n"
        f"  <i>{SIGN}</i>"
    )

    chunks, size = [], 35
    for start in range(0, len(lines), size):
        part = lines[start:start + size]
        if start == 0:
            text = header + "\n".join(part)
        else:
            text = (
                f"{box_title(f'❖ ᴄᴏɴᴛɪɴᴜᴇᴅ {start + 1}–{start + len(part)} ❖')}\n"
                f"{box_close()}\n\n"
                + "\n".join(part)
            )
        chunks.append(text)

    if not chunks:
        return [header.rstrip() + footer]
    chunks[-1] += footer
    return chunks


def skipped_report(invalid):
    body = "\n".join(f"  ✕  <code>{html.escape(x)}</code>" for x in invalid)
    return (
        f"{box_title('⚠ ꜱᴋɪᴘᴘᴇᴅ ⚠')}\n"
        f"{box_line('<i>ᴜɴꜱᴜᴘᴘᴏʀᴛᴇᴅ ɴᴏᴅᴇ</i>')}\n"
        f"{box_close()}\n"
        f"\n{body}"
    )


# ──────────────────────────────────────────────────────────────
# DATABASE
# ──────────────────────────────────────────────────────────────
def utc_now():
    return datetime.now(timezone.utc).isoformat()


def default_db():
    return {
        "users": {},
        "admins": [OWNER_USER_ID],
        "redeem_codes": {},
        "settings": {"upi_id": "faridh@fam", "upi_name": "FARID", "price": 100, "qr_file_id": ""},
        "stats": {"total": 0, "single": 0, "bulk": 0, "taken": 0, "not_taken": 0, "unknown": 0},
        "checks": [],
        "redeem_log": [],
        "premium_log": [],
    }


def load_db():
    try:
        if DB_FILE.exists():
            with DB_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            base = default_db()
            for k, v in base.items():
                data.setdefault(k, v)
            for k, v in base["stats"].items():
                data["stats"].setdefault(k, 0)
            data["settings"] = {**base["settings"], **data.get("settings", {})}
            return data
    except (OSError, json.JSONDecodeError) as exc:
        log.exception("Database load failed: %s", exc)
    return default_db()


DB = load_db()


def save_db():
    try:
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=DB_FILE.parent, delete=False) as f:
            json.dump(DB, f, indent=2, ensure_ascii=False)
            tmp = Path(f.name)
        tmp.replace(DB_FILE)
    except OSError:
        log.exception("Database save failed")


def trim(lst, cap):
    if len(lst) > cap:
        del lst[:-cap]


def log_check(uid, u, email, result, mode, save=True):
    DB["stats"]["total"] = DB["stats"].get("total", 0) + 1
    DB["stats"][mode] = DB["stats"].get(mode, 0) + 1
    DB["stats"][result] = DB["stats"].get(result, 0) + 1
    DB["checks"].append({
        "uid": str(uid),
        "name": u.get("name") or "User",
        "username": u.get("username") or "",
        "email": email,
        "result": result,
        "mode": mode,
        "ts": short_ts(),
    })
    trim(DB["checks"], HISTORY_CAP)
    if save:
        save_db()


def user_for(uid, first_name="User", username=None):
    key = str(uid)
    if key not in DB["users"]:
        DB["users"][key] = {
            "credits": NEW_USER_CREDITS, "unlimited": False, "referred_by": None,
            "referred_users": [], "first_time": False, "username": username,
            "name": first_name, "joined": utc_now(),
        }
        save_db()
    u = DB["users"][key]
    u["name"] = first_name or u.get("name") or "User"
    u["username"] = username
    u.setdefault("credits", NEW_USER_CREDITS)
    u.setdefault("unlimited", False)
    u.setdefault("referred_users", [])
    u.setdefault("referred_by", None)
    return u


def is_owner(uid):
    return int(uid) == OWNER_USER_ID


def is_admin(uid):
    return int(uid) in [int(x) for x in DB.get("admins", [])]


def is_staff(uid):
    return is_owner(uid) or is_admin(uid)


def has_unlimited(uid, u=None):
    u = u or DB["users"].get(str(uid), {})
    return is_owner(uid) or bool(u.get("unlimited"))


def credits_label(uid, u):
    return "♾ ᴜɴʟɪᴍɪᴛᴇᴅ" if has_unlimited(uid, u) else f"⚡ {u.get('credits', 0)}"


def who(u, uid=None):
    name = html.escape((u.get("name") or "User")[:32])
    uname = f" @{html.escape(u['username'])}" if u.get("username") else ""
    idpart = f" · <code>{uid}</code>" if uid else ""
    return f"{name}{uname}{idpart}"


async def send_rich(bot, chat_id, text):
    try:
        await bot.send_message(int(chat_id), text, parse_mode="HTML")
        return True
    except BadRequest:
        try:
            await bot.send_message(int(chat_id), text)
            return True
        except Exception:
            return False
    except Exception:
        return False


# ──────────────────────────────────────────────────────────────
# KEYBOARDS
# ──────────────────────────────────────────────────────────────
def main_keyboard(uid):
    rows = [
        [
            InlineKeyboardButton("◈ ꜱɪɴɢʟᴇ ◈", callback_data="single"),
            InlineKeyboardButton("◈ ʙᴜʟᴋ ◈", callback_data="bulk"),
        ],
        [
            InlineKeyboardButton("✦ ᴘʀᴏꜰɪʟᴇ ✦", callback_data="status"),
            InlineKeyboardButton("✦ ʀᴇᴅᴇᴇᴍ ✦", callback_data="redeem"),
        ],
        [
            InlineKeyboardButton("◇ ʀᴇꜰᴇʀ ◇", callback_data="refer"),
            InlineKeyboardButton("♛ ᴘʀᴇᴍɪᴜᴍ ♛", callback_data="premium"),
        ],
        [
            InlineKeyboardButton("✆ ꜱᴜᴘᴘᴏʀᴛ", url=f"https://t.me/{SUPPORT_CHAT}"),
            InlineKeyboardButton("◈ ᴄʜᴀɴɴᴇʟ", url=f"https://t.me/{CHANNEL}"),
        ],
    ]
    if is_staff(uid):
        rows.append([
            InlineKeyboardButton("❖ ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ ❖", callback_data="panel"),
        ])
    return InlineKeyboardMarkup(rows)


def back_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("◂ ʀᴇᴛᴜʀɴ ᴛᴏ ᴍᴇɴᴜ", callback_data="home"),
    ]])


def panel_back():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◈ ᴘᴀɴᴇʟ", callback_data="panel"),
         InlineKeyboardButton("◂ ʜᴏᴍᴇ", callback_data="home")],
    ])


def panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◈ ꜱᴛᴀᴛꜱ", callback_data="p_stats"),
         InlineKeyboardButton("◈ ʟᴏɢ", callback_data="p_history")],
        [InlineKeyboardButton("✦ ᴜꜱᴇʀꜱ", callback_data="p_users"),
         InlineKeyboardButton("♛ ᴘʀᴇᴍɪᴜᴍ", callback_data="p_premium")],
        [InlineKeyboardButton("◇ ʀᴇꜰꜱ", callback_data="p_refs"),
         InlineKeyboardButton("✦ ᴄʟᴀɪᴍꜱ", callback_data="p_claims")],
        [InlineKeyboardButton("♦ ᴀᴅᴍɪɴꜱ", callback_data="p_admins"),
         InlineKeyboardButton("✉ ᴅᴍ", callback_data="dm_uid")],
        [InlineKeyboardButton("◈ ɢᴇɴ ᴄᴏᴅᴇ", callback_data="gen_code"),
         InlineKeyboardButton("◈ ᴄᴏᴅᴇꜱ", callback_data="list_codes")],
        [InlineKeyboardButton("⚡ ᴄʀᴇᴅɪᴛꜱ", callback_data="add_credits"),
         InlineKeyboardButton("♛ ɢʀᴀɴᴛ", callback_data="grant")],
        [InlineKeyboardButton("✕ ʀᴇᴠᴏᴋᴇ", callback_data="revoke"),
         InlineKeyboardButton("◈ ɪɴꜰᴏ", callback_data="userinfo")],
        [InlineKeyboardButton("✈ ʙʀᴏᴀᴅᴄᴀꜱᴛ", callback_data="broadcast")],
        [InlineKeyboardButton("◂ ʙᴀᴄᴋ", callback_data="home")],
    ])


def admins_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("＋ ᴀᴅᴅ", callback_data="add_admin"),
         InlineKeyboardButton("－ ʀᴇᴍᴏᴠᴇ", callback_data="remove_admin")],
        [InlineKeyboardButton("◈ ᴘᴀɴᴇʟ", callback_data="panel"),
         InlineKeyboardButton("◂ ʜᴏᴍᴇ", callback_data="home")],
    ])


def users_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◈ ʟᴏɢ", callback_data="p_history"),
         InlineKeyboardButton("✦ ᴄʟᴀɪᴍꜱ", callback_data="p_claims")],
        [InlineKeyboardButton("◈ ᴘᴀɴᴇʟ", callback_data="panel"),
         InlineKeyboardButton("◂ ʜᴏᴍᴇ", callback_data="home")],
    ])


# ──────────────────────────────────────────────────────────────
# TEXTS
# ──────────────────────────────────────────────────────────────
def menu_text(uid, u):
    role = (
        BADGE_OWNER if is_owner(uid)
        else BADGE_ADMIN if is_admin(uid)
        else BADGE_PREMIUM if u.get("unlimited")
        else BADGE_FREE
    )
    name = html.escape((u.get("name") or "User").strip()[:20])
    power = html.escape(credits_label(uid, u))
    refs = len(u.get("referred_users", []))
    total_checks = len([r for r in DB["checks"] if r["uid"] == str(uid)])

    profile_lines = [
        f"ɴᴀᴍᴇ    ‣  <b>{name}</b>",
        f"ᴘʟᴀɴ    ‣  {role}",
        f"ᴘᴏᴡᴇʀ   ‣  <b>{power}</b>",
        f"ʀᴇꜰꜱ    ‣  {refs}",
        f"ᴄʜᴇᴄᴋꜱ  ‣  {total_checks}",
    ]

    return (
        f"{box_title(f'❖ {BRAND} ❖')}\n"
        f"{box_line(f'<i>{TAGLINE}</i>')}\n"
        f"{box_close()}\n"
        f"\n"
        f"{box_full('♛ ᴡᴇʟᴄᴏᴍᴇ ᴀʙᴏᴀʀᴅ', profile_lines)}\n"
        f"\n"
        f"<b>{TL}{H * BOX_W}{TR}</b>\n"
        f"<b>{V}</b>  <i>ᴜɴʟᴏᴄᴋ ᴇxᴄʟᴜꜱɪᴠᴇ ᴘᴏᴡᴇʀ</i>  <b>{V}</b>\n"
        f"<b>{BL}{H * BOX_W}{BR}</b>\n"
        f"\n"
        f"  {ARROW} <b>ᴄʜᴏᴏꜱᴇ ʏᴏᴜʀ ᴘᴀᴛʜ ʙᴇʟᴏᴡ</b>"
    )


SINGLE_TEXT = (
    f"{box_title('❖ ꜱɪɴɢʟᴇ ꜱᴄᴀɴ ❖')}\n"
    f"{box_line('<i>ᴏɴᴇ ᴛᴀʀɢᴇᴛ ᴍᴏᴅᴇ</i>')}\n"
    f"{box_close()}\n"
    f"\n"
    f"{box_full('◈ ɪɴꜱᴛʀᴜᴄᴛɪᴏɴ', ['ꜱᴇɴᴅ ᴀ ꜱɪɴɢʟᴇ ᴇᴍᴀɪʟ'])}\n"
    f"\n"
    f"{box_full('✦ ᴇxᴀᴍᴘʟᴇ', ['<code>kallo@hi2.in</code>', '<code>uchiha@telegmail.com</code>'])}\n"
    f"\n"
    f"{DIV}\n"
    f"  <i>{SIGN}</i>"
)


def bulk_text():
    return (
        f"{box_title('❖ ʙᴜʟᴋ ꜱᴄᴀɴ ❖')}\n"
        f"{box_line('<i>ᴍᴀꜱꜱ ᴛᴀʀɢᴇᴛ ᴍᴏᴅᴇ</i>')}\n"
        f"{box_close()}\n"
        f"\n"
        f"{box_full('◈ ɪɴꜱᴛʀᴜᴄᴛɪᴏɴ', ['ꜱᴇɴᴅ ᴜɴʟɪᴍɪᴛᴇᴅ ᴇᴍᴀɪʟꜱ'])}\n"
        f"\n"
        f"{box_full('✦ ꜰᴏʀᴍᴀᴛ', ['ꜱᴘᴀᴄᴇ ꜱᴇᴘᴀʀᴀᴛᴇᴅ', 'ᴄᴏᴍᴍᴀ ꜱᴇᴘᴀʀᴀᴛᴇᴅ', 'ɴᴇᴡ-ʟɪɴᴇ ꜱᴇᴘᴀʀᴀᴛᴇᴅ'])}\n"
        f"\n"
        f"{box_full('◈ ᴇxᴀᴍᴘʟᴇ', ['<code>kallo@hi2.in</code>', '<code>uchiha@hi2.in</code>'])}\n"
        f"\n"
        f"{DIV}\n"
        f"  <i>{SIGN}</i>"
    )


async def status_text(uid, u):
    refs = len(u.get("referred_users", []))
    role = (
        BADGE_OWNER if is_owner(uid)
        else BADGE_ADMIN if is_admin(uid)
        else BADGE_PREMIUM if u.get("unlimited")
        else BADGE_FREE
    )
    mine = [r for r in DB["checks"] if r["uid"] == str(uid)]
    free_hits = sum(1 for r in mine if r["result"] == "not_taken")
    taken_hits = sum(1 for r in mine if r["result"] == "taken")

    account_lines = [
        f"ɴᴀᴍᴇ     ‣ {html.escape(u.get('name', 'User'))}",
        f"ɪᴅ       ‣ <code>{uid}</code>",
        f"ᴜꜱᴇʀɴᴀᴍᴇ ‣ @{html.escape(u.get('username') or 'not set')}",
        f"ᴊᴏɪɴᴇᴅ   ‣ {u.get('joined', '')[:10]}",
    ]
    status_lines = [
        f"ʀᴏʟᴇ    ‣ {role}",
        f"ᴘᴏᴡᴇʀ   ‣ <b>{credits_label(uid, u)}</b>",
        f"ʀᴇꜰꜱ    ‣ {refs}",
    ]
    activity_lines = [
        f"ᴛᴏᴛᴀʟ    ‣ {len(mine)}",
        f"ꜰʀᴇᴇ     ‣ {free_hits}",
        f"ᴛᴀᴋᴇɴ    ‣ {taken_hits}",
    ]

    return (
        f"{box_title('❖ ᴘʀᴏꜰɪʟᴇ ❖')}\n"
        f"{box_line('<i>ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ</i>')}\n"
        f"{box_close()}\n"
        f"\n"
        f"{box_full('◈ ᴀᴄᴄᴏᴜɴᴛ', account_lines)}\n"
        f"\n"
        f"{box_full('✦ ꜱᴛᴀᴛᴜꜱ', status_lines)}\n"
        f"\n"
        f"{box_full('◈ ᴀᴄᴛɪᴠɪᴛʏ', activity_lines)}\n"
        f"\n"
        f"{DIV}\n"
        f"  <i>{SIGN}</i>"
    )


def panel_text():
    s = DB["stats"]
    premium = sum(1 for x in DB["users"].values() if x.get("unlimited"))
    refs = sum(len(x.get("referred_users", [])) for x in DB["users"].values())

    user_lines = [
        f"ᴜꜱᴇʀꜱ    ‣ <b>{len(DB['users'])}</b>",
        f"ᴘʀᴇᴍɪᴜᴍ  ‣ <b>{premium}</b>",
        f"ᴀᴅᴍɪɴꜱ   ‣ <b>{len(DB['admins'])}</b>",
        f"ᴄᴏᴅᴇꜱ    ‣ <b>{len(DB['redeem_codes'])}</b>",
        f"ʀᴇꜰꜱ     ‣ <b>{refs}</b>",
    ]
    scan_lines = [
        f"ᴛᴏᴛᴀʟ    ‣ <b>{s.get('total', 0)}</b>",
        f"ꜱɪɴɢʟᴇ   ‣ {s.get('single', 0)}",
        f"ʙᴜʟᴋ     ‣ {s.get('bulk', 0)}",
        f"ꜰʀᴇᴇ     ‣ {s.get('not_taken', 0)}",
        f"ᴛᴀᴋᴇɴ    ‣ {s.get('taken', 0)}",
        f"ᴜɴᴋɴᴏᴡɴ  ‣ {s.get('unknown', 0)}",
    ]
    event_lines = [
        f"ᴄʟᴀɪᴍꜱ  ‣ {len(DB['redeem_log'])}",
        f"ɢʀᴀɴᴛꜱ  ‣ {len(DB['premium_log'])}",
    ]

    return (
        f"{box_title('❖ ᴀᴅᴍɪɴ ᴄᴏʀᴇ ❖')}\n"
        f"{box_line('<i>ᴄᴏɴᴛʀᴏʟ ᴄᴇɴᴛᴇʀ</i>')}\n"
        f"{box_close()}\n"
        f"\n"
        f"{box_full('◈ ᴜꜱᴇʀꜱ', user_lines)}\n"
        f"\n"
        f"{box_full('✦ ꜱᴄᴀɴꜱ', scan_lines)}\n"
        f"\n"
        f"{box_full('◈ ᴇᴠᴇɴᴛꜱ', event_lines)}\n"
        f"\n"
        f"  <i>{SIGN}</i>"
    )


def history_text():
    rows = DB["checks"][-LIST_PAGE:]
    if not rows:
        return f"{box_title('❖ ᴄʜᴇᴄᴋ ʟᴏɢ ❖')}\n{box_close()}\n\n  ɴᴏ ᴄʜᴇᴄᴋꜱ ʏᴇᴛ."
    out = [box_title("❖ ᴄʜᴇᴄᴋ ʟᴏɢ ❖"), box_close(), ""]
    for r in reversed(rows):
        out.append(
            f"{MARK.get(r['result'], '?')}  <code>{html.escape(r['email'])}</code>\n"
            f"   {who(r, r['uid'])}  ·  {r.get('ts', '')}"
        )
    return "\n".join(out)


def users_text():
    users = sorted(DB["users"].items(), key=lambda kv: kv[1].get("joined", ""), reverse=True)
    if not users:
        return f"{box_title('❖ ᴜꜱᴇʀꜱ ❖')}\n{box_close()}\n\n  ɴᴏ ᴜꜱᴇʀꜱ."
    out = [box_title("❖ ᴜꜱᴇʀꜱ ❖"), box_close(), ""]
    for uid, u in users[:LIST_PAGE]:
        tag = "♾" if u.get("unlimited") else f"⚡{u.get('credits', 0)}"
        out.append(f"{tag}  {who(u, uid)}")
    return "\n".join(out)


def premium_text():
    rows = [(uid, u) for uid, u in DB["users"].items() if u.get("unlimited")]
    out = [box_title("❖ ᴘʀᴇᴍɪᴜᴍ ❖"), box_close(), ""]
    if not rows:
        out.append("  ɴᴏ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ.")
    for uid, u in rows[-LIST_PAGE:]:
        out.append(f"♛  {who(u, uid)}")
    return "\n".join(out)


def refs_text():
    rows = [(uid, u) for uid, u in DB["users"].items() if u.get("referred_users")]
    total = sum(len(u.get("referred_users", [])) for _, u in rows)
    out = [box_title("❖ ʀᴇꜰᴇʀʀᴀʟꜱ ❖"), box_line(f"<i>{total} ᴛᴏᴛᴀʟ ɪɴᴠɪᴛᴇꜱ</i>"), box_close(), ""]
    if not rows:
        out.append("  ɴᴏ ʀᴇꜰꜱ ʏᴇᴛ.")
    for uid, u in sorted(rows, key=lambda kv: len(kv[1]["referred_users"]), reverse=True)[:LIST_PAGE]:
        out.append(f"◈  {who(u, uid)}  ‣  <b>{len(u['referred_users'])}</b>")
    return "\n".join(out)


def claims_text():
    out = [box_title("❖ ᴄʟᴀɪᴍꜱ ❖"), box_close(), ""]
    if not DB["redeem_log"]:
        out.append("  ɴᴏ ᴄʟᴀɪᴍꜱ.")
    for r in reversed(DB["redeem_log"][-LIST_PAGE:]):
        out.append(f"⚡ +{r['credits']}  ·  <code>{r['uid']}</code>  ·  {html.escape(r['code'])}")
    return "\n".join(out)


def admins_text():
    out = [box_title("❖ ᴀᴅᴍɪɴꜱ ❖"), box_close(), ""]
    for a in DB["admins"]:
        u = DB["users"].get(str(a), {})
        tag = "♛ ᴏᴡɴᴇʀ" if int(a) == OWNER_USER_ID else "♦ ᴀᴅᴍɪɴ"
        out.append(f"{tag}  {who(u, a)}")
    return "\n".join(out)


# ──────────────────────────────────────────────────────────────
# HANDLERS
# ──────────────────────────────────────────────────────────────
async def safe_edit(query, text, markup=None):
    try:
        await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")
    except BadRequest as exc:
        if "Message is not modified" not in str(exc):
            try:
                await query.message.reply_text(text, reply_markup=markup, parse_mode="HTML")
            except Exception:
                log.exception("Fallback message failed")
    except (NetworkError, TimedOut):
        log.warning("Network issue editing message")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = user_for(user.id, user.first_name, user.username)
    if u.pop("first_time", False):
        u["credits"] = NEW_USER_CREDITS
    payload = context.args[0] if context.args else ""
    if payload.startswith("ref_") and not u.get("referred_by"):
        ref_id = payload[4:]
        if ref_id.isdigit() and ref_id != str(user.id) and ref_id in DB["users"]:
            ref = DB["users"][ref_id]
            refs = ref.setdefault("referred_users", [])
            if str(user.id) not in refs:
                refs.append(str(user.id))
                ref["credits"] = ref.get("credits", 0) + REFERRER_BONUS
                u["credits"] = u.get("credits", NEW_USER_CREDITS) + REFERRED_BONUS
                u["referred_by"] = ref_id
    save_db()
    await update.effective_message.reply_text(
        menu_text(user.id, u),
        reply_markup=main_keyboard(user.id),
        parse_mode="HTML",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def single_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_for(user.id, user.first_name, user.username)
    context.user_data["action"] = "single"
    await update.effective_message.reply_text(
        SINGLE_TEXT, reply_markup=back_keyboard(), parse_mode="HTML"
    )


async def bulk_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_for(user.id, user.first_name, user.username)
    context.user_data["action"] = "bulk"
    await update.effective_message.reply_text(
        bulk_text(), reply_markup=back_keyboard(), parse_mode="HTML"
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    try:
        await q.answer()
    except (BadRequest, NetworkError, TimedOut):
        pass

    user = q.from_user
    uid = user.id
    u = user_for(uid, user.first_name, user.username)
    data = q.data or ""

    if data == "home":
        context.user_data.pop("action", None)
        await safe_edit(q, menu_text(uid, u), main_keyboard(uid))
    elif data == "single":
        context.user_data["action"] = "single"
        await safe_edit(q, SINGLE_TEXT, back_keyboard())
    elif data == "bulk":
        context.user_data["action"] = "bulk"
        await safe_edit(q, bulk_text(), back_keyboard())
    elif data == "status":
        await safe_edit(q, await status_text(uid, u), back_keyboard())
    elif data == "redeem":
        context.user_data["action"] = "redeem"
        await safe_edit(
            q,
            f"{box_title('❖ ʀᴇᴅᴇᴇᴍ ❖')}\n{box_close()}\n\n"
            f"  ꜱᴇɴᴅ ʏᴏᴜʀ ᴄᴏᴅᴇ\n  <code>KALLO-ABC123</code>\n\n{DIV}",
            back_keyboard(),
        )
    elif data == "refer":
        bot_username = context.bot_data.get("bot_username")
        if not bot_username:
            bot = await context.bot.get_me()
            bot_username = bot.username
            context.bot_data["bot_username"] = bot_username
        link = f"https://t.me/{bot_username}?start=ref_{uid}"
        body = [
            f"  <code>{link}</code>",
            "",
            f"  ʏᴏᴜ ᴇᴀʀɴ     ‣  +{REFERRER_BONUS}",
            f"  ꜰʀɪᴇɴᴅ ɢᴇᴛꜱ  ‣  +{REFERRED_BONUS}",
        ]
        await safe_edit(
            q,
            f"{box_title('❖ ʀᴇꜰᴇʀ & ᴇᴀʀɴ ❖')}\n{box_close()}\n\n"
            + "\n".join(body) + f"\n\n{DIV}\n  <i>{SIGN}</i>",
            back_keyboard(),
        )
    elif data == "premium":
        s = DB["settings"]
        plan_lines = [
            f"ᴘʀɪᴄᴇ  ‣ <b>₹{s.get('price', 100)}</b>",
            f"ᴜᴘɪ    ‣ <code>{html.escape(str(s.get('upi_id', 'faridh@fam')))}</code>",
            f"ɴᴀᴍᴇ   ‣ {html.escape(str(s.get('upi_name', 'FARID')))}",
        ]
        benefits_lines = [
            "♾ ᴜɴʟɪᴍɪᴛᴇᴅ ᴄʜᴇᴄᴋꜱ",
            "⚡ ᴘʀɪᴏʀɪᴛʏ ꜱᴄᴀɴ",
            "◈ ᴇxᴄʟᴜꜱɪᴠᴇ ᴀᴄᴄᴇꜱꜱ",
            "✦ ᴘʀᴇᴍɪᴜᴍ ꜱᴜᴘᴘᴏʀᴛ",
        ]
        steps_lines = [
            "① ꜱᴄᴀɴ ᴛʜᴇ ǫʀ",
            "② ᴍᴀᴋᴇ ᴘᴀʏᴍᴇɴᴛ",
            f"③ ᴅᴍ @{SUPPORT_CHAT}",
        ]
        await safe_edit(
            q,
            f"{box_title('♛ ᴘʀᴇᴍɪᴜᴍ ♛')}\n"
            f"{box_line('<i>ᴇxᴄʟᴜꜱɪᴠᴇ ᴀᴄᴄᴇꜱꜱ</i>')}\n"
            f"{box_close()}\n\n"
            f"{box_full('◈ ᴘʟᴀɴ', plan_lines)}\n\n"
            f"{box_full('✦ ʙᴇɴᴇꜰɪᴛꜱ', benefits_lines)}\n\n"
            f"{box_full('◈ ꜱᴛᴇᴘꜱ', steps_lines)}\n\n"
            f"{DIV}\n  <i>{SIGN}</i>",
            back_keyboard(),
        )
        qr_file_id = s.get("qr_file_id")
        if qr_file_id:
            try:
                # Ekane problem ta chilo, seta fix kora hoyeche
                upi_id_str = str(s.get("upi_id", "faridh@fam"))
                caption_text = (
                    f"{box_title('♛ ᴜᴘɪ ǫʀ ♛')}\n"
                    f"{box_line(f'<code>{html.escape(upi_id_str)}</code>')}\n"
                    f"{box_close()}"
                )
                await q.message.reply_photo(
                    photo=qr_file_id,
                    caption=caption_text,
                    parse_mode="HTML",
                )
            except (NetworkError, TimedOut, BadRequest) as exc:
                log.warning("QR send failed: %s", exc)

    # ── panel ────────────────────────────────────────────────
    elif data == "panel":
        if not is_staff(uid):
            await safe_edit(q, "⛔ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ.", back_keyboard())
            return
        await safe_edit(q, panel_text(), panel_keyboard())
    elif data in {"p_stats", "p_history", "p_users", "p_premium", "p_refs",
                  "p_claims", "p_admins"}:
        if not is_staff(uid):
            await safe_edit(q, "⛔ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ.", back_keyboard())
            return
        if data == "p_stats":
            await safe_edit(q, panel_text(), panel_keyboard())
        elif data == "p_history":
            await safe_edit(q, history_text(), users_keyboard())
        elif data == "p_users":
            await safe_edit(q, users_text(), users_keyboard())
        elif data == "p_premium":
            await safe_edit(q, premium_text(), panel_back())
        elif data == "p_refs":
            await safe_edit(q, refs_text(), panel_back())
        elif data == "p_claims":
            await safe_edit(q, claims_text(), panel_back())
        elif data == "p_admins":
            await safe_edit(q, admins_text(), admins_keyboard())
    elif data == "list_codes":
        if not is_staff(uid):
            await safe_edit(q, "⛔ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ.", back_keyboard())
            return
        if not DB["redeem_codes"]:
            text = f"{box_title('❖ ᴄᴏᴅᴇꜱ ❖')}\n{box_close()}\n\n  ɴᴏ ᴄᴏᴅᴇꜱ ʏᴇᴛ."
        else:
            body = "\n".join(
                f"<code>{html.escape(c)}</code>  ·  {d['credits']} ᴄʀ  ·  "
                f"{len(d.get('claimed_by', []))}/{d['max_claims']}"
                for c, d in list(DB["redeem_codes"].items())[-30:]
            )
            text = f"{box_title('❖ ᴄᴏᴅᴇꜱ ❖')}\n{box_close()}\n\n{body}"
        await safe_edit(q, text, panel_back())
    elif data in {"gen_code", "add_credits", "grant", "revoke", "userinfo",
                  "broadcast", "dm_uid", "add_admin", "remove_admin"}:
        if not is_staff(uid):
            await safe_edit(q, "⛔ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ.", back_keyboard())
            return
        if data in {"add_admin", "remove_admin"} and not is_owner(uid):
            await safe_edit(q, "⛔ ᴏᴡɴᴇʀ ᴏɴʟʏ.", panel_back())
            return
        context.user_data["action"] = data
        prompts = {
            "gen_code": "ꜱᴇɴᴅ: <code>CREDITS MAX_CLAIMS</code>",
            "add_credits": "ꜱᴇɴᴅ: <code>USER_ID AMOUNT</code>",
            "grant": "ꜱᴇɴᴅ ᴛʜᴇ ᴜꜱᴇʀ ɪᴅ.",
            "revoke": "ꜱᴇɴᴅ ᴛʜᴇ ᴜꜱᴇʀ ɪᴅ.",
            "userinfo": "ꜱᴇɴᴅ ᴀ ᴜꜱᴇʀ ɪᴅ.",
            "broadcast": "ꜱᴇɴᴅ ᴛʜᴇ ᴍᴇꜱꜱᴀɢᴇ.",
            "dm_uid": "ꜱᴇɴᴅ ᴛʜᴇ ᴛᴀʀɢᴇᴛ ᴜꜱᴇʀ ɪᴅ.",
            "add_admin": "ꜱᴇɴᴅ ᴛʜᴇ ᴜꜱᴇʀ ɪᴅ.",
            "remove_admin": "ꜱᴇɴᴅ ᴛʜᴇ ᴀᴅᴍɪɴ ɪᴅ.",
        }
        await safe_edit(
            q,
            f"{box_title('❖ ᴀᴅᴍɪɴ ᴀᴄᴛɪᴏɴ ❖')}\n{box_close()}\n\n  {prompts[data]}",
            panel_back(),
        )


# ── PARSE + TEXT FLOW ────────────────────────────────────────
def parse_entries(text, single_mode):
    if single_mode:
        lines = [l for l in text.splitlines() if l.strip()]
        parts = [lines[0]] if lines else []
    else:
        parts = [t for t in re.split(r"[\s,]+", text) if t]

    seen, items = set(), []
    for it in parts:
        it = it.strip().lower()
        if not it or it in seen:
            continue
        seen.add(it)
        items.append(it)

    valid, invalid = [], []
    for it in items:
        if "@" in it:
            prefix, dom = it.split("@", 1)
            if dom not in SUPPORTED_DOMAINS:
                invalid.append(it)
                continue
            valid.append(f"{prefix}@{dom}")
        else:
            valid.append(f"{it}@hi2.in")
    return valid, invalid


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    uid = user.id
    u = user_for(uid, user.first_name, user.username)
    text = (msg.text or "").strip()
    action = context.user_data.get("action")

    # ── redeem ───────────────────────────────────────────────
    if action == "redeem":
        code = text.upper()
        item = DB["redeem_codes"].get(code)
        if not item:
            await msg.reply_text("✕ ɪɴᴠᴀʟɪᴅ ᴄᴏᴅᴇ.")
        elif str(uid) in item.get("claimed_by", []):
            await msg.reply_text("· ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ᴄʟᴀɪᴍᴇᴅ.")
        elif len(item.get("claimed_by", [])) >= int(item.get("max_claims", 0)):
            await msg.reply_text("✕ ᴄᴏᴅᴇ ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ.")
        else:
            item.setdefault("claimed_by", []).append(str(uid))
            u["credits"] = u.get("credits", 0) + int(item["credits"])
            DB["redeem_log"].append({
                "uid": str(uid), "code": code, "credits": int(item["credits"]), "ts": short_ts(),
            })
            trim(DB["redeem_log"], LOG_CAP)
            save_db()
            await msg.reply_text(f"✓ ʀᴇᴅᴇᴇᴍᴇᴅ  ·  +{item['credits']} ᴄʀ  ·  ʙᴀʟᴀɴᴄᴇ: {u['credits']}")
        context.user_data.pop("action", None)
        return

    # ── personal DM ─────────────────────────────────────────
    if action == "dm_uid":
        target = text.strip()
        if not target.isdigit():
            await msg.reply_text("⚠ ꜱᴇɴᴅ ᴀ ɴᴜᴍᴇʀɪᴄ ɪᴅ.")
            return
        context.user_data["dm_target"] = target
        context.user_data["action"] = "dm_text"
        await msg.reply_text(f"✍ ꜱᴇɴᴅ ᴛʜᴇ ᴍᴇꜱꜱᴀɢᴇ ꜰᴏʀ <code>{target}</code>.", parse_mode="HTML")
        return

    if action == "dm_text":
        target = context.user_data.pop("dm_target", None)
        context.user_data.pop("action", None)
        if not target:
            await msg.reply_text("⚠ ᴛᴀʀɢᴇᴛ ʟᴏꜱᴛ.")
            return
        ok = await send_rich(context.bot, target, text)
        await msg.reply_text("✓ ᴅᴇʟɪᴠᴇʀᴇᴅ." if ok else "✕ ꜰᴀɪʟᴇᴅ.")
        return

    # ── single / bulk ───────────────────────────────────────
    if action in {"single", "bulk"}:
        single_mode = action == "single"
        valid, invalid = parse_entries(text, single_mode)

        if not valid:
            await msg.reply_text(
                f"{box_title('✕ ɴᴏ ᴛᴀʀɢᴇᴛ ✕')}\n{box_close()}\n\n"
                f"  <code>user@hi2.in</code>",
                parse_mode="HTML",
            )
            return

        cost = len(valid) * (SINGLE_CHECK_COST if single_mode else BULK_CHECK_COST)
        if not has_unlimited(uid, u) and u.get("credits", 0) < cost:
            await msg.reply_text(
                f"{box_title('⚠ ɴᴏ ᴄʀᴇᴅɪᴛꜱ ⚠')}\n{box_close()}\n\n"
                f"  ʀᴇǫᴜɪʀᴇᴅ ‣ {cost}\n  ʙᴀʟᴀɴᴄᴇ  ‣ {u.get('credits', 0)}",
                parse_mode="HTML",
            )
            return

        if not has_unlimited(uid, u):
            u["credits"] -= cost
            save_db()

        # ── SINGLE (looping) ────────────────────────────────
        if single_mode:
            email = valid[0]
            result, elapsed, status_msg = await scan_single_animated(msg, email)
            log_check(uid, u, email, result, "single")
            report = single_report(email, result, elapsed, uid, u)
            markup = back_keyboard()

            if status_msg is None:
                await msg.reply_text(report, parse_mode="HTML", reply_markup=markup)
            else:
                try:
                    await status_msg.edit_text(report, parse_mode="HTML", reply_markup=markup)
                except BadRequest:
                    await msg.reply_text(report, parse_mode="HTML", reply_markup=markup)

            if invalid:
                await msg.reply_text(skipped_report(invalid), parse_mode="HTML")

            # Keep "single" action active — next email loops automatically.
            await msg.reply_text(
                f"<b>{TL}{H * BOX_W}{TR}</b>\n"
                f"<b>{V}</b>  <i>{ARROW} ꜱᴇɴᴅ ɴᴇxᴛ ᴇᴍᴀɪʟ</i>  <b>{V}</b>\n"
                f"<b>{BL}{H * BOX_W}{BR}</b>",
                parse_mode="HTML",
                reply_markup=back_keyboard(),
            )
            return

        # ── BULK ────────────────────────────────────────────
        status_msg = await msg.reply_text(
            f"{box_title('❖ ʙᴜʟᴋ ᴄᴏʀᴇ ❖')}\n"
            f"{box_line(f'⟦{_bar(0, len(valid))}⟧  <b>0%</b>')}\n"
            f"{box_line('◜  ᴡᴀʀᴍɪɴɢ ᴄᴏʀᴇ…')}\n"
            f"{box_close()}",
            parse_mode="HTML",
        )
        lines, elapsed = await scan_bulk_animated(msg, valid, status_msg)

        for email, line in zip(valid, lines):
            res = "taken" if "ᴛᴀᴋᴇɴ" in line else (
                "not_taken" if "ꜰʀᴇᴇ" in line else "unknown"
            )
            log_check(uid, u, email, res, "bulk", save=False)
        save_db()

        chunks = bulk_report_chunks(lines, len(valid), elapsed)
        try:
            await status_msg.edit_text(chunks[0], parse_mode="HTML")
        except BadRequest:
            await msg.reply_text(chunks[0], parse_mode="HTML")
        for chunk in chunks[1:]:
            await msg.reply_text(chunk, parse_mode="HTML")

        if invalid:
            await msg.reply_text(skipped_report(invalid), parse_mode="HTML")

        context.user_data.pop("action", None)
        await msg.reply_text(
            "✓ ʙᴜʟᴋ ᴄᴏᴍᴘʟᴇᴛᴇ.",
            reply_markup=back_keyboard(),
        )
        return

    # ── admin actions ───────────────────────────────────────
    if action and is_staff(uid):
        parts = text.split()
        try:
            if action == "gen_code":
                if len(parts) != 2:
                    raise ValueError
                credits, max_claims = int(parts[0]), int(parts[1])
                if credits < 1 or max_claims < 1:
                    raise ValueError
                code = "KALLO-" + "".join(
                    secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6)
                )
                DB["redeem_codes"][code] = {
                    "credits": credits, "max_claims": max_claims, "claimed_by": [],
                }
                save_db()
                await msg.reply_text(
                    f"✓ ᴄᴏᴅᴇ ɢᴇɴᴇʀᴀᴛᴇᴅ\n<code>{code}</code>\n{credits} ᴄʀ · {max_claims} ᴄʟᴀɪᴍꜱ",
                    parse_mode="HTML",
                )
            elif action == "add_credits":
                if len(parts) != 2:
                    raise ValueError
                target, amount = str(int(parts[0])), int(parts[1])
                if amount < 1:
                    raise ValueError
                tu = DB["users"].setdefault(
                    target,
                    {"credits": 0, "unlimited": False, "referred_users": [],
                     "name": "User", "joined": utc_now()},
                )
                tu["credits"] = tu.get("credits", 0) + amount
                save_db()
                await msg.reply_text(f"✓ +{amount} → <code>{target}</code>", parse_mode="HTML")
                await send_rich(
                    context.bot, target,
                    f"♛ ᴄʀᴇᴅɪᴛꜱ ᴀᴅᴅᴇᴅ\n+{amount}  ·  ʙᴀʟᴀɴᴄᴇ: {tu['credits']}",
                )
            elif action in {"grant", "revoke"}:
                target = str(int(text))
                tu = DB["users"].setdefault(
                    target,
                    {"credits": 0, "unlimited": False, "referred_users": [],
                     "name": "User", "joined": utc_now()},
                )
                tu["unlimited"] = action == "grant"
                DB["premium_log"].append({"uid": target, "action": action, "ts": short_ts()})
                trim(DB["premium_log"], LOG_CAP)
                save_db()
                await msg.reply_text(
                    f"✓ {'ɢʀᴀɴᴛ' if action == 'grant' else 'ʀᴇᴠᴏᴋᴇ'} → <code>{target}</code>",
                    parse_mode="HTML",
                )
                await send_rich(
                    context.bot, target,
                    "♛ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴀᴛᴇᴅ" if action == "grant"
                    else "◈ ᴘʀᴇᴍɪᴜᴍ ᴇxᴘɪʀᴇᴅ",
                )
            elif action == "userinfo":
                target = str(int(text))
                tu = DB["users"].get(target)
                if not tu:
                    await msg.reply_text("✕ ɴᴏᴛ ꜰᴏᴜɴᴅ.")
                else:
                    checks = [r for r in DB["checks"] if r["uid"] == target]
                    await msg.reply_text(
                        f"{box_title('❖ ᴜꜱᴇʀ ɪɴꜰᴏ ❖')}\n{box_close()}\n\n"
                        f"  ɪᴅ        ‣ <code>{target}</code>\n"
                        f"  ɴᴀᴍᴇ      ‣ {html.escape(tu.get('name', 'User'))}\n"
                        f"  ᴄʀᴇᴅɪᴛꜱ   ‣ {tu.get('credits', 0)}\n"
                        f"  ᴘʀᴇᴍɪᴜᴍ   ‣ {bool(tu.get('unlimited'))}\n"
                        f"  ᴄʜᴇᴄᴋꜱ    ‣ {len(checks)}",
                        parse_mode="HTML",
                    )
            elif action == "broadcast":
                sent = failed = 0
                await msg.reply_text(f"❖ ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ → {len(DB['users'])} ᴜꜱᴇʀꜱ")
                for target in list(DB["users"]):
                    if await send_rich(context.bot, target, text):
                        sent += 1
                    else:
                        failed += 1
                    await asyncio.sleep(0.05)
                await msg.reply_text(f"✓ ꜱᴇɴᴛ: {sent}\n✕ ꜰᴀɪʟᴇᴅ: {failed}")
            elif action in {"add_admin", "remove_admin"}:
                if not is_owner(uid):
                    raise PermissionError
                target = str(int(text))
                if action == "add_admin":
                    if int(target) not in [int(x) for x in DB["admins"]]:
                        DB["admins"].append(int(target))
                        save_db()
                        await send_rich(context.bot, target, "♦ ᴀᴅᴍɪɴ ᴀᴄᴄᴇꜱꜱ ɢʀᴀɴᴛᴇᴅ")
                    await msg.reply_text(f"✓ <code>{target}</code> → ᴀᴅᴍɪɴ", parse_mode="HTML")
                else:
                    if int(target) == OWNER_USER_ID:
                        await msg.reply_text("♛ ᴏᴡɴᴇʀ ᴄᴀɴ'ᴛ ʙᴇ ᴅᴇᴍᴏᴛᴇᴅ.")
                    else:
                        DB["admins"] = [x for x in DB["admins"] if int(x) != int(target)]
                        save_db()
                        await send_rich(context.bot, target, "◈ ᴀᴅᴍɪɴ ᴀᴄᴄᴇꜱꜱ ʀᴇᴠᴏᴋᴇᴅ")
                        await msg.reply_text(f"✓ <code>{target}</code> ᴅᴇᴍᴏᴛᴇᴅ.", parse_mode="HTML")
        except PermissionError:
            await msg.reply_text("⛔ ᴏᴡɴᴇʀ ᴏɴʟʏ.")
        except (ValueError, TypeError):
            await msg.reply_text("⚠ ɪɴᴠᴀʟɪᴅ ꜰᴏʀᴍᴀᴛ.")
        context.user_data.pop("action", None)
        return

    if text.startswith("/"):
        return
    await msg.reply_text(menu_text(uid, u), reply_markup=main_keyboard(uid), parse_mode="HTML")


# ──────────────────────────────────────────────────────────────
# HIDDEN ADMIN COMMANDS
# ──────────────────────────────────────────────────────────────
async def setqr_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    if not user or not is_owner(user.id):
        await msg.reply_text("⛔ ᴏᴡɴᴇʀ ᴏɴʟʏ.")
        return
    replied = msg.reply_to_message
    if not replied:
        await msg.reply_text("ʀᴇᴘʟʏ ᴛᴏ ᴀɴ ɪᴍᴀɢᴇ ᴡɪᴛʜ /setqr")
        return
    file_id = None
    if replied.photo:
        file_id = replied.photo[-1].file_id
    elif replied.document and (replied.document.mime_type or "").startswith("image/"):
        file_id = replied.document.file_id
    if not file_id:
        await msg.reply_text("⚠ ɪᴍᴀɢᴇ ʀᴇǫᴜɪʀᴇᴅ.")
        return
    DB["settings"]["qr_file_id"] = file_id
    DB["settings"]["upi_id"] = "faridh@fam"
    DB["settings"]["upi_name"] = "FARID"
    save_db()
    await msg.reply_text("✓ ǫʀ ꜱᴀᴠᴇᴅ.")


async def panel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_staff(update.effective_user.id):
        await update.effective_message.reply_text("⛔ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ.")
        return
    await update.effective_message.reply_text(
        panel_text(), reply_markup=panel_keyboard(), parse_mode="HTML"
    )


async def addcredits_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_staff(uid):
        await update.effective_message.reply_text("⛔ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ.")
        return
    if len(context.args) != 2:
        await update.effective_message.reply_text("ᴜꜱᴀɢᴇ: /addcredits USER_ID AMOUNT")
        return
    try:
        target, amount = str(int(context.args[0])), int(context.args[1])
        if amount < 1:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text("ɪɴᴠᴀʟɪᴅ.")
        return
    tu = DB["users"].setdefault(
        target,
        {"credits": 0, "unlimited": False, "referred_users": [],
         "name": "User", "joined": utc_now()},
    )
    tu["credits"] = tu.get("credits", 0) + amount
    save_db()
    await update.effective_message.reply_text(f"✓ +{amount} → {target}")
    await send_rich(context.bot, target, f"♛ +{amount} ᴄʀᴇᴅɪᴛꜱ  ·  ʙᴀʟᴀɴᴄᴇ: {tu['credits']}")


async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_owner(uid):
        await update.effective_message.reply_text("⛔ ᴏᴡɴᴇʀ ᴏɴʟʏ.")
        return
    if len(context.args) != 1:
        await update.effective_message.reply_text("ᴜꜱᴀɢᴇ: /addadmin USER_ID")
        return
    try:
        target = str(int(context.args[0]))
    except ValueError:
        await update.effective_message.reply_text("ɪɴᴠᴀʟɪᴅ.")
        return
    if int(target) not in [int(x) for x in DB["admins"]]:
        DB["admins"].append(int(target))
        save_db()
        await send_rich(context.bot, target, "♦ ᴀᴅᴍɪɴ ᴀᴄᴄᴇꜱꜱ ɢʀᴀɴᴛᴇᴅ")
    await update.effective_message.reply_text(f"✓ {target} → ᴀᴅᴍɪɴ")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    err = context.error
    if isinstance(err, (TimedOut, NetworkError)):
        log.warning("Telegram network hiccup: %s", err)
        return
    if isinstance(err, RetryAfter):
        log.warning("Rate limit; retry after %ss", err.retry_after)
        return
    log.error("Unhandled update error", exc_info=(type(err), err, err.__traceback__))


async def post_init(app: Application):
    me = await app.bot.get_me()
    app.bot_data["bot_username"] = me.username
    log.info("KALLO NEXUS online as @%s", me.username)
    try:
        await app.bot.set_my_commands([
            ("start", "open the main menu"),
            ("help", "show the main menu"),
            ("single", "scan one email"),
            ("bulk", "scan multiple emails"),
        ])
    except Exception:
        log.exception("Could not set bot commands")


def main():
    if not BOT_TOKEN:
        raise SystemExit("Missing BOT_TOKEN environment variable.")

    print("""
    ╭─────────────────────────────╮
    │       ᴋᴀʟʟᴏ  ɴᴇxᴜꜱ           │
    │       scan core · v5         │
    ╰─────────────────────────────╯
    ❖ system initialised
    ❖ awaiting updates
    """)

    normal_request = HTTPXRequest(
        connection_pool_size=16, connect_timeout=60, read_timeout=60,
        write_timeout=60, pool_timeout=60,
    )
    polling_request = HTTPXRequest(
        connection_pool_size=4, connect_timeout=60, read_timeout=70,
        write_timeout=60, pool_timeout=60,
    )
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .request(normal_request)
        .get_updates_request(polling_request)
        .post_init(post_init)
        .build()
    )
    app.add_error_handler(error_handler)

    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CommandHandler("single", single_cmd))
    app.add_handler(CommandHandler("bulk", bulk_cmd))

    app.add_handler(CommandHandler("panel", panel_cmd))
    app.add_handler(CommandHandler("addcredits", addcredits_cmd))
    app.add_handler(CommandHandler("addadmin", admin_cmd))
    app.add_handler(CommandHandler("setqr", setqr_cmd))

    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    log.info("Starting long-polling worker")
    app.run_polling(drop_pending_updates=False, allowed_updates=Update.ALL_TYPES, timeout=30)


if __name__ == "__main__":
    main()
