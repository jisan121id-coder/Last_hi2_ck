"""
KALLO NEXUS — Final Xoss Edition (Advanced Engine)
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
DB_FILE = Path(os.getenv("DB_FILE", "data/kallo_db.json"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("kallo")

BRAND = "𝙆 𝘼 𝙇 𝙇 𝙊  𝙉 𝙀 𝙓 𝙐 𝙎"
DIV = "🔱══════════════════════🔱"

# ──────────────────────────────────────────────────────────────
# ADVANCED ENGINE (Cloudscraper + Recaptcha)
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

def build_session(seed_cookies=True):
    s = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
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
        r = session.get(anchor, timeout=12, headers={"User-Agent": random.choice(USER_AGENTS), "Referer": "https://hi2.in/"})
        if 'recaptcha-token" value="' not in r.text: return None
        token = r.text.split('recaptcha-token" value="')[1].split('"')[0]

        payload = f"v={RECAPTCHA_V}&reason=q&c={token}&k={RECAPTCHA_SITEKEY}&co={RECAPTCHA_CO}&hl=en&size=invisible"
        headers = {"User-Agent": random.choice(USER_AGENTS), "Referer": anchor, "Content-Type": "application/x-www-form-urlencoded", "Origin": "https://www.google.com"}
        
        d = session.post("https://www.google.com/recaptcha/enterprise/reload", data=payload, headers=headers, timeout=12)
        if 'resp","' not in d.text: return None
        return d.text.split('resp","')[1].split('"')[0]
    except Exception:
        return None

def check_hi2_email(email):
    if "@" not in email: return "unknown"
    prefix, domain = email.split("@", 1)
    domain = domain.lower()

    session = build_session()
    recaptcha = solve_recaptcha_hi2(session)
    if not recaptcha: return "unknown"

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
        if r.status_code == 403 and "Just a moment" in r.text: return "unknown"
        body = r.text.lower()
        if "already taken" in body or "taken" in body: return "taken"
        if "available" in body or "success" in body: return "not_taken"
        return "unknown"
    except Exception:
        return "unknown"

# ──────────────────────────────────────────────────────────────
# DATABASE
# ──────────────────────────────────────────────────────────────
def default_db(): return {"allowed_users": []}
def load_db():
    try:
        if DB_FILE.exists():
            with DB_FILE.open("r", encoding="utf-8") as f: return json.load(f)
    except: pass
    return default_db()

DB = load_db()
def save_db():
    try:
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(DB, f, indent=2)
    except: pass

def is_owner(uid): return int(uid) == OWNER_USER_ID
def is_allowed(uid): return is_owner(uid) or str(uid) in DB.get("allowed_users", [])

# ──────────────────────────────────────────────────────────────
# SCANNER & UI
# ──────────────────────────────────────────────────────────────
async def _tick(fut, seconds=1.0):
    try: await asyncio.wait_for(asyncio.shield(fut), timeout=seconds)
    except asyncio.TimeoutError: pass

async def scan_animated(msg, email):
    fut = asyncio.ensure_future(asyncio.to_thread(check_hi2_email, email))
    target = None
    while not fut.done():
        text = f"🔮 **𝙉𝙚𝙪𝙧𝙖𝙡 𝙎𝙘𝙖𝙣𝙣𝙞𝙣𝙜**\n`{html.escape(email)}`\n\n🧬 `Querying Registry...`\n\n{DIV}\n`> _ Please Wait`"
        try:
            if target is None: target = await msg.reply_text(text, parse_mode="HTML")
            else: await target.edit_text(text, parse_mode="HTML")
        except: pass
        await _tick(fut)
    return fut.result(), target

def get_result_text(email, result):
    if result == "not_taken": status = "🟢 **AVAILABLE**"
    elif result == "taken": status = "🔴 **TAKEN**"
    else: status = "🟡 **UNKNOWN**"
        
    return f"🔮 **𝙉𝙚𝙪𝙧𝙖𝙡 𝙑𝙚𝙧𝙙𝙞𝙘𝙩**\n\n🎯 `Target:` `{html.escape(email)}`\n◈ `Status:` {status}\n\n{DIV}\n`> _ Scan Complete.` 💀"

# ──────────────────────────────────────────────────────────────
# KEYBOARDS & HANDLERS
# ──────────────────────────────────────────────────────────────
def main_keyboard(uid):
    rows = [
        [InlineKeyboardButton("🗡 𝙎𝙞𝙣𝙜𝙡𝙚 𝙎𝙘𝙖𝙣", callback_data="single"), InlineKeyboardButton("🧬 𝘽𝙪𝙡𝙠 𝙋𝙧𝙤𝙘𝙚𝙨𝙨", callback_data="bulk")],
    ]
    if is_owner(uid):
        rows.append([InlineKeyboardButton("👑 𝘼𝙙𝙢𝙞𝙣 𝙋𝙖𝙣𝙚𝙡", callback_data="admin_panel")])
    return InlineKeyboardMarkup(rows)

def back_keyboard(): return InlineKeyboardMarkup([[InlineKeyboardButton("<< 𝙍𝙚𝙩𝙪𝙧𝙣", callback_data="home")]])
def admin_keyboard(): return InlineKeyboardMarkup([
    [InlineKeyboardButton("➕ 𝘼𝙙𝙙 𝙐𝙨𝙚𝙧", callback_data="add_user"), InlineKeyboardButton("➖ 𝙍𝙚𝙢𝙤𝙫𝙚 𝙐𝙨𝙚𝙧", callback_data="remove_user")],
    [InlineKeyboardButton("<< 𝘽𝙖𝙘𝙠 𝙩𝙤 𝙈𝙚𝙣𝙪", callback_data="home")]
])

def menu_text(uid):
    return f"⛓️ **{BRAND}** ⛓️\n`> Overlord Protocols Online.`\n\n🆔 `ID` : `{uid}`\n\n{DIV}\n\n`> Select Protocol Below`"

SINGLE_TEXT = f"🗡 **𝙉𝙚𝙪𝙧𝙖𝙡 𝙎𝙘𝙖𝙣**\n`> Send one email to begin.`\n\n{DIV}\n`> _ Awaiting Input`"
BULK_TEXT = f"🧬 **𝘽𝙪𝙡𝙠 𝙋𝙧𝙤𝙘𝙚𝙨𝙨**\n`> Send multiple emails (Space/Comma/Newline).`\n\n{DIV}\n`> _ Awaiting Input`"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_allowed(uid):
        await update.effective_message.reply_text(f"⛔ **Access Denied.**\n`> Your ID: {uid}`\n`> Contact Owner for access.`", parse_mode="HTML")
        return
    await update.effective_message.reply_text(menu_text(uid), reply_markup=main_keyboard(uid), parse_mode="HTML")

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    
    if not is_allowed(uid):
        await q.edit_message_text(f"⛔ **Access Denied.**", parse_mode="HTML")
        return

    if q.data == "home":
        context.user_data.pop("action", None)
        await q.edit_message_text(menu_text(uid), reply_markup=main_keyboard(uid), parse_mode="HTML")
    elif q.data == "single":
        context.user_data["action"] = "single"
        await q.edit_message_text(SINGLE_TEXT, reply_markup=back_keyboard(), parse_mode="HTML")
    elif q.data == "bulk":
        context.user_data["action"] = "bulk"
        await q.edit_message_text(BULK_TEXT, reply_markup=back_keyboard(), parse_mode="HTML")
    elif q.data == "admin_panel":
        if not is_owner(uid): return
        await q.edit_message_text(f"👑 **𝘼𝙙𝙢𝙞𝙣 𝘾𝙤𝙧𝙚**\n`> Manage allowed users.`\n\n{DIV}", reply_markup=admin_keyboard(), parse_mode="HTML")
    elif q.data == "add_user":
        if not is_owner(uid): return
        context.user_data["action"] = "awaiting_add"
        await q.edit_message_text(f"➕ **𝘼𝙙𝙙 𝙐𝙨𝙚𝙧**\n`> Send the User ID to allow access.`\n\n{DIV}\n`> _ Awaiting Input`", reply_markup=back_keyboard(), parse_mode="HTML")
    elif q.data == "remove_user":
        if not is_owner(uid): return
        context.user_data["action"] = "awaiting_remove"
        await q.edit_message_text(f"➖ **𝙍𝙚𝙢𝙤𝙫𝙚 𝙐𝙨𝙚𝙧**\n`> Send the User ID to remove access.`\n\n{DIV}\n`> _ Awaiting Input`", reply_markup=back_keyboard(), parse_mode="HTML")

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    uid = update.effective_user.id
    
    if not is_allowed(uid):
        await msg.reply_text(f"⛔ **Access Denied.**\n`> Your ID: {uid}`", parse_mode="HTML")
        return

    text = msg.text.strip()
    action = context.user_data.get("action")

    if action == "awaiting_add" and is_owner(uid):
        try:
            target = str(int(text))
            if target not in DB["allowed_users"] and int(target) != OWNER_USER_ID:
                DB["allowed_users"].append(target)
                save_db()
            await msg.reply_text(f"✅ `User {target} added.`", parse_mode="HTML", reply_markup=main_keyboard(uid))
        except:
            await msg.reply_text("⚠️ `Invalid ID.`", parse_mode="HTML")
        context.user_data.pop("action", None)
        return

    if action == "awaiting_remove" and is_owner(uid):
        try:
            target = str(int(text))
            if target in DB["allowed_users"]:
                DB["allowed_users"].remove(target)
                save_db()
            await msg.reply_text(f"✅ `User {target} removed.`", parse_mode="HTML", reply_markup=main_keyboard(uid))
        except:
            await msg.reply_text("⚠️ `Invalid ID.`", parse_mode="HTML")
        context.user_data.pop("action", None)
        return

    if action == "single":
        email = text.split()[0]
        if "@" not in email: email = f"{email}@hi2.in"
        res, status_msg = await scan_animated(msg, email)
        report = get_result_text(email, res)
        await status_msg.edit_text(report, parse_mode="HTML", reply_markup=back_keyboard())
        await msg.reply_text(f"`> Send next email to continue.`", parse_mode="HTML", reply_markup=back_keyboard())

    elif action == "bulk":
        emails = text.replace(",", " ").split()
        valid = [e if "@" in e else f"{e}@hi2.in" for e in emails]
        
        status_msg = await msg.reply_text(f"🧬 `Processing {len(valid)} targets...`", parse_mode="HTML")
        results = []
        for e in valid:
            res = await asyncio.to_thread(check_hi2_email, e)
            status = "🟢 **AVAILABLE**" if res == "not_taken" else "🔴 **TAKEN**" if res == "taken" else "🟡 **UNKNOWN**"
            results.append(f"`{e}` ➔ {status}")
        
        report = f"🔮 **𝘽𝙪𝙡𝙠 𝙍𝙚𝙨𝙪𝙡𝙩𝙨**\n\n" + "\n".join(results) + f"\n\n{DIV}\n`> _ Conquest Complete.` 💀"
        await status_msg.edit_text(report, parse_mode="HTML", reply_markup=back_keyboard())
        context.user_data.pop("action", None)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.run_polling()

if __name__ == "__main__":
    main()
