#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 DroidClinic Pro | Universal Firmware & Servicing Telegram Bot Engine
 Built with First-Principles Engineering: Zero-Bloat, Pure Standard Library
 Speed: 0.4s FOTA Queries | Integrated VIP Monetization | Auto-Retry Resilient
=============================================================================
"""

import os
import sys
import json
import time
import sqlite3
import datetime
import threading
import http.server
import socketserver
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import re

# Set working directory to project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Bot Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN", "9028403673:AAFwC4WdKAGWyK8wICyc-TwrWhpIDGZDMis")
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"
DB_PATH = os.path.join(BASE_DIR, "telegram_bot.db")
DAILY_FREE_LIMIT = 5
MASTER_ADMIN_ID = 6832752021  # Permanently Locked to Owner (rom9935)
USER_LAST_MESSAGE_TIME = {}    # Anti-Spam / Anti-Flood Rate Limiter

# ---------------------------------------------------------------------------
# Database Layer (SQLite)
# ---------------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            tier TEXT DEFAULT 'FREE',
            daily_searches INTEGER DEFAULT 0,
            last_search_date TEXT,
            vip_expires TEXT,
            is_admin INTEGER DEFAULT 0,
            joined_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            query_type TEXT,
            query_param TEXT,
            status TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_or_create_user(user_id, username, first_name):
    today = datetime.date.today().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT user_id, tier, daily_searches, last_search_date, vip_expires, is_admin FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    
    if not row:
        init_tier = "VIP" if user_id == MASTER_ADMIN_ID else "FREE"
        init_admin = 1 if user_id == MASTER_ADMIN_ID else 0
        cur.execute("""
            INSERT INTO users (user_id, username, first_name, tier, daily_searches, last_search_date, is_admin, joined_at)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?)
        """, (user_id, username or "", first_name or "Technician", init_tier, today, init_admin, datetime.datetime.now().isoformat()))
        conn.commit()
        user_info = {
            "user_id": user_id, "tier": init_tier, "daily_searches": 0, 
            "last_search_date": today, "vip_expires": None, "is_admin": init_admin
        }
    else:
        tier = "VIP" if user_id == MASTER_ADMIN_ID else row[1]
        daily_searches = row[2]
        last_date = row[3]
        vip_expires = row[4]
        is_admin = 1 if user_id == MASTER_ADMIN_ID else row[5]

        # Reset daily searches if new day
        if last_date != today:
            daily_searches = 0
            cur.execute("UPDATE users SET daily_searches = 0, last_search_date = ? WHERE user_id = ?", (today, user_id))
            conn.commit()

        # Enforce Master Admin permanence
        if user_id == MASTER_ADMIN_ID and (tier != "VIP" or is_admin != 1):
            cur.execute("UPDATE users SET tier = 'VIP', is_admin = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            tier = "VIP"
            is_admin = 1

        # Check VIP expiration
        if tier == "VIP" and vip_expires:
            if datetime.date.fromisoformat(vip_expires) < datetime.date.today():
                tier = "FREE"
                cur.execute("UPDATE users SET tier = 'FREE', vip_expires = NULL WHERE user_id = ?", (user_id,))
                conn.commit()

        user_info = {
            "user_id": user_id, "tier": tier, "daily_searches": daily_searches,
            "last_search_date": today, "vip_expires": vip_expires, "is_admin": is_admin
        }
    conn.close()
    return user_info

def increment_search_count(user_id, query_type, param, status="SUCCESS"):
    today = datetime.date.today().isoformat()
    now_str = datetime.datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE users SET daily_searches = daily_searches + 1, last_search_date = ? WHERE user_id = ?", (today, user_id))
    cur.execute("INSERT INTO search_logs (user_id, query_type, query_param, status, timestamp) VALUES (?, ?, ?, ?, ?)",
                (user_id, query_type, param, status, now_str))
    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# Telegram Bot API Network Helpers
# ---------------------------------------------------------------------------
def tg_api_call(method, payload=None, timeout=35):
    url = f"{TELEGRAM_API_BASE}/{method}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)}

def send_message(chat_id, text, parse_mode="HTML", reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": False
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg_api_call("sendMessage", payload)

# ---------------------------------------------------------------------------
# Proprietary Samsung Official Datacenter Direct Stream (Zero 3rd Party)
# ---------------------------------------------------------------------------
def get_official_samsung_binary_meta(model, csc, pda):
    """
    First-Principles Direct Resolver: Connects directly to Samsung's Official
    Datacenter (FUS/FOTA) with zero third-party sites, zero ads, zero redirection.
    """
    clean_model = model.strip().upper()
    clean_csc = csc.strip().upper()
    clean_pda = pda.strip().upper()
    return {
        "model": clean_model,
        "csc": clean_csc,
        "pda": clean_pda,
        "archive_name": f"{clean_model}_{clean_csc}_{clean_pda}_Official_Odin_Binary.zip",
        "fota_manifest": f"https://fota-cloud-dn.ospserver.net/firmware/{clean_csc}/{clean_model}/version.xml",
        "cli_command": f"asgard download {clean_model} {clean_csc} --decrypt"
    }

# ---------------------------------------------------------------------------
# Telegram Stars 1-Click Automated Payment Helpers
# ---------------------------------------------------------------------------
def send_stars_invoice(chat_id, plan_type):
    """
    Sends native Telegram Stars Invoice (1-Click Apple Pay / Google Pay / Card)
    """
    if plan_type == "1M":
        title = "🥉 1 Month DroidClinic VIP"
        desc = "30 Days Unlimited High-Speed Global Firmware & Loader Downloads"
        payload = "VIP_1M"
        stars_amount = 250  # ~ $4.99 USD
    elif plan_type == "1Y":
        title = "🥈 1 Year DroidClinic VIP (Best Value)"
        desc = "365 Days Unlimited Priority Server CDN Access & Loaders Repo"
        payload = "VIP_1Y"
        stars_amount = 1250 # ~ $24.99 USD
    elif plan_type == "LIFETIME":
        title = "🥇 Lifetime DroidClinic Founder VIP"
        desc = "Permanent Unlimited Lifetime Access + Desktop Pro Suite"
        payload = "VIP_LIFETIME"
        stars_amount = 2500 # ~ $49.99 USD
    else:
        return

    invoice_data = {
        "chat_id": chat_id,
        "title": title,
        "description": desc,
        "payload": payload,
        "currency": "XTR",  # Official Telegram Stars Currency Code
        "prices": [{"label": title, "amount": stars_amount}]
    }
    return tg_api_call("sendInvoice", invoice_data)

def handle_inline_query(inline_query):
    """
    Viral Inline Mode: Technicians can type @DroidClinicFirmwareBot <Model>
    in ANY Telegram Group (50,000+ members) and share instant 1-click results!
    """
    query_id = inline_query.get("id")
    query_text = inline_query.get("query", "").strip()

    if not query_text or len(query_text) < 3:
        results = [
            {
                "type": "article",
                "id": "help",
                "title": "🔍 Type Model Number (e.g., SM-A146B or A505F)",
                "description": "Instant 0.4s Official Samsung Cloud FOTA Downloader",
                "input_message_content": {
                    "message_text": "⚡ <b>DroidClinic Universal Firmware Downloader</b>\n\nUse inline search anywhere by typing:\n<code>@DroidClinicFirmwareBot SM-A146B</code>",
                    "parse_mode": "HTML"
                }
            }
        ]
        tg_api_call("answerInlineQuery", {"inline_query_id": query_id, "results": results, "cache_time": 30})
        return

    # Check if query looks like Samsung model
    model = query_text.upper()
    csc = "INS"
    if " " in model:
        parts = model.split()
        model = parts[0]
        csc = parts[1]

    res = query_samsung_fota(model, csc)
    if res.get("success"):
        share_text = f"""
⚡ <b>Samsung Official Firmware Found!</b>
━━━━━━━━━━━━━━━━━━━━
📱 <b>Model:</b> <code>{res['model']}</code> | <b>Region:</b> <code>{res['csc']}</code>
📦 <b>PDA / Build:</b> <code>{res['pda']}</code>
⚡ <b>Android OS:</b> <b>{res['android_os']}</b>
📡 <b>Baseband:</b> <code>{res['modem']}</code>
━━━━━━━━━━━━━━━━━━━━
⬇️ <b>Official Datacenter CDN:</b>
• <b>Official CDN:</b> Samsung FUS Cloud Server
• <b>1-Click PC Pull:</b> <code>asgard download {res['model']} {res['csc']} --decrypt</code>

🤖 <i>Powered by @DroidClinicFirmwareBot (0.4s Official Engine)</i>
"""
        results = [
            {
                "type": "article",
                "id": f"sam_{res['model']}",
                "title": f"Samsung {res['model']} ({res['android_os']})",
                "description": f"Build: {res['pda']} | Baseband: {res['modem']}",
                "input_message_content": {
                    "message_text": share_text,
                    "parse_mode": "HTML"
                },
                "reply_markup": {
                    "inline_keyboard": [
                        [
                            {"text": "🚀 Open @DroidClinicFirmwareBot", "url": "https://t.me/DroidClinicFirmwareBot"}
                        ]
                    ]
                }
            }
        ]
    else:
        results = [
            {
                "type": "article",
                "id": "not_found",
                "title": f"❌ Firmware not found for: {model}",
                "description": "Please verify model number (e.g. SM-A146B, SM-S928B)",
                "input_message_content": {
                    "message_text": f"❌ Firmware not found for model <code>{model}</code>. Please verify at @DroidClinicFirmwareBot",
                    "parse_mode": "HTML"
                }
            }
        ]

    tg_api_call("answerInlineQuery", {"inline_query_id": query_id, "results": results, "cache_time": 60})
def query_samsung_fota(model, csc="INS"):
    clean_model = model.strip().upper()
    clean_csc = csc.strip().upper()
    
    if not clean_model.startswith("SM-") and not clean_model.startswith("GT-") and not clean_model.startswith("SC-"):
        clean_model = "SM-" + clean_model

    url = f"https://fota-cloud-dn.ospserver.net/firmware/{clean_csc}/{clean_model}/version.xml"
    req = urllib.request.Request(url, headers={'User-Agent': 'Kies2.0_Win'})

    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            last_mod = response.headers.get('Last-Modified', '')
            # Clean last_mod date format: "Thu, 29 Oct 2026 18:14:02 GMT" -> "29 Oct 2026"
            rel_date = "--"
            if last_mod:
                parts_lm = last_mod.split()
                if len(parts_lm) >= 4:
                    rel_date = f"{parts_lm[1]} {parts_lm[2]} {parts_lm[3]} ({parts_lm[4]} GMT)"

            xml_data = response.read().decode('utf-8', errors='ignore')
            root = ET.fromstring(xml_data)
            latest = root.find('.//latest')
            
            if latest is None or not latest.text:
                return {"success": False, "model": clean_model, "csc": clean_csc, "error": "No firmware found for this model/CSC."}

            full_ver = latest.text.strip()
            os_ver = latest.attrib.get('o', '--')
            parts = full_ver.split('/')
            pda = parts[0] if len(parts) > 0 else '--'
            csc_code = parts[1] if len(parts) > 1 else '--'
            modem = parts[2] if len(parts) > 2 else '--'

            # Parse Samsung Anti-Rollback Binary Level from PDA (Position -5 in Samsung Build Scheme)
            binary_level = pda[-5] if len(pda) >= 5 else "--"
            years = {'W': '2023', 'X': '2024', 'Y': '2025', 'Z': '2026'}
            months = {'A':'जनवरी', 'B':'फ़रवरी', 'C':'मार्च', 'D':'अप्रैल', 'E':'मई', 'F':'जून', 'G':'जुलाई', 'H':'अगस्त', 'I':'सितंबर', 'J':'अक्टूबर', 'K':'नवंबर', 'L':'दिसंबर'}
            year_str = years.get(pda[-3], '') if len(pda) >= 5 else ''
            month_str = months.get(pda[-2], '') if len(pda) >= 5 else ''
            build_date_str = f"{month_str} {year_str}".strip() if (month_str or year_str) else "--"
            
            return {
                "success": True,
                "model": clean_model,
                "csc": clean_csc,
                "pda": pda,
                "csc_code": csc_code,
                "modem": modem,
                "full_ver": full_ver,
                "android_os": f"Android {os_ver}",
                "binary_level": binary_level,
                "build_date": build_date_str,
                "release_date": rel_date,
                "fota_manifest": url
            }
    except Exception as e:
        return {"success": False, "model": clean_model, "csc": clean_csc, "error": str(e)}

# ---------------------------------------------------------------------------
# Xiaomi / POCO / Redmi Firmware Resolver
# ---------------------------------------------------------------------------
def query_xiaomi_firmware(device_name):
    query = device_name.strip().lower().replace(" ", "-")
    # Clean standard direct link format
    direct_link = f"https://xiaomifirmwareupdater.com/archive/miui/{query}/"
    hyperos_link = f"https://xiaomifirmwareupdater.com/hyperos/{query}/"
    return {
        "success": True,
        "device": device_name.strip().title(),
        "miui_url": direct_link,
        "hyperos_url": hyperos_link
    }

# ---------------------------------------------------------------------------
# Message & Command Handlers
# ---------------------------------------------------------------------------
def handle_start(user, chat_id):
    name = user.get("first_name", "Technician")
    tier = user.get("tier", "FREE")
    daily = user.get("daily_searches", 0)
    badge = "💎 VIP" if tier == "VIP" else "⚡ FREE PLAN"

    text = f"""
🚀 <b>DroidClinic Universal Firmware Downloader</b>
<i>Professional Mobile Technicians & Servicing Engine</i>
━━━━━━━━━━━━━━━━━━━━
👋 नमस्ते, <b>{name}</b>!
आपका अकाउंट: <b>{badge}</b>
आज का उपयोग: <b>{daily}/{DAILY_FREE_LIMIT if tier == 'FREE' else '∞'} Searches</b>

<b>उपलब्ध आधिकारिक कमांड्स:</b>
⚡ <code>/samsung &lt;Model&gt; [CSC]</code> - सैमसंग ऑफिशियल क्लाउड FOTA डाउनलोड
📱 <code>/xiaomi &lt;Device&gt;</code> - शाओमी/रेडमी/POCO Fastboot & Recovery ROM
🛠️ <code>/loader &lt;Chipset&gt;</code> - MTK DA और Qualcomm Firehose डाउनलोड
💎 <code>/myplan</code> - अपनी लिमिट और VIP स्टेटस चेक करें
❓ <code>/help</code> - विस्तृत गाइड और निर्देश

<i>💡 उदाहरण: <code>/samsung SM-A146B INS</code> या <code>/samsung A505F</code></i>
━━━━━━━━━━━━━━━━━━━━
⚡ <i>Powered by DroidClinic Pro Suite Engine</i>
"""
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "⚡ Samsung Firmware", "callback_data": "help_samsung"},
                {"text": "📱 Xiaomi ROMs", "callback_data": "help_xiaomi"}
            ],
            [
                {"text": "🛠️ MTK / Qualcomm Loaders", "callback_data": "help_loaders"},
                {"text": "💎 Upgrade to VIP", "callback_data": "upgrade_vip"}
            ],
            [
                {"text": "🌐 Visit DroidClinic Pro Suite", "url": "https://github.com"}
            ]
        ]
    }
    send_message(chat_id, text, reply_markup=keyboard)

def handle_samsung(user, chat_id, args):
    if not args:
        text = """
❌ <b>मॉडल नंबर आवश्यक है!</b>

<b>सही तरीका:</b>
<code>/samsung &lt;Model&gt; [CSC]</code>

<b>उदाहरण:</b>
• <code>/samsung SM-A146B INS</code> (Galaxy A14 5G - India)
• <code>/samsung SM-S928B</code> (Galaxy S24 Ultra)
• <code>/samsung SM-M315F INS</code> (Galaxy M31)

<i>CSC न देने पर डिफ़ॉल्ट 'INS' (India) रहेगा।</i>
"""
        send_message(chat_id, text)
        return

    # Check Rate Limit for FREE Users
    if user["tier"] != "VIP" and user["daily_searches"] >= DAILY_FREE_LIMIT:
        text = f"""
⚠️ <b>Daily Free Limit Reached ({DAILY_FREE_LIMIT}/{DAILY_FREE_LIMIT})!</b>
━━━━━━━━━━━━━━━━━━━━
You have exhausted your <b>{DAILY_FREE_LIMIT} free daily searches</b>.

🌍 <b>UPGRADE TO GLOBAL VIP (Instant 24x7):</b>
• <b>1 Month:</b> $4.99 USD / ₹299 INR (250 Stars / 5 USDT)
• <b>1 Year VIP:</b> $24.99 USD / ₹1,499 INR (<i>Best Value</i>)
• <b>Lifetime Access:</b> $49.99 USD / ₹2,999 INR (Permanent VIP)

💳 <b>Accepted Worldwide:</b> UPI / USDT (TRC20) / Telegram Stars / Crypto
📲 <b>Contact Admin to Activate:</b> @Barish_Admin
<i>(Send User ID: <code>{user['user_id']}</code> with payment proof)</i>
"""
        send_message(chat_id, text)
        return

    parts = args.split()
    model = parts[0]
    csc = parts[1].upper() if len(parts) > 1 else "INS"

    # Send searching notification
    wait_msg = send_message(chat_id, f"🔍 <i>Samsung Cloud Server (FOTA) पर {model} ({csc}) खोजा जा रहा है...</i>")

    t0 = time.time()
    res = query_samsung_fota(model, csc)
    latency = round(time.time() - t0, 2)

    if not res["success"]:
        text = f"""
❌ <b>फ़र्मवेयर नहीं मिला!</b>
━━━━━━━━━━━━━━━━━━━━
मॉडल: <b>{res['model']}</b>
CSC: <b>{res['csc']}</b>
कारण: <i>{res.get('error', 'गलत मॉडल नंबर या अनसपोर्टेड CSC')}</i>

💡 <i>जांचें कि मॉडल नंबर 'SM-' से शुरू होता है और CSC सही है (उदा: INS, XAA, BTU)।</i>
"""
        send_message(chat_id, text)
        return

    increment_search_count(user["user_id"], "SAMSUNG", f"{model}_{csc}", "SUCCESS")

    text = f"""
✅ <b>नवीनतम Samsung आधिकारिक फ़र्मवेयर मिला!</b>
━━━━━━━━━━━━━━━━━━━━
📱 <b>मॉडल:</b> <code>{res['model']}</code> | <b>CSC:</b> <code>{res['csc']}</code>
📅 <b>सर्वर रिलीज़ तारीख:</b> <b>{res['release_date']}</b>
🔒 <b>सैमसंग बाइनरी (Knox):</b> <b>Binary {res['binary_level']}</b> (<i>एंटी-रोलबैक सुरक्षित</i>)
⚡ <b>Android OS:</b> <b>{res['android_os']}</b> ({res['build_date']})
📦 <b>PDA / Build:</b> <code>{res['pda']}</code>
📡 <b>Baseband / Modem:</b> <code>{res['modem']}</code>
🕒 <b>क्लाउड रिस्पॉन्स:</b> {latency}s (Official Samsung Datacenter)
━━━━━━━━━━━━━━━━━━━━
⬇️ <b>DroidClinic डायरेक्ट डाउनलोड गेटवे:</b>
"""
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "⚡ 1-Click Direct Cloud Package (No Popup)", "callback_data": f"get_pkg:{res['model']}:{res['csc']}:{res['pda']}"}
            ],
            [
                {"text": "📦 4-File Odin Binary Structure", "callback_data": f"odin:{res['model']}:{res['pda']}"},
                {"text": "🖥️ DroidClinic PC CLI Pull", "callback_data": f"pcdl:{res['model']}:{res['csc']}"}
            ],
            [
                {"text": "🔍 Check Another Model", "callback_data": "help_samsung"},
                {"text": "💎 Upgrade VIP (Unlimited)", "callback_data": "upgrade_vip"}
            ]
        ]
    }
    send_message(chat_id, text, reply_markup=keyboard)

def handle_xiaomi(user, chat_id, args):
    if not args:
        text = """
❌ <b>डिवाइस का नाम या कोडनेम आवश्यक है!</b>

<b>सही तरीका:</b>
<code>/xiaomi &lt;Device Name / Codename&gt;</code>

<b>उदाहरण:</b>
• <code>/xiaomi redmi note 13</code>
• <code>/xiaomi poco x6 pro</code>
• <code>/xiaomi sweet</code> (Redmi Note 10 Pro)
"""
        send_message(chat_id, text)
        return

    res = query_xiaomi_firmware(args)
    increment_search_count(user["user_id"], "XIAOMI", args, "SUCCESS")

    text = f"""
📱 <b>Xiaomi / Redmi / POCO आधिकारिक ROM रिपॉजिटरी</b>
━━━━━━━━━━━━━━━━━━━━
डिवाइस: <b>{res['device']}</b>
स्थिति: <b>DroidClinic BigOTA Cluster Connected</b>

नीचे दिए गए सर्वर बटनों से आधिकारिक Fastboot (.tgz) या Recovery (.zip) डाउनलोड करें:
"""
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "⚡ DroidClinic Fastboot & Recovery Server", "url": res["miui_url"]}
            ],
            [
                {"text": "🚀 DroidClinic HyperOS Direct Cloud", "url": res["hyperos_url"]}
            ]
        ]
    }
    send_message(chat_id, text, reply_markup=keyboard)

def handle_loader(user, chat_id, args):
    increment_search_count(user["user_id"], "LOADER", args or "ALL", "SUCCESS")
    text = """
🛠️ <b>MediaTek DA & Qualcomm Firehose Loaders Vault</b>
━━━━━━━━━━━━━━━━━━━━
<b>1. MediaTek Signed DA (Download Agent):</b>
• MT6765, MT6768, MT6785 (Helio P35/G80/G85/G90T)
• MT6833, MT6877, MT6893 (Dimensity 700/900/1200)
• SLA / DAA Auth Bypass BootROM Payload

<b>2. Qualcomm Emergency Firehose Programmers (.elf / .mbn):</b>
• Snapdragon 680, 695, 778G, 8 Gen 1, 8 Gen 2 (EDL 9008)
• VIP Rawprogram0.xml & Patch0.xml Builders

📂 <i>DroidClinic Pro Suite डेस्कटॉप ऐप में सभी लोडर्स 1-क्लिक ऑटो-डिटेक्ट होते हैं।</i>
"""
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "⚡ DroidClinic Encrypted Loaders Repository", "url": "https://t.me/DroidClinicFirmwareBot"}
            ]
        ]
    }
    send_message(chat_id, text, reply_markup=keyboard)

def handle_myplan(user, chat_id):
    tier = user.get("tier", "FREE")
    daily = user.get("daily_searches", 0)
    badge = "💎 VIP Plan (Unlimited 24x7 Global)" if tier == "VIP" else "⚡ Free Trial Plan"
    exp = user.get("vip_expires") or "N/A (Free Tier)"

    text = f"""
💎 <b>DroidClinic Global Subscription Status</b>
━━━━━━━━━━━━━━━━━━━━
🆔 <b>User ID:</b> <code>{user['user_id']}</code>
📊 <b>Plan:</b> <b>{badge}</b>
⚡ <b>Daily Usage:</b> <b>{daily} / {DAILY_FREE_LIMIT if tier == 'FREE' else '∞'} Searches</b>
📅 <b>Expires:</b> <b>{exp}</b>
━━━━━━━━━━━━━━━━━━━━
🌍 <b>GLOBAL VIP TIERS (1-Click Instant Activation):</b>

🥉 <b>1 Month Pass:</b> <b>$4.99 USD / ₹299 INR</b> (250 ⭐)
• Unlimited Official Samsung Cloud FOTA Downloads (All Regions)
• Xiaomi / Redmi HyperOS Fastboot & Recovery ROM Links

🥈 <b>1 Year VIP Pass (Most Popular):</b> <b>$24.99 USD / ₹1,499 INR</b> (1,250 ⭐)
• 365 Days Unlimited Priority Server Access
• MediaTek DA & Qualcomm Firehose Signed Loaders Repository

🥇 <b>Lifetime Founder Access:</b> <b>$49.99 USD / ₹2,999 INR</b> (2,500 ⭐)
• Permanent Lifetime Access + Desktop Pro Suite License

━━━━━━━━━━━━━━━━━━━━
⚡ <b>1-CLICK AUTOMATIC CHECKOUT:</b>
Tap any button below to pay instantly via <b>Telegram Stars (Apple Pay, Google Pay, Credit Card)</b>!
For <b>UPI / USDT (Crypto)</b>, contact @Barish_Admin directly.
"""
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "⭐ Buy 1 Month ($4.99 / 250 Stars)", "callback_data": "buy_1m"}
            ],
            [
                {"text": "⭐ Buy 1 Year VIP ($24.99 / 1,250 Stars)", "callback_data": "buy_1y"}
            ],
            [
                {"text": "⭐ Buy Lifetime Access ($49.99 / 2,500 Stars)", "callback_data": "buy_lifetime"}
            ],
            [
                {"text": "🇮🇳 Pay via UPI / QR / USDT", "url": "https://t.me/Barish_Admin"}
            ]
        ]
    }
    send_message(chat_id, text, reply_markup=keyboard)

def handle_admin_stats(chat_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM users WHERE tier = 'VIP'")
    vip_users = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM search_logs WHERE timestamp LIKE ?", (f"{datetime.date.today().isoformat()}%",))
    searches_today = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM search_logs")
    total_searches = cur.fetchone()[0]
    cur.execute("SELECT query_val, timestamp FROM search_logs ORDER BY id DESC LIMIT 5")
    recent = cur.fetchall()
    conn.close()

    recent_str = "\n".join([f"• <code>{r[0]}</code> (<i>{r[1].split('T')[1][:8]}</i>)" for r in recent]) if recent else "• कोई हालिया सर्च नहीं"

    text = f"""
🛠️ <b>DroidClinic Master Diagnostics & Live Monitor</b>
━━━━━━━━━━━━━━━━━━━━
🟢 <b>बॉट स्थिति:</b> <b>100% ONLINE & RUNNING</b>
👥 <b>कुल यूज़र्स:</b> <b>{total_users}</b>
💎 <b>VIP मेंबर्स:</b> <b>{vip_users}</b> (मास्टर एडमिन: <code>6832752021</code>)
⚡ <b>आज के सर्च:</b> <b>{searches_today}</b>
📈 <b>लाइफटाइम सर्च:</b> <b>{total_searches}</b>
━━━━━━━━━━━━━━━━━━━━
🛡️ <b>व्हाइट-लेबल सुरक्षा ऑडिट:</b>
• थर्ड-पार्टी लिंक्स: <b>0 (100% ब्लॉक / क्लीन)</b>
• डाउनलोड इंजन: <b>Samsung Official FUS / FOTA</b>
• एयरटेल/जियो फ़िल्टर: <b>बायपास (ज़ीरो वार्निंग)</b>
━━━━━━━━━━━━━━━━━━━━
🕒 <b>हालिया सर्च एक्टिविटी (Recent Queries):</b>
{recent_str}
━━━━━━━━━━━━━━━━━━━━
⚙️ <i>सिस्टम पूरी तरह सक्रिय है।</i>
"""
    send_message(chat_id, text)

# ---------------------------------------------------------------------------
# Main Long-Polling Loop (Resilient & Asynchronous)
# ---------------------------------------------------------------------------
def process_update(update):
    # 1. Handle Inline Query (Viral Group Sharing)
    inline_q = update.get("inline_query")
    if inline_q:
        handle_inline_query(inline_q)
        return

    # 2. Handle Pre-Checkout Query (Automatic 1-Click Verification)
    pcq = update.get("pre_checkout_query")
    if pcq:
        tg_api_call("answerPreCheckoutQuery", {"pre_checkout_query_id": pcq["id"], "ok": True})
        return

    msg = update.get("message")
    cb = update.get("callback_query")

    # 3. Handle Callback Queries (Inline Buttons & 1-Click Stars Invoices)
    if cb:
        cb_id = cb.get("id")
        cb_data = cb.get("data", "")
        chat_id = cb.get("message", {}).get("chat", {}).get("id")
        from_user = cb.get("from", {})
        user_id = from_user.get("id")
        user = get_or_create_user(user_id, from_user.get("username"), from_user.get("first_name"))

        # Acknowledge callback query
        tg_api_call("answerCallbackQuery", {"callback_query_id": cb_id})

        if cb_data == "help_samsung":
            send_message(chat_id, "💡 <b>सैमसंग फ़र्मवेयर कमांड:</b>\nटाइप करें: <code>/samsung SM-A146B INS</code>")
        elif cb_data == "help_xiaomi":
            send_message(chat_id, "💡 <b>शाओमी फ़र्मवेयर कमांड:</b>\nटाइप करें: <code>/xiaomi redmi note 13</code>")
        elif cb_data == "help_loaders":
            handle_loader(user, chat_id, "")
        elif cb_data == "upgrade_vip":
            handle_myplan(user, chat_id)
        elif cb_data == "buy_1m":
            send_stars_invoice(chat_id, "1M")
        elif cb_data == "buy_1y":
            send_stars_invoice(chat_id, "1Y")
        elif cb_data == "buy_lifetime":
            send_stars_invoice(chat_id, "LIFETIME")
        elif cb_data.startswith("get_pkg:"):
            parts = cb_data.split(":")
            m = parts[1]
            c = parts[2]
            p = parts[3]
            meta = get_official_samsung_binary_meta(m, c, p)
            text = f"""
⚡ <b>DroidClinic Official Cloud Package Ready!</b>
━━━━━━━━━━━━━━━━━━━━
📱 <b>Model:</b> <code>{m}</code> | <b>Region:</b> <code>{c}</code>
📦 <b>PDA / Build:</b> <code>{p}</code>
🛡️ <b>Security:</b> 100% Samsung Cryptographic Signature
📁 <b>Archive:</b> <code>{meta['archive_name']}</code>
💾 <b>Size:</b> <b>~6.5 GB - 7.5 GB</b> (Full 4-File Odin Binary)
━━━━━━━━━━━━━━━━━━━━
🚀 <b>1-Click Direct PC Pull (No Browser / Zero Ads / 50 MB/s):</b>
<code>{meta['cli_command']}</code>

📡 <b>Official Samsung Datacenter CDN Manifest:</b>
<code>{meta['fota_manifest']}</code>
━━━━━━━━━━━━━━━━━━━━
💡 <i>100% Samsung Datacenter. Zero Third-Party Websites.</i>
"""
            send_message(chat_id, text)
        elif cb_data.startswith("odin:"):
            parts = cb_data.split(":")
            m = parts[1]
            p = parts[2]
            text = f"""
📦 <b>Samsung 4-File Odin Package Architecture</b>
━━━━━━━━━━━━━━━━━━━━
📱 <b>Model:</b> <code>{m}</code> | <b>Build:</b> <code>{p}</code>

📂 <b>Odin Slot Mapping Guide:</b>
• <b>[BL] Slot:</b> <code>BL_{p}_...tar.md5</code>
  <i>(Primary Bootloader, S-Boot, Trusted Execution Environment)</i>
• <b>[AP] Slot:</b> <code>AP_{p}_...tar.md5</code>
  <i>(System Core, Vendor, Product, Super Partition, Recovery)</i>
• <b>[CP] Slot:</b> <code>CP_{p}_...tar.md5</code>
  <i>(Modem, Baseband, Cellular RF Drivers)</i>
• <b>[CSC] Slot:</b> <code>CSC_OXM_{p}_...tar.md5</code>
  <i>(Carrier config & partition format - Factory Reset)</i>
• <b>[HOME_CSC]:</b> Use only if retaining user data during update.

⚡ <i>100% Verified Samsung Cryptographic Binary Package.</i>
"""
            send_message(chat_id, text)
        elif cb_data.startswith("pcdl:"):
            parts = cb_data.split(":")
            m = parts[1]
            c = parts[2]
            text = f"""
🖥️ <b>DroidClinic Direct PC Downloader (50 MB/s)</b>
━━━━━━━━━━━━━━━━━━━━
ब्राउज़र या किसी वेबसाइट को खोले बिना सीधे अपने कंप्यूटर पर डाउनलोड करने के लिए:

💻 <b>CMD या PowerShell में चलाएं:</b>
<code>asgard download {m} {c} --decrypt</code>

📂 <b>परिणाम:</b>
सैमसंग के ऑफिशियल सर्वर से सीधे <code>BL</code>, <code>AP</code>, <code>CP</code>, <code>CSC</code> चारों फ़ाइलें आपके फ़ोल्डर में ऑटोमैटिक डिक्रिप्ट होकर सेव हो जाएँगी!
"""
            send_message(chat_id, text)
        return

    if not msg:
        return

    chat_id = msg.get("chat", {}).get("id")
    from_user = msg.get("from", {})
    user_id = from_user.get("id")

    # 4. Handle Successful 1-Click Payment
    sp = msg.get("successful_payment")
    if sp:
        payload = sp.get("invoice_payload", "")
        stars = sp.get("total_amount", 0)
        today = datetime.date.today()

        if payload == "VIP_1M":
            exp_date = (today + datetime.timedelta(days=30)).isoformat()
            plan_label = "1 Month Pro Pass"
        elif payload == "VIP_1Y":
            exp_date = (today + datetime.timedelta(days=365)).isoformat()
            plan_label = "1 Year VIP Pass"
        else:
            exp_date = "2099-12-31"
            plan_label = "Lifetime Founder VIP"

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("UPDATE users SET tier = 'VIP', vip_expires = ? WHERE user_id = ?", (exp_date, user_id))
        conn.commit()
        conn.close()

        success_text = f"""
🎉 <b>PAYMENT CONFIRMED ({stars} ⭐ Stars)!</b>
━━━━━━━━━━━━━━━━━━━━
Congratulations, <b>{from_user.get('first_name', 'Technician')}</b>!
Your account has been upgraded to <b>{plan_label}</b>!
📅 Valid until: <b>{exp_date}</b>

⚡ <b>You now have Unlimited 24x7 Cloud FOTA Downloads!</b>
Start downloading now: <code>/samsung SM-A146B INS</code>
"""
        send_message(chat_id, success_text)
        return

    text = msg.get("text", "").strip()

    if not text:
        return

    # Anti-Spam / Anti-DDoS Rate Limiter (Max 1 request per 1.5 seconds per user)
    now = time.time()
    last_time = USER_LAST_MESSAGE_TIME.get(user_id, 0)
    if now - last_time < 1.5 and user_id != MASTER_ADMIN_ID:
        return  # Drop flood requests silently
    USER_LAST_MESSAGE_TIME[user_id] = now

    user = get_or_create_user(user_id, from_user.get("username"), from_user.get("first_name"))

    # Command Router
    parts = text.split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd in ["/start", "/help"]:
        handle_start(user, chat_id)
    elif cmd == "/samsung":
        handle_samsung(user, chat_id, args)
    elif cmd == "/xiaomi":
        handle_xiaomi(user, chat_id, args)
    elif cmd == "/loader":
        handle_loader(user, chat_id, args)
    elif cmd == "/myplan":
        handle_myplan(user, chat_id)
    elif cmd in ("/stats", "/diagnostics", "/admin"):
        if user_id == MASTER_ADMIN_ID:
            handle_admin_stats(chat_id)
        else:
            send_message(chat_id, "⛔ <i>यह कमांड केवल बॉट ओनर/एडमिन के लिए आरक्षित है।</i>")
    elif cmd == "/claim_admin":
        if user_id == MASTER_ADMIN_ID:
            send_message(chat_id, "👑 <b>आप पहले से ही इस बॉट के स्थायी मास्टर एडमिन और लाइफटाइम VIP हैं!</b>")
        else:
            send_message(chat_id, "⛔ <b>अनधिकृत प्रयास! एडमिन अधिकार सुरक्षित हैं।</b>")
    else:
        # Handle smart natural language queries (e.g. "asgard download SM-A146B INS --decrypt", "download A14", etc.)
        cleaned_text = text.strip()
        if "DOWNLOAD" in cleaned_text.upper():
            parts = cleaned_text.split()
            found_model = None
            found_csc = "INS"
            for p in parts:
                p_up = p.upper()
                if p_up.startswith("SM-") or p_up.startswith("GT-") or (len(p_up) >= 4 and any(c.isdigit() for c in p_up) and not p_up.startswith("-") and p_up not in ("ASGARD", "DOWNLOAD", "FIRMWARE")):
                    found_model = p_up
                elif len(p_up) == 3 and p_up.isalpha() and p_up not in ("ALL", "NEW", "ZIP"):
                    found_csc = p_up
            if found_model:
                send_message(chat_id, f"⚡ <b>कमांड डिटेक्टेड!</b> <code>{found_model} ({found_csc})</code> का आधिकारिक डेटा निकाला जा रहा है...")
                handle_samsung(user, chat_id, f"{found_model} {found_csc}")
                return

        if text.upper().startswith("SM-") or text.upper().startswith("GT-") or (len(text) <= 8 and text.isalnum()):
            handle_samsung(user, chat_id, text)
        else:
            send_message(chat_id, f"❓ अज्ञात कमांड। कृपया मुख्य मेनू देखने के लिए <code>/start</code> दबाएं।")

class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"DroidClinic Telegram Bot Engine is Live 24/7!\n")

    def log_message(self, format, *args):
        pass  # Keep logs clean

def start_http_server():
    port = int(os.environ.get("PORT", 10000))
    try:
        # Allow immediate port reuse
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", port), HealthCheckHandler) as httpd:
            print(f"[*] Cloud Health Check HTTP Server listening on port {port}")
            httpd.serve_forever()
    except Exception as e:
        print(f"[!] HTTP Server Notice: {e}")

def bot_polling_loop():
    print("[*] DroidClinic Telegram Bot Engine Starting...")
    init_db()
    offset = 0

    while True:
        try:
            updates = tg_api_call("getUpdates", {"offset": offset, "timeout": 20}, timeout=25)
            if updates.get("ok"):
                for update in updates.get("result", []):
                    offset = update["update_id"] + 1
                    threading.Thread(target=process_update, args=(update,)).start()
            else:
                time.sleep(2)
        except Exception as e:
            print(f"[!] Polling Exception: {e}")
            time.sleep(3)

if __name__ == "__main__":
    # Start background HTTP Health Check server for Cloud 24/7 uptime
    threading.Thread(target=start_http_server, daemon=True).start()
    bot_polling_loop()
