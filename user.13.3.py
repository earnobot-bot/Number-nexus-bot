import os
import threading
from flask import Flask

# --- RENDER ER JONNO FLASK SERVER SETUP ---
app = Flask(__name__)

@app.route('/')
def home():
    return "User Bot is successfully running on Render!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import requests
import json
import time
import uuid
import re
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- EMOJI FILE THEKE DB IMPORT KORA HOYECHE ---
from emoji import DEFAULT_CUSTOM_EMOJIS, PREMIUM_FLAGS

# --- CONFIGURATION (USER BOT TOKEN) ---
TOKEN = "8670504840:AAFMvnloNANEjiZJi5URWGPriR0R5pBy21k"  
ADMIN_ID = 6703675335

# ============================================================
# ✅ ZENEX NETWORK - OFFICIAL UPDATE (June 2026)
# ============================================================
BASE_URL = "https://api.zenexnetwork.com/v1"
NEXA_API_KEY = "ZNX_PF6LLINA9Z2UCPNGQB50C26C"  
BOT_NAME = "FreeGet Number"

http_session = requests.Session()

# Voltx SSL warning suppress (logs clean রাখতে)
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass

active_sessions = {}
active_sessions_lock = threading.RLock()

try:
    from telebot.types import CopyTextButton
    HAS_COPY_BTN = True
except ImportError:
    HAS_COPY_BTN = False

# ========================================================
# --- STYLE & CUSTOM EMOJI MAPS WITHOUT COLLISION BAGS ---
# ========================================================
_old_inline_dict = InlineKeyboardButton.to_dict
def _new_inline_dict(self):
    d = _old_inline_dict(self)
    style = getattr(self, 'style', None)
    if style:
        d['style'] = style
    emoji_id = getattr(self, 'icon_custom_emoji_id', None)
    if emoji_id:
        val = str(emoji_id).strip()
        if val:
            d['icon_custom_emoji_id'] = val
    return d
InlineKeyboardButton.to_dict = _new_inline_dict

_old_kb_dict = KeyboardButton.to_dict
def _new_kb_dict(self):
    d = _old_kb_dict(self)
    style = getattr(self, 'style', None)
    if style:
        d['style'] = style
    emoji_id = getattr(self, 'icon_custom_emoji_id', None)
    if emoji_id:
        val = str(emoji_id).strip()
        if val:
            d['icon_custom_emoji_id'] = val
    return d
KeyboardButton.to_dict = _new_kb_dict

def escape_html(text):
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def ibtn(text, callback_data=None, url=None, style=None, copy_text_str=None, custom_emoji_id=None, switch_inline_query=None, switch_inline_query_current_chat=None):
    kwargs = {'text': text}
    if callback_data: kwargs['callback_data'] = callback_data
    if url: kwargs['url'] = url
    if switch_inline_query is not None:
        kwargs['switch_inline_query'] = switch_inline_query
    if switch_inline_query_current_chat is not None:
        kwargs['switch_inline_query_current_chat'] = switch_inline_query_current_chat
    
    if copy_text_str:
        if HAS_COPY_BTN:
            try:
                kwargs['copy_text'] = CopyTextButton(text=str(copy_text_str))
            except Exception:
                kwargs['callback_data'] = f"cp_{copy_text_str}"
        else:
            kwargs['callback_data'] = f"cp_{copy_text_str}"
            
    try:
        b = InlineKeyboardButton(**kwargs)
    except TypeError:
        if 'copy_text' in kwargs:
            del kwargs['copy_text']
            kwargs['callback_data'] = f"cp_{copy_text_str}"
        b = InlineKeyboardButton(**kwargs)
        
    if style:
        try: b.style = style
        except AttributeError: pass
        
    emoji_val = str(custom_emoji_id).strip() if custom_emoji_id else None
    if emoji_val and emoji_val.isdigit() and len(emoji_val) >= 10:
        try: b.icon_custom_emoji_id = emoji_val
        except AttributeError: pass
        
    return b

def rbtn(text, style=None, custom_emoji_id=None):
    b = KeyboardButton(text=text)
    if style:
        try: b.style = style
        except AttributeError: pass
    emoji_val = str(custom_emoji_id).strip() if custom_emoji_id else None
    if emoji_val and emoji_val.isdigit() and len(emoji_val) >= 10:
        try: b.icon_custom_emoji_id = emoji_val
        except AttributeError: pass
    return b

bot = telebot.TeleBot(TOKEN, num_threads=35)
BOT_USERNAME_CACHE = None

def get_bot_username():
    global BOT_USERNAME_CACHE
    if not BOT_USERNAME_CACHE:
        try:
            BOT_USERNAME_CACHE = bot.get_me().username
        except:
            BOT_USERNAME_CACHE = "NM_Super_boT"
    return BOT_USERNAME_CACHE

def normalize_number(num):
    return re.sub(r'\D', '', str(num))

DATA_FILE = "Data_File.json"
db_lock = threading.RLock()
active_polls = {}

broadcast_cooldown = {}

def repair_mojibake(val):
    if isinstance(val, str):
        if any(c in val for c in "âãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ"):
            try:
                return val.encode('latin-1').decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass
        return val
    elif isinstance(val, dict):
        return {k: repair_mojibake(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [repair_mojibake(v) for v in val]
    return val

def load_data():
    global db_lock
    with db_lock:
        default_data = {
            "users": [], 
            "banned_users": [], 
            "services_data": {}, 
            "forward_groups": [], 
            "balances": {}, 
            "wallets": {}, 
            "referred_by": {}, 
            "referrals": {},
            "pending_withdrawals": {}, 
            "admins": [5009726439, 6703675335], 
            "maintenance_mode": False,
            "maintenance_message": "<b>⚠️ System under maintenance. Please try again later.</b>",
            "texts": {
                "welcome": '<b>𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐓𝐎</b>\n<b>FreeGet Number BOT</b>\n<b>Super instant otp</b>',
                "support": '<tg-emoji emoji-id="5337302974806922068">💬</tg-emoji> Support\n\n<tg-emoji emoji-id="5355208818017999139">📱</tg-emoji> Click the button below to contact support.',
                "support_link": "https://t.me/c/6703675335",
                "otp_group_link": "https://t.me/+7JTfYe5oQAM4ODNl",
                "main_channel_link": "https://t.me/+7JTfYe5oQAM4ODNl",
                "renge_group_link": "https://t.me/+7JTfYe5oQAM4ODNl",
                "btn_get_number": "GET NUMBER",
                "btn_balance": "BALANCE",
                "btn_refer": "REFER AND EARN",
                "btn_support": "SUPPORT",
                "btn_renge_group": "Renge Group",
                "cooldown_message": "<b>⏳ Cooldown Active!</b>\n\n🕒 You can change again in <b>{time_left}s</b>.\n📌 Total Cooldown: <b>{cooldown}s</b>\n\nPress the button again when the time is up."
            },
            "custom_emojis": DEFAULT_CUSTOM_EMOJIS,
            "custom_rates": {},
            "agents": {},
            "api_key": NEXA_API_KEY, 
            "base_url": "https://api.zenexnetwork.com/v1",
            "credited_numbers": [],
            "leaderboard": {
                "last_reset": 0.0,
                "stats": {}
            },
            "last_number_fetch": {},
            "settings": {
                "otp_bonus": 0.0031, 
                "ref_bonus": 0.001, 
                "max_numbers": 2, 
                "min_withdraw": 0.3,
                "leaderboard_reset_days": 3,
                "force_join_channels": [],
                "admin_alerts": True,
                "only_member_join_alert": True,
                "number_cooldown_seconds": 60
            },
            "panels": {
                "zenex": {
                    "name": "Zenex Network",
                    "base_url": "https://api.zenexnetwork.com/v1",
                    "api_key": "ZNX_PF6LLINA9Z2UCPNGQB50C26C",
                    "active": False,
                    "priority": 2,
                    "type": "zenex"
                },
                "voltx": {
                    "name": "Voltx SMS",
                    "base_url": "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api", # URL FIXED HERE
                    "api_key": "MQ6WJ56ED4U",
                    "active": True,
                    "priority": 1,
                    "type": "voltx"
                }
            },
            "default_panel": "voltx"
        }
        
        default_data = repair_mojibake(default_data)
        
        def sanitize(loaded, defaults):
            if not isinstance(loaded, dict):
                return defaults.copy()
            for key, default_val in defaults.items():
                if key not in loaded:
                    loaded[key] = default_val
                else:
                    if isinstance(default_val, dict):
                        loaded[key] = sanitize(loaded[key], default_val)
                    elif isinstance(default_val, list):
                        if not isinstance(loaded[key], list):
                            loaded[key] = default_val.copy()
                    elif isinstance(default_val, float):
                        try: loaded[key] = float(loaded[key])
                        except: loaded[key] = default_val
                    elif isinstance(default_val, int):
                        try: loaded[key] = int(loaded[key])
                        except: loaded[key] = default_val
                    elif isinstance(default_val, str):
                        loaded[key] = str(loaded[key])
            return loaded

        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w", encoding='utf-8') as f: 
                json.dump(default_data, f, indent=4)
            return default_data
            
        try:
            with open(DATA_FILE, "r", encoding='utf-8') as f:
                raw = f.read().strip()
                if not raw:
                    loaded_data = default_data
                else:
                    loaded_data = json.loads(raw)
        except Exception:
            loaded_data = default_data

        loaded_data = sanitize(loaded_data, default_data)
        loaded_data = repair_mojibake(loaded_data)
        
        if loaded_data.get("api_key") != NEXA_API_KEY:
            loaded_data["api_key"] = NEXA_API_KEY
            try:
                with open(DATA_FILE, "w", encoding='utf-8') as f:
                    json.dump(loaded_data, f, indent=4)
            except:
                pass

        # FIX: Ensure existing Voltx URL is overridden if it has the wrong HXS ID
        try:
            if loaded_data.get("panels", {}).get("voltx", {}).get("base_url") == "https://api.2oo9.cloud/HXS47FLFX8U/tnevs/@public/api":
                loaded_data["panels"]["voltx"]["base_url"] = "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api"
                with open(DATA_FILE, "w", encoding='utf-8') as f:
                    json.dump(loaded_data, f, indent=4)
        except: pass

        return loaded_data

def save_data(data):
    global db_lock
    with db_lock:
        try:
            with open(DATA_FILE, "w", encoding='utf-8') as f: 
                json.dump(data, f, indent=4)
        except: 
            pass

# ==================== NEW PANEL LOGIC (FIX) ====================
def get_current_panel_config():
    """Returns the active panel's config. Supports Zenex/Voltx switching from admin panel.
    Only one panel is active at a time."""
    data = load_data()
    panels = data.get("panels", {})
    default_panel = data.get("default_panel")
    if default_panel and default_panel in panels:
        p = panels[default_panel]
        if isinstance(p, dict) and p.get("active", False):
            return p.copy()
    active_panels = [(pid, p) for pid, p in panels.items() if isinstance(p, dict) and p.get("active", False)]
    if active_panels:
        active_panels.sort(key=lambda x: x[1].get("priority", 99))
        return active_panels[0][1].copy()
    return {
        "base_url": data.get("base_url", BASE_URL),
        "api_key": data.get("api_key", NEXA_API_KEY),
        "type": "zenex"
    }

def get_base_url():
    """Returns current active panel BASE_URL"""
    panel = get_current_panel_config()
    return str(panel.get("base_url", BASE_URL)).rstrip("/")

def get_api_key():
    """Returns current active panel API key"""
    panel = get_current_panel_config()
    return panel.get("api_key", NEXA_API_KEY)

def get_api_headers():
    """Returns correct auth headers based on current panel type.
    Voltx uses 'mauthapi', Zenex and others use 'mapikey'.
    """
    panel = get_current_panel_config()
    ptype = str(panel.get("type", "zenex")).lower().strip()
    api_key = get_api_key()
    if ptype == "voltx":
        return {'mauthapi': api_key, 'Content-Type': 'application/json'}
    else:
        return {'mapikey': api_key, 'Content-Type': 'application/json'}
# ============================================================

def is_admin(user_id):
    data = load_data()
    admins = data.setdefault("admins", [ADMIN_ID])
    return int(user_id) in [int(a) for a in admins] or int(user_id) == ADMIN_ID

def is_banned(chat_id):
    data = load_data()
    return str(chat_id) in data.get("banned_users", [])

def get_country_flag(country_name):
    cn_lower = str(country_name).lower().strip()
    fallback = "🌍"
    if cn_lower in PREMIUM_FLAGS:
        eid = PREMIUM_FLAGS[cn_lower]
        return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'
    for k, v in PREMIUM_FLAGS.items():
        if k in cn_lower:
            return f'<tg-emoji emoji-id="{v}">{fallback}</tg-emoji>'
    return get_emoji_tag("emj_country", fallback)

def detect_country_by_prefix(range_val):
    prefix = normalize_number(range_val)
    if prefix.startswith("223"): return "Mali", get_country_flag("Mali")
    if prefix.startswith("225"): return "Ivory Coast", get_country_flag("Ivory Coast")
    if prefix.startswith("228"): return "Togo", get_country_flag("Togo")
    if prefix.startswith("880") or prefix.startswith("88"): return "Bangladesh", get_country_flag("Bangladesh")
    if prefix.startswith("91"): return "India", get_country_flag("India")
    if prefix.startswith("92"): return "Pakistan", get_country_flag("Pakistan")
    if prefix.startswith("7"): return "Russia", get_country_flag("Russia")
    if prefix.startswith("380") or prefix.startswith("38"): return "Ukraine", get_country_flag("Ukraine")
    if prefix.startswith("48"): return "Poland", get_country_flag("Poland")
    if prefix.startswith("1"): return "United States", get_country_flag("United States")
    if prefix.startswith("44"): return "United Kingdom", get_country_flag("United Kingdom")
    if prefix.startswith("998"): return "Uzbekistan", get_country_flag("Uzbekistan")
    if prefix.startswith("90"): return "Turkey", get_country_flag("Turkey")
    if prefix.startswith("375") or prefix.startswith("37"): return "Belarus", get_country_flag("Belarus")
    if prefix.startswith("55"): return "Brazil", get_country_flag("Brazil")
    if prefix.startswith("84"): return "Vietnam", get_country_flag("Vietnam")
    if prefix.startswith("62"): return "Indonesia", get_emoji_tag("emj_changing")
    if prefix.startswith("63"): return "Philippines", get_country_flag("Philippines")
    return "Custom Number", get_emoji_tag("emj_changing")

def get_country_short_code(country_name):
    cn = str(country_name).lower().strip()
    mapping = {
        "mali": "ML", "myanmar": "MM", "uzbekistan": "UZ", "lebanon": "LB", "bangladesh": "BD", 
        "india": "IN", "pakistan": "PK", "russia": "RU", "indonesia": "ID",
        "ukraine": "UA", "egypt": "EG", "vietnam": "VN", "turkey": "TR",
        "ivory coast": "CI", "usa": "US", "uk": "GB", "philippines": "PH", "liberia": "LR",
        "custom number": "CUSTOM", "peru": "PE"
    }
    for k, v in mapping.items():
        if k in cn: return v
    return cn[:2].upper()

def get_emoji_tag(key, fallback=None):
    placeholders = {
        "emj_support": "💬", "emj_number": "📱", "emj_wallet": "💳", "emj_profile": "👤",       
        "emj_refer": "👥", "emj_bkash": "🏦", "emj_rocket": "🚀", "emj_binance": "🪙",       
        "emj_country": "🌍", "emj_instagram": "📸", "emj_facebook": "f", "emj_tiktok": "🎬",        
        "emj_whatsapp": "📞", "emj_telegram": "💬", "emj_admin_panel": "⚙️", "emj_ban": "🚫",           
        "emj_broadcast": "📢", "emj_otp_coming": "⏳", "emj_otp_received": "💾", "emj_message": "✉️",             
        "emj_stop": "🛑", "emj_successful": "👑", "emj_changing": "⚙️", "emj_add": "➕",                 
        "emj_link": "🔗", "emj_nagad": "🏦", "emj_cross": "❌", "emj_gift": "🎁",          
        "emj_up": "🔺", "emj_support_btn": "💬", "emj_key": "🔑", "emj_done": "✅",                
        "emj_search": "🔍", "emj_share": "📢", "emj_otp_group": "👥", "emj_gen_number": "⏳",  
        "emj_copy_link": "🔗"    
    }
    if not fallback:
        fallback = placeholders.get(key, "⭐")
    
    fallback = str(fallback).replace("\ufe0f", "")
    if len(fallback) > 1 and not (len(fallback) == 2 and ord(fallback[0]) >= 0xd800):
        fallback = "⭐"
        
    data = load_data()
    emojis = data.setdefault("custom_emojis", {})
    emoji_id = emojis.get(key, "").strip()
    if emoji_id:
        return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'
    return fallback

def get_emoji_id(key):
    data = load_data()
    emojis = data.setdefault("custom_emojis", {})
    if key == "emj_instragram" or key == "instragram":
        key = "emj_instagram"
    val = emojis.get(key, "").strip()
    return val if val else None

def get_service_emoji(service_name):
    sn = str(service_name).lower()
    if 'facebook' in sn: return get_emoji_tag("emj_facebook")
    if 'tiktok' in sn: return get_emoji_tag("emj_tiktok")
    if 'telegram' in sn: return get_emoji_tag("emj_telegram")
    if 'whatsapp' in sn: return get_emoji_tag("emj_whatsapp")
    if 'instagram' in sn or 'instragram' in sn: return get_emoji_tag("emj_instagram")
    if 'custom number' in sn: return get_emoji_tag("emj_changing")
    return "" 

def mask_number(phone):
    phone_str = normalize_number(phone)
    if len(phone_str) > 8:
        return f"{phone_str[:4]}•••{phone_str[-4:]}"
    elif len(phone_str) > 6:
        return f"{phone_str[:3]}•••{phone_str[-3:]}"
    return f"{phone_str}"

def is_subscribed(user_id):
    if int(user_id) == ADMIN_ID or is_admin(user_id): return True
    data = load_data()
    channels = data.setdefault("settings", {}).setdefault("force_join_channels", [])
    if not channels: return True
    
    for ch in channels:
        try:
            ch_clean = str(ch).strip()
            if ch_clean.startswith("https://t.me/"):
                ch_clean = "@" + ch_clean.split("/")[-1].split("?")[0]
            elif ch_clean.startswith("t.me/"):
                ch_clean = "@" + ch_clean.split("/")[-1].split("?")[0]
            elif not ch_clean.startswith("@") and not ch_clean.startswith("-"):
                ch_clean = "@" + ch_clean
            member = bot.get_chat_member(ch_clean, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception:
            continue
    return True

def send_force_join(chat_id):
    data = load_data()
    channels = data["settings"].setdefault("force_join_channels", [])
    
    text = f'{get_emoji_tag("emj_stop")} <b>Please join our channels to use the bot!</b>'
    markup = InlineKeyboardMarkup()
    
    for idx, ch in enumerate(channels, 1):
        url = f"https://t.me/{ch.replace('@', '')}" if ch.startswith("@") else ch
        markup.add(ibtn(f"Join Channel {idx}", url=url, style="primary", custom_emoji_id=get_emoji_id("emj_link")))
        
    markup.add(ibtn("Check Joined", callback_data="chk_joined", style="success", custom_emoji_id=get_emoji_id("emj_successful")))
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

def is_menu_button(text):
    if not text:
        return False
    data = load_data()
    texts = data.setdefault("texts", {})
    menu_buttons = [
        texts.get("btn_get_number", "GET NUMBER"),
        "Custom Number",
        texts.get("btn_balance", "BALANCE"),
        texts.get("btn_refer", "REFER AND EARN"),
        "LEADERBOARD",
        texts.get("btn_support", "SUPPORT"),
        texts.get("btn_renge_group", "Renge Group")
    ]
    return text.strip() in menu_buttons

def extract_otp(sms_text):
    if not sms_text:
        return "Not Extracted"
    text = str(sms_text).strip()
    # Improved patterns for FB/IG/WA and other services (contextual match first)
    priority_patterns = [
        r'(?i)(?:your\s+)?(?:verification\s+)?(?:code|otp|pin|passcode)[\s:]*(\d{4,8})',
        r'(?i)(?:code|otp)[\s:]*(\d{4,8})',
        r'(\d{4,8})[\s]*(?:is your|your code|verification code|otp)',
        r'\b(\d{6})\b',
    ]
    for pat in priority_patterns:
        m = re.search(pat, text)
        if m:
            return m.group(1)
    # Original fallback logic
    match = re.search(r'\b\d{3}[-\s]\d{3}\b', text)
    if match:
        return match.group(0)
    match = re.search(r'\b\d{4,8}\b', text)
    if match:
        return match.group(0)
    return "Not Extracted"

def safe_get_chat_id(grp):
    """Improved to handle t.me links, usernames, and chat IDs.
    Note: For private invite links (t.me/+...), you must use actual chat_id (-100...) instead.
    """
    try:
        if grp is None:
            return None
        val = str(grp).strip()
        if not val:
            return None
        # Handle common t.me / telegram.me links
        lower_val = val.lower()
        if "t.me/" in lower_val or "telegram.me/" in lower_val:
            # Extract the path part
            for sep in ["t.me/", "telegram.me/"]:
                if sep in lower_val:
                    path = val.split(sep, 1)[1].split("?")[0].strip("/")
                    if path.startswith("joinchat/") or path.startswith("+"):
                        # Private invite hash - cannot resolve to chat_id here. Will likely fail send.
                        print(f"[safe_get_chat_id] Private invite link detected ({val}). Use real chat_id (e.g. -1001234567890) instead of invite link.")
                        return val
                    if path:
                        if not path.startswith("@"):
                            path = "@" + path
                        return path
        # Numeric chat IDs (supergroups/channels are usually negative like -100...)
        if val.startswith("-") and val[1:].replace("-", "").isdigit():
            return int(val)
        elif val.isdigit():
            return int(val)
        # Username with or without @
        if val.startswith("@"):
            return val
        if val and not val.startswith(("-", "http", "https")):
            return "@" + val
    except Exception as ex:
        print(f"[safe_get_chat_id EXC] {ex}")
        pass
    return grp

def credit_user_and_update_leaderboard(chat_id, target_num, otp_id):
    num_key = f"{chat_id}_{target_num}_{otp_id}"
    data = load_data()
    credited_list = data.setdefault("credited_numbers", [])
    if num_key in credited_list:
        return False
        
    credited_list.append(num_key)
    try:
        current_bal = data.get("balances", {}).get(str(chat_id), 0.0)
        
        custom_rates = data.setdefault("custom_rates", {})
        user_rate = custom_rates.get(str(chat_id))
        if user_rate is not None:
            try: bonus = float(user_rate)
            except: bonus = data.get("settings", {}).get("otp_bonus", 0.001)
        else:
            bonus = data.get("settings", {}).get("otp_bonus", 0.001)
            
        data.setdefault("balances", {})[str(chat_id)] = round(current_bal + bonus, 5)
        
        try:
            referred_by = data.get("referred_by", {}).get(str(chat_id))
            if referred_by:
                ref_str = str(referred_by)
                agents = data.get("agents", {})
                if ref_str in agents:
                    agent_bonus = float(agents[ref_str])
                    ref_bal = data.get("balances", {}).get(ref_str, 0.0)
                    data.setdefault("balances", {})[ref_str] = round(ref_bal + agent_bonus, 5)
        except:
            pass
        
        leaderboard = data.setdefault("leaderboard", {"last_reset": time.time(), "stats": {}})
        now = time.time()
        reset_days = data.get("settings", {}).get("leaderboard_reset_days", 3)
        try: last_reset_time = float(leaderboard.get("last_reset", 0.0))
        except:
            last_reset_time = now
            leaderboard["last_reset"] = now
            
        if now - last_reset_time >= (reset_days * 86400):
            notify_admin_leaderboard_winners_on_reset(leaderboard, data)
            
        stats = leaderboard.setdefault("stats", {})
        stats[str(chat_id)] = stats.get(str(chat_id), 0) + 1
        
        try:
            referred_by = data.get("referred_by", {}).get(str(chat_id))
            if referred_by:
                ref_str = str(referred_by)
                if ref_str in data.get("agents", {}):
                    stats[ref_str] = stats.get(ref_str, 0) + 1
        except:
            pass
            
        save_data(data)
        return True
    except Exception as e:
        pass
    return False

def notify_admin_leaderboard_winners_on_reset(leaderboard, data):
    try:
        stats = leaderboard.get("stats", {})
        if not stats:
            leaderboard["stats"] = {}
            leaderboard["last_reset"] = time.time()
            return

        sorted_stats = sorted(stats.items(), key=lambda item: item[1], reverse=True)[:3]
        if not sorted_stats:
            leaderboard["stats"] = {}
            leaderboard["last_reset"] = time.time()
            return

        def _get_user_name(uid):
            try:
                chat_info = bot.get_chat(int(uid))
                name = chat_info.first_name or chat_info.username or f"User ({str(uid)[-4:]})"
                return escape_html(name)
            except:
                return f"User ({str(uid)[-4:]})"

        names = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_uid = {executor.submit(_get_user_name, uid): uid for uid, _ in sorted_stats}
            for future in as_completed(future_to_uid):
                uid = future_to_uid[future]
                try:
                    names[uid] = future.result()
                except:
                    names[uid] = f"User ({str(uid)[-4:]})"

        msg = f"{get_emoji_tag('emj_successful')} <b>🏆 LEADERBOARD SEASON ENDED!</b>\n\n"
        msg += f"<b>Top 3 Winners (previous season):</b>\n\n"
        winners_list = []
        for idx, (uid, count) in enumerate(sorted_stats, 1):
            name = names.get(uid, f"User ({str(uid)[-4:]})")
            msg += f"<b>{idx}.</b> {name}\n"
            msg += f"    UID: <code>{uid}</code>  |  OTPs: <code>{count}</code>\n\n"
            winners_list.append({
                "rank": idx,
                "uid": str(uid),
                "name": name,
                "otps": count
            })
        msg += f"<i>Admin: Please send the specified bonus reward to these top 3 performers.</i>\n"

        leaderboard["last_season_winners"] = winners_list

        try:
            bot.send_message(ADMIN_ID, msg, parse_mode="HTML")
        except Exception as notify_err:
            print(f"[Leaderboard Reset Notify] Failed to send to ADMIN: {notify_err}")

    except Exception as e:
        print(f"[Leaderboard Reset Notify] Error: {e}")
        pass

    leaderboard["stats"] = {}
    leaderboard["last_reset"] = time.time()

def generate_otp_card_data(srv_name, cnt_name, phone_number, otp_code, is_group=False):
    premium_flag = get_country_flag(cnt_name)
    short_code = get_country_short_code(cnt_name)
    srv_emoji = get_service_emoji(srv_name)
    
    if is_group:
        num_display = mask_number(phone_number)
    else:
        num_display = normalize_number(phone_number)
        
    badge = srv_name[:3].upper().replace("FAC", "FB").replace("TEL", "TG").replace("WHA", "WA")
    
    text = (
        f"<b>{escape_html(srv_name)}</b>                  <code>{badge}</code>\n"
        f"{premium_flag} <b>{short_code}</b>  {srv_emoji}  <code>{num_display}</code>"
    )
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        ibtn(f"{otp_code}", copy_text_str=otp_code, style="success", custom_emoji_id=get_emoji_id("emj_key"))
    )
    
    if is_group:
        data = load_data()
        markup.add(
            ibtn("CHANNEL", url=data.get("texts", {}).get("main_channel_link", "https://t.me/+7JTfYe5oQAM4ODNl"), style="danger", custom_emoji_id=get_emoji_id("emj_link")),
            ibtn("NUMBER ", url=f"https://t.me/{get_bot_username()}", style="primary", custom_emoji_id=get_emoji_id("emj_number"))
        )
        
    return text, markup

# ============================================
# --- USER UI FUNCTIONS ---
# ============================================
def get_main_menu(chat_id):
    data = load_data()
    texts = data.setdefault("texts", {})
    btn_get_number = texts.get("btn_get_number", "GET NUMBER")
    btn_balance = texts.get("btn_balance", "BALANCE")
    btn_refer = texts.get("btn_refer", "REFER AND EARN")
    btn_support = texts.get("btn_support", "SUPPORT")
    btn_renge = texts.get("btn_renge_group", "Renge Group")

    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        rbtn(btn_get_number, "primary", custom_emoji_id=get_emoji_id("emj_number")),
        rbtn("Custom Number", "success", custom_emoji_id=get_emoji_id("emj_changing"))
    )
    markup.add(
        rbtn(btn_balance, "success", custom_emoji_id=get_emoji_id("emj_wallet")),
        rbtn(btn_refer, "success", custom_emoji_id=get_emoji_id("emj_refer"))
    )
    markup.add(
        rbtn("LEADERBOARD", "primary", custom_emoji_id=get_emoji_id("emj_profile")),
        rbtn(btn_support, "primary", custom_emoji_id=get_emoji_id("emj_support"))
    )
    markup.add(
        rbtn(btn_renge, "success", custom_emoji_id=get_emoji_id("emj_link"))
    )
    return markup

def show_services(chat_id, message_id=None):
    data = load_data()
    markup = InlineKeyboardMarkup(row_width=2)
    services = data.get("services_data", {})
    if not services:
        bot.send_message(chat_id, f'{get_emoji_tag("emj_cross")} No services available currently.', parse_mode="HTML")
        return
    
    for srv_id, srv in services.items():
        if not isinstance(srv, dict) or "name" not in srv: continue
        srv_name_lower = str(srv['name']).lower()
        emoji_id = None
        if 'facebook' in srv_name_lower: emoji_id = get_emoji_id("emj_facebook")
        elif 'tiktok' in srv_name_lower: emoji_id = get_emoji_id("emj_tiktok")
        elif 'telegram' in srv_name_lower: emoji_id = get_emoji_id("emj_telegram")
        elif 'whatsapp' in srv_name_lower: emoji_id = get_emoji_id("emj_whatsapp")
        elif 'instagram' in srv_name_lower or 'instragram' in srv_name_lower: emoji_id = get_emoji_id("emj_instagram")
        
        markup.add(ibtn(srv['name'], callback_data=f"usr_s|{srv_id}", style="primary", custom_emoji_id=emoji_id))
        
    text = f'{get_emoji_tag("emj_number")} <b>Select a Service:</b>'
    if message_id:
        try: bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, parse_mode="HTML", reply_markup=markup)
        except: pass
    else:
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

def show_countries(chat_id, srv_id, message_id=None):
    data = load_data()
    srv_data = data.get("services_data", {}).get(srv_id)
    if not srv_data:
        try:
            bot.send_message(chat_id, f'{get_emoji_tag("emj_cross")} <b>Service not available.</b> Please try again or contact support.', parse_mode="HTML")
        except:
            pass
        return
    
    markup = InlineKeyboardMarkup(row_width=2)
    for cnt_id, cnt in srv_data.get("countries", {}).items():
        if not isinstance(cnt, dict) or "name" not in cnt: continue
        cn_lower = str(cnt['name']).lower().strip()
        cnt_emoji_id = PREMIUM_FLAGS.get(cn_lower)
        if not cnt_emoji_id:
            for k, v in PREMIUM_FLAGS.items():
                if k in cn_lower:
                    cnt_emoji_id = v
                    break
        
        markup.add(ibtn(f"{cnt['name']}", callback_data=f"usr_c|{srv_id}|{cnt_id}", style="primary", custom_emoji_id=cnt_emoji_id))
        
    markup.add(ibtn("Back", callback_data="back_to_services", style="danger", custom_emoji_id=get_emoji_id("emj_cross")))
    
    text = f'<b>Selected country for {srv_data.get("name", "Service")}:</b>'
    
    if message_id: 
        try: bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, parse_mode="HTML", reply_markup=markup)
        except: pass
    else: 
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

def get_updated_number_markup(chat_id):
    with active_sessions_lock:
        session = active_sessions.get(str(chat_id))
        if not session: return None
        
        numbers = session["numbers"]
        srv_id = session["service_info"].get("srv_id", "custom")
        cnt_id = session["service_info"].get("cnt_id", "custom")
        custom_range = session["service_info"].get("custom_range")
        
        markup = InlineKeyboardMarkup(row_width=1)
        for num in numbers:
            otp_status = session["otp_received"]
            is_done = len(otp_status.get(num, [])) > 0 if isinstance(otp_status.get(num), list) else False
            emoji_id = "5936067938955039275" if is_done else get_emoji_id("emj_copy_link")
            markup.add(ibtn(f"- {num}", copy_text_str=num, custom_emoji_id=emoji_id))
            
        if srv_id and srv_id != "custom":
            markup.add(
                ibtn("Change Number", callback_data=f"chg_r|{srv_id}|{cnt_id if not custom_range else 'custom'}", style="danger", custom_emoji_id=get_emoji_id("emj_changing")),
                ibtn("Change Country", callback_data=f"usr_s|{srv_id}", style="success", custom_emoji_id=get_emoji_id("emj_country"))
            )
        else:
            markup.add(ibtn("Change Number", callback_data="chg_r|custom|custom", style="danger", custom_emoji_id=get_emoji_id("emj_changing")))
            
        data = load_data()
        markup.row(
            ibtn("Otp Group", url=data.get("texts", {}).get("otp_group_link", "https://t.me/+7JTfYe5oQAM4ODNl"), style="primary", custom_emoji_id=get_emoji_id("emj_otp_group")),
            ibtn("Main Channel", url=data.get("texts", {}).get("main_channel_link", "https://t.me/+7JTfYe5oQAM4ODNl"), style="primary", custom_emoji_id=get_emoji_id("emj_link"))
        )
        return markup

def fetch_single_number(api_key, clean_range):
    retries = 3
    
    panel_config = get_current_panel_config()
    ptype = str(panel_config.get("type", "zenex")).lower().strip()
    
    for attempt in range(retries):
        try:
            headers = get_api_headers()
            
            if ptype == "voltx":
                # === VOLTX CORRECT FORMAT (from official docs) ===
                # rid = range WITHOUT trailing XXX (e.g. 22581XXX → 22581)
                rid = re.sub(r'[^0-9]', '', str(clean_range).upper().replace('X', ''))
                # If user gave full like 22581XXX, rid becomes 22581
                payload = {"rid": rid}
                print(f"[VOLTX] Using rid={rid} (original: {clean_range})")
            else:
                # Zenex
                payload = {"range": clean_range, "is_national": True, "remove_plus": False}
            
            url = f"{get_base_url()}/getnum"
            
            print(f"[FETCH] Panel:{ptype} | URL:{url} | Payload:{payload}")
            
            # Voltx-এ SSL verify error এড়াতে (Render/local-এ common issue)
            if ptype == "voltx":
                res = http_session.post(url, json=payload, headers=headers, timeout=15, verify=False)
            else:
                res = http_session.post(url, json=payload, headers=headers, timeout=15)
            
            print(f"[FETCH] Status:{res.status_code} | Body:{res.text[:500]}")
            
            if res.status_code != 200:
                try: 
                    err_json = res.json()
                    err = err_json.get("message") or err_json.get("error") or f"HTTP {res.status_code}"
                except: 
                    err = f"HTTP {res.status_code} - {res.text[:300]}"
                print(f"[FETCH ERROR] {ptype} | {err}")
                if attempt == retries - 1:
                    return None, err
                time.sleep(1)
                continue
                
            res_json = res.json()
            data_part = res_json.get("data") or {}
            num = data_part.get("full_number") or data_part.get("number")
            if num: 
                print(f"[FETCH SUCCESS] {ptype} → {num}")
                return f"+{str(num).replace('+', '')}", None
            else:
                err = res_json.get("message") or res_json.get("error") or "No number returned"
                print(f"[FETCH] {ptype} no number: {res_json}")
                if attempt == retries - 1: return None, err
        except Exception as e:
            print(f"[FETCH EXC] {ptype}: {str(e)}")
            if attempt == retries - 1: return None, f"Error: {str(e)}"
            time.sleep(1)

def fetch_real_numbers(chat_id, srv_id, cnt_id, msg_id, custom_range=None, call_id=None):
    try:
        data = load_data()
        api_key = get_api_key()
        max_nums = data.get("settings", {}).get("max_numbers", 2) 
        
        if srv_id and srv_id != "custom":
            srv_data = data.get("services_data", {}).get(srv_id)
            if not srv_data: raise RuntimeError("srv_data missing for selected service")
            srv_name = srv_data.get('name', 'Service')
        else:
            srv_name = "Custom Number"

        if custom_range:
            ranges_list = [r.strip() for r in re.split(r'[,\s;]+', str(custom_range)) if r.strip()]
            if not ranges_list: raise RuntimeError("No valid custom ranges provided")
            display_name, premium_flag = detect_country_by_prefix(ranges_list[0])
        else:
            cnt_data = srv_data.get("countries", {}).get(cnt_id) if srv_data else None
            if not cnt_data or not cnt_data.get("range"): raise RuntimeError("No range configured for selected country")
            ranges_list = [r.strip() for r in re.split(r'[,\s;]+', str(cnt_data["range"])) if r.strip()]
            if not ranges_list: raise RuntimeError("No valid ranges after split for country")
            display_name = cnt_data.get('name', 'Country')
            premium_flag = get_country_flag(display_name)

        if msg_id:
            try: bot.edit_message_text(f'{get_emoji_tag("emj_gen_number")} <b>Generating numbers... Please wait.</b>', chat_id=chat_id, message_id=msg_id, parse_mode="HTML")
            except: pass
        else:
            try: msg_id = bot.send_message(chat_id, f'{get_emoji_tag("emj_gen_number")} <b>Generating...</b>', parse_mode="HTML").message_id
            except: raise RuntimeError("Failed to send Generating message")
        
        fetched_numbers = []
        last_error_msg = "All ranges are currently out of stock."
        
        with ThreadPoolExecutor(max_workers=max_nums) as executor:
            futures = []
            for i in range(max_nums):
                clean_range = ranges_list[i % len(ranges_list)]
                futures.append(executor.submit(fetch_single_number, api_key, clean_range))
                
            for future in as_completed(futures):
                try:
                    num, err = future.result()
                    if num and num not in fetched_numbers: fetched_numbers.append(num)
                    elif err: last_error_msg = err
                except Exception as ex:
                    last_error_msg = f"Thread failure: {str(ex)}"

        if not fetched_numbers:
            # Show exactly like Cooldown popup notice (show_alert style)
            # "🌀 Number Not Found" popup window - no long error card
            popup_text = "🌀 Number Not Found"
            if call_id:
                try:
                    bot.answer_callback_query(call_id, popup_text, show_alert=True)
                except: pass
            else:
                # Fallback for text path (Custom Number)
                try:
                    bot.send_message(chat_id, f'{get_emoji_tag("emj_changing")} <b>{popup_text}</b>\nPlease try again in a few minutes.', parse_mode="HTML")
                except: pass
            
            # Clean up Generating message
            try:
                bot.delete_message(chat_id, msg_id)
            except: pass
            
            # Notify admin (technical only)
            panel_config = get_current_panel_config()
            ptype = str(panel_config.get("type", "zenex")).lower().strip()
            try:
                safe_err = str(last_error_msg)[:200] if last_error_msg else "Unknown"
                bot.send_message(ADMIN_ID, f"⚠️ Fetch failed\nUser: <code>{chat_id}</code>\nPanel: <b>{ptype}</b>\nError: <code>{safe_err}</code>", parse_mode="HTML")
            except: pass
            return

        try:
            d = load_data()
            d.setdefault("last_number_fetch", {})[str(chat_id)] = time.time()
            save_data(d)
        except: pass

        text = (
            f"{premium_flag} <b>{escape_html(display_name)} Number selected</b>\n"
            f"{get_emoji_tag('emj_otp_coming')} <b>Waiting for OTP...</b>"
        )
        
        service_info = {"srv_name": srv_name, "cnt_name": display_name, "srv_id": srv_id if srv_id else "custom", "cnt_id": cnt_id if not custom_range else "custom", "custom_range": custom_range}
        
        with active_sessions_lock:
            active_sessions[str(chat_id)] = {
                "msg_id": msg_id,
                "numbers": fetched_numbers,
                "otp_received": {num: [] for num in fetched_numbers},
                "service_info": service_info,
                "start_time": time.time()
            }
            
        markup = get_updated_number_markup(chat_id)

        # Always delete the "Generating..." message first (more reliable)
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass

        # Always send a fresh new message with the numbers (avoids edit failures)
        try:
            new_msg = bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
            # Update the session with the new message ID for future OTP updates
            with active_sessions_lock:
                if str(chat_id) in active_sessions:
                    active_sessions[str(chat_id)]["msg_id"] = new_msg.message_id
        except Exception as send_err:
            print(f"[Number Display Error] chat_id={chat_id} err={send_err}")
            try:
                bot.send_message(chat_id, f'{get_emoji_tag("emj_cross")} <b>Could not display numbers. Please try again.</b>', parse_mode="HTML")
            except:
                pass

        active_polls[str(chat_id)] = True
    except Exception as general_err:
        print(f"[fetch_real_numbers ERROR] chat_id={chat_id} err={general_err}")
        try:
            if msg_id:
                bot.delete_message(chat_id, msg_id)
        except:
            pass
        try:
            bot.send_message(chat_id, f'{get_emoji_tag("emj_cross")} <b>Error while generating numbers.</b> Please try again or contact support.', parse_mode="HTML")
        except:
            pass
        if call_id:
            try:
                bot.answer_callback_query(call_id, "Error generating numbers. Please try again.", show_alert=True)
            except:
                pass
        try:
            bot.send_message(ADMIN_ID, f"⚠️ <b>Number generation failed</b>\nUser: <code>{chat_id}</code>\nError: <code>{str(general_err)[:300]}</code>", parse_mode="HTML")
        except:
            pass

def manual_check_otps(chat_id, call_id=None):
    headers = get_api_headers()
    panel_config = get_current_panel_config()
    ptype = str(panel_config.get("type", "zenex")).lower().strip()
    
    with active_sessions_lock:
        sess = active_sessions.get(str(chat_id))
        if not sess:
            if call_id:
                try: bot.answer_callback_query(call_id, "❌ No active session found.", show_alert=True)
                except: pass
            return
        msg_id, service_info, numbers, otp_status = sess["msg_id"], sess["service_info"], sess["numbers"], sess["otp_received"]
        
    try:
        # FIX: Dynamic endpoint based on panel
        endpoint = f"{get_base_url()}/success-otp" if ptype == "voltx" else f"{get_base_url()}/numsuccess/info"
        res = http_session.get(endpoint, headers=headers, timeout=15, verify=False if ptype == 'voltx' else True).json()
        # Robust otps_list extraction (supports different panel response structures)
        data_part = res.get("data") if isinstance(res.get("data"), dict) else res
        otps_list = []
        if isinstance(data_part, dict):
            otps_list = data_part.get("otps") or data_part.get("messages") or data_part.get("data") or []
        if not isinstance(otps_list, list):
            otps_list = []
        new_otp_found = False
        
        if otps_list:
            with active_sessions_lock:
                sess = active_sessions.get(str(chat_id))
                if not sess: return
                
                data = load_data() # For forward groups
                
                for otp_entry in otps_list:
                    if not isinstance(otp_entry, dict):
                        continue
                    # Support multiple possible field names for phone number (FB/IG/Voltx/Zenex variants)
                    entry_num_raw = ""
                    for f in ["number", "phone", "phone_number", "msisdn", "full_number", "num", "destination"]:
                        if otp_entry.get(f):
                            entry_num_raw = otp_entry.get(f)
                            break
                    entry_num = normalize_number(entry_num_raw)
                    for num in numbers:
                        target_num = normalize_number(num)
                        if entry_num == target_num:
                            # Support multiple id fields
                            otp_id = ""
                            for f in ["nid", "otp_id", "id", "sms_id", "message_id", "uid"]:
                                val = otp_entry.get(f)
                                if val:
                                    otp_id = str(val)
                                    break
                            if not otp_id:
                                otp_id = f"{target_num}_{otp_entry.get('otp', otp_entry.get('message', ''))}"
                            if not isinstance(otp_status.get(num), list): otp_status[num] = []
                            
                            # FIX: Support both Zenex ("otp") and Voltx ("message") + extra fields for FB/IG
                            raw_sms = ""
                            for f in ["otp", "message", "sms", "text", "body", "content", "msg", "verification"]:
                                if otp_entry.get(f):
                                    raw_sms = str(otp_entry.get(f))
                                    break
                            otp_code = extract_otp(raw_sms)
                            
                            if otp_code == "Not Extracted": otp_code = "See Full SMS Below"
                                
                            otp_key = f"{otp_id}_{otp_code}"
                            if otp_key not in otp_status[num]:
                                credit_user_and_update_leaderboard(chat_id, target_num, otp_id)
                                otp_status[num].append(otp_key)
                                new_otp_found = True
                                
                                updated_markup = get_updated_number_markup(chat_id)
                                if updated_markup:
                                    try: bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=updated_markup)
                                    except: pass
                                    
                                otp_count = len(otp_status[num])
                                srv_display_name = service_info['srv_name']
                                if otp_count > 1:
                                    suffix = "nd" if otp_count == 2 else "rd" if otp_count == 3 else "th"
                                    srv_display_name = f"{srv_display_name} ({otp_count}{suffix} OTP)"
                                    
                                user_text, user_markup = generate_otp_card_data(srv_display_name, service_info['cnt_name'], num, otp_code, is_group=False)
                                group_text, group_markup = generate_otp_card_data(srv_display_name, service_info['cnt_name'], num, otp_code, is_group=True)
                                
                                try: bot.send_message(chat_id, user_text, parse_mode="HTML", reply_markup=user_markup)
                                except: pass
                                
                                forward_groups = data.get("forward_groups", [])
                                if forward_groups:
                                    print(f"[GROUP FORWARD - manual] User {chat_id} got new OTP. Forwarding to groups: {forward_groups}")
                                for grp in forward_groups:
                                    target = safe_get_chat_id(grp)
                                    print(f"[GROUP FORWARD - manual] -> Sending to target={target} (original: {grp})")
                                    try:
                                        bot.send_message(target, group_text, parse_mode="HTML", reply_markup=group_markup)
                                        print(f"[GROUP FORWARD - manual] ✅ SUCCESS posted to {grp}")
                                    except Exception as e:
                                        err_str = str(e)[:300]
                                        print(f"[OTP Group Forward Error - manual] ❌ FAILED Group: {grp} | target={target} | Error: {err_str}")
                                        try:
                                            bot.send_message(ADMIN_ID, f"⚠️ <b>OTP Group Forward Failed</b>\nGroup: <code>{grp}</code>\nTarget: <code>{target}</code>\nError: <code>{err_str}</code>\n\n<b>Common fixes:</b>\n• Make sure bot is <b>ADMIN</b> in the group/channel\n• For channels: enable 'Post Messages' permission\n• Use real chat_id (e.g. -1001234567890) not invite link\n• Check Data_File.json forward_groups list", parse_mode="HTML")
                                        except: pass
        if call_id:
            if new_otp_found:
                try: bot.answer_callback_query(call_id, "✅ New OTP received successfully!", show_alert=True)
                except: pass
            else:
                try: bot.answer_callback_query(call_id, "⏳ No new OTP yet.", show_alert=True)
                except: pass
    except: pass

def global_otp_polling_loop():
    while True:
        try:
            data = load_data()
            headers = get_api_headers()
            panel_config = get_current_panel_config()
            ptype = str(panel_config.get("type", "zenex")).lower().strip()
            
            has_active = False
            with active_sessions_lock:
                now = time.time()
                to_remove = []
                for cid, sess in list(active_sessions.items()):
                    if now - sess.get("start_time", now) > 1200:
                        to_remove.append(cid)
                    else:
                        has_active = True
                for cid in to_remove:
                    if cid in active_sessions: del active_sessions[cid]
                    active_polls.pop(str(cid), None)
            
            if has_active:
                # FIX: Dynamic endpoint based on panel
                endpoint = f"{get_base_url()}/success-otp" if ptype == "voltx" else f"{get_base_url()}/numsuccess/info"
                res = http_session.get(endpoint, headers=headers, timeout=8, verify=False if ptype == 'voltx' else True).json()
                # Robust otps_list extraction (supports different panel response structures for FB/IG etc)
                data_part = res.get("data") if isinstance(res.get("data"), dict) else res
                otps_list = []
                if isinstance(data_part, dict):
                    otps_list = data_part.get("otps") or data_part.get("messages") or data_part.get("data") or []
                if not isinstance(otps_list, list):
                    otps_list = []
                
                if otps_list:
                    with active_sessions_lock:
                        for cid, sess in list(active_sessions.items()):
                            msg_id, service_info, numbers, otp_status = sess["msg_id"], sess["service_info"], sess["numbers"], sess["otp_received"]
                            
                            for otp_entry in otps_list:
                                if not isinstance(otp_entry, dict):
                                    continue
                                # Support multiple possible field names for phone number (FB/IG/Voltx/Zenex variants)
                                entry_num_raw = ""
                                for f in ["number", "phone", "phone_number", "msisdn", "full_number", "num", "destination"]:
                                    if otp_entry.get(f):
                                        entry_num_raw = otp_entry.get(f)
                                        break
                                entry_num = normalize_number(entry_num_raw)
                                for num in numbers:
                                    target_num = normalize_number(num)
                                    if entry_num == target_num:
                                        # Support multiple id fields
                                        otp_id = ""
                                        for f in ["nid", "otp_id", "id", "sms_id", "message_id", "uid"]:
                                            val = otp_entry.get(f)
                                            if val:
                                                otp_id = str(val)
                                                break
                                        if not otp_id:
                                            otp_id = f"{target_num}_{otp_entry.get('otp', otp_entry.get('message', ''))}"
                                        if not isinstance(otp_status.get(num), list): otp_status[num] = []
                                            
                                        # FIX: Support both Zenex ("otp") and Voltx ("message") + extra fields for FB/IG
                                        raw_sms = ""
                                        for f in ["otp", "message", "sms", "text", "body", "content", "msg", "verification"]:
                                            if otp_entry.get(f):
                                                raw_sms = str(otp_entry.get(f))
                                                break
                                        otp_code = extract_otp(raw_sms)
                                        
                                        if otp_code == "Not Extracted": otp_code = "See Full SMS Below"
                                        
                                        otp_key = f"{otp_id}_{otp_code}"
                                        if otp_key not in otp_status[num]:
                                            credit_user_and_update_leaderboard(cid, target_num, otp_id)
                                            otp_status[num].append(otp_key)
                                            
                                            updated_markup = get_updated_number_markup(cid)
                                            if updated_markup:
                                                try: bot.edit_message_reply_markup(cid, msg_id, reply_markup=updated_markup)
                                                except: pass
                                                
                                            otp_count = len(otp_status[num])
                                            srv_display_name = service_info['srv_name']
                                            if otp_count > 1:
                                                suffix = "nd" if otp_count == 2 else "rd" if otp_count == 3 else "th"
                                                srv_display_name = f"{srv_display_name} ({otp_count}{suffix} OTP)"
                                                
                                            user_text, user_markup = generate_otp_card_data(srv_display_name, service_info['cnt_name'], num, otp_code, is_group=False)
                                            group_text, group_markup = generate_otp_card_data(srv_display_name, service_info['cnt_name'], num, otp_code, is_group=True)
                                            
                                            try: bot.send_message(cid, user_text, parse_mode="HTML", reply_markup=user_markup)
                                            except: pass
                                            
                                            forward_groups = data.get("forward_groups", [])
                                            if forward_groups:
                                                print(f"[GROUP FORWARD - global] User {cid} got new OTP. Forwarding to groups: {forward_groups}")
                                            for grp in forward_groups:
                                                target = safe_get_chat_id(grp)
                                                print(f"[GROUP FORWARD - global] -> Sending to target={target} (original: {grp})")
                                                try:
                                                    bot.send_message(target, group_text, parse_mode="HTML", reply_markup=group_markup)
                                                    print(f"[GROUP FORWARD - global] ✅ SUCCESS posted to {grp}")
                                                except Exception as e:
                                                    err_str = str(e)[:300]
                                                    print(f"[OTP Group Forward Error - global] ❌ FAILED Group: {grp} | target={target} | Error: {err_str}")
                                                    try:
                                                        bot.send_message(ADMIN_ID, f"⚠️ <b>OTP Group Forward Failed</b>\nGroup: <code>{grp}</code>\nTarget: <code>{target}</code>\nError: <code>{err_str}</code>\n\n<b>Common fixes:</b>\n• Make sure bot is <b>ADMIN</b> in the group/channel\n• For channels: enable 'Post Messages' permission\n• Use real chat_id (e.g. -1001234567890) not invite link\n• Check Data_File.json forward_groups list", parse_mode="HTML")
                                                    except: pass
        except: pass
        time.sleep(3.5)

def show_balance(chat_id, message_id=None):
    data = load_data()
    uid_str = str(chat_id)
    bal = data.get("balances", {}).get(uid_str, 0.0)
    min_wd = data.get("settings", {}).get("min_withdraw", 0.3)
    user_wallets = data.get("wallets", {}).get(uid_str, {})
    
    wallet_info = ""
    if user_wallets:
        wallet_info = f"\n{get_emoji_tag('emj_wallet')} <b>Your Saved Wallets:</b>\n"
        for w, v in user_wallets.items():
            wallet_info += f"- <b>{w.capitalize()}:</b> <code>{v}</code>\n"
    else:
        wallet_info = f"\n{get_emoji_tag('emj_wallet')} <i>No wallets added yet.</i>\n"

    text = f'{get_emoji_tag("emj_wallet")} <b>Balance</b>\n\n{get_emoji_tag("emj_wallet")} <b>Current balance:</b> {bal}$\n{get_emoji_tag("emj_stop")} <b>Minimum withdraw:</b> {min_wd}${wallet_info}\n<b>Choose a withdrawal method below:</b>'
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        ibtn("Bkash", callback_data="req_wd_bkash", style="success", custom_emoji_id=get_emoji_id("emj_bkash")), 
        ibtn("Nagad", callback_data="req_wd_nagad", style="success", custom_emoji_id=get_emoji_id("emj_nagad"))
    )
    markup.add(
        ibtn("Binance", callback_data="req_wd_binance", style="success", custom_emoji_id=get_emoji_id("emj_binance"))
    )
    
    w_types = ["bkash", "nagad", "binance"]
    for w in w_types:
        emoji_id = get_emoji_id(f"emj_{w}")
        if w in user_wallets:
            markup.add(
                ibtn(f"Edit {w.capitalize()}", callback_data=f"add_wal_{w}", style="primary", custom_emoji_id=emoji_id),
                ibtn(f"Delete {w.capitalize()}", callback_data=f"del_wal_{w}", style="danger", custom_emoji_id=get_emoji_id("emj_cross"))
            )
        else:
            markup.add(ibtn(f"Add {w.capitalize()}", callback_data=f"add_wal_{w}", style="primary", custom_emoji_id=emoji_id))
            
    markup.add(ibtn("Back to Menu", callback_data="close_inline", style="danger", custom_emoji_id=get_emoji_id("emj_cross")))
    
    if message_id: 
        try: bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, parse_mode="HTML", reply_markup=markup)
        except: pass
    else: 
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

def process_add_wallet(message, wallet_type):
    chat_id = message.chat.id
    try: bot.delete_message(chat_id, message.message_id)
    except: pass
    
    if message.text and is_menu_button(message.text):
        bot.clear_step_handler_by_chat_id(chat_id)
        handle_text(message)
        return
    
    data = load_data()
    data.setdefault("wallets", {}).setdefault(str(chat_id), {})[wallet_type] = message.text.strip()
    save_data(data)
    show_balance(chat_id)

def process_smart_wallet_withdrawal(message, wallet_type, amount):
    chat_id = message.chat.id
    try: bot.delete_message(chat_id, message.message_id)
    except: pass
    
    if message.text and is_menu_button(message.text):
        bot.clear_step_handler_by_chat_id(chat_id)
        handle_text(message)
        return
        
    val = message.text.strip()
    data = load_data()
    uid_str = str(chat_id)
    
    data.setdefault("wallets", {}).setdefault(uid_str, {})[wallet_type] = val
    
    bal = data.get("balances", {}).get(uid_str, 0.0)
    if bal <= 0 or bal < amount:
        bot.send_message(chat_id, f"{get_emoji_tag('emj_cross')} <b>Error:</b> Balance changed or insufficient.", parse_mode="HTML")
        save_data(data)
        show_balance(chat_id)
        return
        
    req_id = "wd_" + str(uuid.uuid4())[:8]
    
    data["balances"][uid_str] = round(bal - amount, 5)
    
    data.setdefault("pending_withdrawals", {})[req_id] = {
        "uid": uid_str, "amount": amount, "method": wallet_type, "address": val
    }
    save_data(data)
    
    bot.send_message(chat_id, f"{get_emoji_tag('emj_successful')} <b>Withdrawal Request Sent!</b>\n\n<b>Amount:</b> {amount}$\n<b>Method:</b> {wallet_type.capitalize()}\n<b>Address:</b> <code>{val}</code>\n\nPlease wait for admin approval.", parse_mode="HTML")
    
    admin_msg = (
        f"{get_emoji_tag('emj_wallet')} <b>NEW WITHDRAWAL REQUEST</b>\n\n"
        f"{get_emoji_tag('emj_profile')} <b>User ID:</b> <code>{uid_str}</code>\n"
        f"{get_emoji_tag('emj_wallet')} <b>Amount:</b> {amount}$\n"
        f"<b>Method:</b> {wallet_type.capitalize()}\n"
        f"<b>Address:</b> <code>{val}</code>\n\n"
        f"<i>Please open the Admin Panel Bot to approve or reject this withdrawal.</i>"
    )
    try: bot.send_message(ADMIN_ID, admin_msg, parse_mode="HTML")
    except: pass
    show_balance(chat_id)

def show_referral(chat_id):
    data = load_data()
    uid_str = str(chat_id)
    bal = data.get("balances", {}).get(uid_str, 0.0)
    ref_bonus = data.get("settings", {}).get("ref_bonus", 0.01)
    
    ref_list = data.get("referrals", {}).get(uid_str, [])
    total_refs = len(ref_list)
    ref_earnings = round(total_refs * ref_bonus, 5)
    
    ref_link = f"https://t.me/{get_bot_username()}?start={chat_id}"
    
    is_agent_or_admin = is_admin(chat_id) or str(chat_id) in data.get("agents", {})
    
    if is_agent_or_admin:
        # Agent view - shows commission earned from referrals' OTPs
        user_otp_rate = data.get("agents", {}).get(uid_str, data.get("settings", {}).get("otp_bonus", 0.0031))
        heading = f'{get_emoji_tag("emj_refer")} <b>Refer & Earn</b> [ <b>Agent</b><tg-emoji emoji-id="5339247212012528642">🌟</tg-emoji> ]'
        text = (
            f'{heading}\n\n'
            f'{get_emoji_tag("emj_link")} <b>Your referral link:</b>\n'
            f'<code>{ref_link}</code>\n\n'
            f'{get_emoji_tag("emj_profile")} <b>Total referrals:</b> {total_refs}\n'
            f'{get_emoji_tag("emj_successful")} <b>Per otp bonus:</b> {user_otp_rate}$\n\n'
            f'{get_emoji_tag("emj_wallet")} <b>Your current balance:</b> {bal}$'
        )
    else:
        # Normal user view - clean design without personal OTP rate
        heading = f'{get_emoji_tag("emj_refer")} <b>Refer & Earn</b>'
        text = (
            f'{heading}\n\n'
            f'{get_emoji_tag("emj_link")} <b>Your referral link:</b>\n'
            f'<code>{ref_link}</code>\n\n'
            f'{get_emoji_tag("emj_profile")} <b>Total referrals:</b> {total_refs}\n'
            f'{get_emoji_tag("emj_wallet")} <b>Referral earnings:</b> {ref_earnings}$\n'
            f'{get_emoji_tag("emj_add")} <b>Per referral:</b> {ref_bonus}$\n\n'
            f'{get_emoji_tag("emj_wallet")} <b>Your current balance:</b> {bal}$'
        )
    
    # === Share Button (with pre-filled message) ===
    share_text = (
        "প্রতিটা নাম্বারে ওটিপি আসে, রেফারেল পার ওটিপি বোনাস ৫০ পয়সা করে 💫\n\n"
        f"{ref_link}\n\n"
        "💯 এই বটে কাজ করে দেখুন 100% পার্সেন্ট আইডি হবে।"
    )
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        ibtn("🔗 Share", switch_inline_query=share_text, style="primary", custom_emoji_id=get_emoji_id("emj_share"))
    )
    
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

def show_support(chat_id):
    data = load_data()
    texts = data.setdefault("texts", {})
    sup_text = '<tg-emoji emoji-id="5337302974806922068">💬</tg-emoji> Support\n\n<tg-emoji emoji-id="5355208818017999139">📱</tg-emoji> Click the button below to contact support.'
    sup_lnk = texts.get("support_link") or "https://t.me/c/6703675335"
    
    markup = InlineKeyboardMarkup(row_width=2).add(ibtn("Contact Support", url=sup_lnk, style="primary", custom_emoji_id="5336879280578138635")) 
    bot.send_message(chat_id, sup_text, parse_mode="HTML", reply_markup=markup)

def show_leaderboard(chat_id):
    data = load_data()
    leaderboard = data.setdefault("leaderboard", {"last_reset": time.time(), "stats": {}})
    now = time.time()
    try: last_reset_time = float(leaderboard.get("last_reset", 0.0))
    except:
        last_reset_time = now
        leaderboard["last_reset"] = now
        save_data(data)

    reset_days = data.get("settings", {}).get("leaderboard_reset_days", 3)
    if now - last_reset_time >= (reset_days * 86400):
        notify_admin_leaderboard_winners_on_reset(leaderboard, data)
        save_data(data)
    
    stats = leaderboard.get("stats", {})
    sorted_stats = sorted(stats.items(), key=lambda item: item[1], reverse=True)[:10]
    
    text = f'{get_emoji_tag("emj_successful")} <b>DAILY TOP LEADERBOARD</b> {get_emoji_tag("emj_successful")}\n'
    text += f'<i>Resets automatically every {reset_days} days.</i>\n\n'
    
    if sorted_stats:
        def _get_user_name(uid):
            try:
                chat_info = bot.get_chat(int(uid))
                return chat_info.first_name or chat_info.username or f"User ({uid[-4:]})"
            except:
                return f"User ({uid[-4:]})"

        names = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_uid = {executor.submit(_get_user_name, uid): uid for uid, _ in sorted_stats}
            for future in as_completed(future_to_uid):
                uid = future_to_uid[future]
                try:
                    names[uid] = future.result()
                except:
                    names[uid] = f"User ({uid[-4:]})"

        for index, (uid, count) in enumerate(sorted_stats, 1):
            user_name = names.get(uid, f"User ({uid[-4:]})")
            text += f'<b>{index}.</b> {escape_html(user_name)} ➜ <code>{count} OTPs</code>\n'
    else:
        text += f'<i>{get_emoji_tag("emj_stop")} No OTPs fetched in this reset cycle.</i>'
        
    bot.send_message(chat_id, text, parse_mode="HTML")

def process_custom_rng_step_1(message, srv_id=None, edit_msg_id=None):
    chat_id = message.chat.id if hasattr(message, 'chat') else message.message.chat.id
    text = f"{get_emoji_tag('emj_changing')} <b>Please enter your Custom Range(s):</b>\n<i>(e.g., 261387304XXX)</i>"
    markup = InlineKeyboardMarkup().add(ibtn("Cancel", callback_data="cancel", style="danger", custom_emoji_id=get_emoji_id("emj_cross")))
    
    if edit_msg_id:
        try: bot.edit_message_text(text, chat_id=chat_id, message_id=edit_msg_id, parse_mode="HTML", reply_markup=markup)
        except: bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
        
    bot.register_next_step_handler_by_chat_id(chat_id, process_custom_rng_step_2, srv_id)

def process_custom_rng_step_2(message, srv_id=None):
    chat_id = message.chat.id
    if message.text and is_menu_button(message.text):
        bot.clear_step_handler_by_chat_id(chat_id)
        handle_text(message)
        return
        
    range_val = message.text.strip()
    try: bot.delete_message(chat_id, message.message_id)
    except: pass
    
    if not range_val: return
    threading.Thread(target=fetch_real_numbers, args=(chat_id, srv_id if srv_id != "custom" else None, None, None, range_val, None)).start()

# ============================================
# --- MESSAGE HANDLERS ---
# ============================================
@bot.message_handler(commands=['start', 'restart'])
def send_welcome(message):
    try:
        chat_id = message.chat.id
        if is_banned(chat_id): return
        
        data = load_data()
        if data.get("maintenance_mode", False) and not is_admin(chat_id):
            bot.send_message(chat_id, data.get("maintenance_message", "<b>⚠️ System under maintenance. Please try again later.</b>"), parse_mode="HTML")
            return
            
        if not is_subscribed(chat_id):
            send_force_join(chat_id)
            return
            
        bot.clear_step_handler_by_chat_id(chat_id)
        active_polls.pop(str(chat_id), None)
        user_id_str = str(chat_id)
        
        command_parts = message.text.split()
        if len(command_parts) > 1 and user_id_str not in data.get("users", []):
            ref_id = command_parts[1].strip()
            if ref_id.isdigit() and ref_id != user_id_str:
                ref_bonus = data.get("settings", {}).get("ref_bonus", 0.01)
                new_referral = False
                with db_lock:
                    temp_data = load_data()
                    temp_data.setdefault("referred_by", {})[user_id_str] = ref_id
                    if user_id_str not in temp_data.setdefault("referrals", {}).setdefault(ref_id, []):
                        temp_data["referrals"][ref_id].append(user_id_str)
                        temp_data.setdefault("balances", {})[ref_id] = round(temp_data.get("balances", {}).get(ref_id, 0.0) + ref_bonus, 5)
                        new_referral = True
                    save_data(temp_data)
                if new_referral:
                    try: bot.send_message(ref_id, f"{get_emoji_tag('emj_successful')} <b>New Referral!</b>\nUser <a href='tg://user?id={user_id_str}'>{user_id_str}</a> has joined through your link.\nYou earned <b>{ref_bonus}$</b>!", parse_mode="HTML")
                    except: pass
                data = temp_data

        if user_id_str not in data.get("users", []):
            data.setdefault("users", []).append(user_id_str)
            if data.get("settings", {}).get("admin_alerts", True):
                try: bot.send_message(ADMIN_ID, f"👤 <b>New User Started Bot!</b>\nID: <code>{user_id_str}</code>\nName: <a href='tg://user?id={user_id_str}'>{escape_html(message.from_user.first_name)}</a>", parse_mode="HTML")
                except: pass
            
        save_data(data)
        bot.send_message(chat_id, data.get("texts", {}).get("welcome", 'Welcome'), reply_markup=get_main_menu(chat_id), parse_mode="HTML", disable_web_page_preview=True)
    except: pass

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        bot.reply_to(message, "🚫 Only admins can use this command.")
        return
        
    last_time = broadcast_cooldown.get(chat_id, 0)
    current_time = time.time()
    if current_time - last_time < 300:
        remaining = int(300 - (current_time - last_time))
        bot.reply_to(message, f"⚠️ ব্রডকাস্টের জন্য আরও {remaining} সেকেন্ড অপেক্ষা করুন।")
        return

    bot.clear_step_handler_by_chat_id(chat_id)
    bot.reply_to(message, "📢 Send the message (text, photo, video, document, etc.) you want to broadcast to all users:\n\n⚠️ Note: This will send to ALL registered users. Be careful!")
    bot.register_next_step_handler(message, process_broadcast_to_users)

def process_broadcast_to_users(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        return
        
    data = load_data()
    users = data.get("users", [])
    if not users:
        bot.reply_to(message, "No users to broadcast to.")
        return

    broadcast_cooldown[chat_id] = time.time()

    success = 0
    failed = 0
    total = len(users)
    
    try:
        status_msg = bot.reply_to(message, f"🚀 Starting broadcast to {total} users...\nPlease wait, this may take time for large user base.")
    except:
        status_msg = None

    for idx, uid in enumerate(users, 1):
        try:
            bot.copy_message(chat_id=int(uid), from_chat_id=chat_id, message_id=message.message_id)
            success += 1
        except Exception as e:
            failed += 1
        time.sleep(0.03)

        if status_msg and idx % 50 == 0:
            try:
                bot.edit_message_text(f"🚀 Broadcasting... {idx}/{total} done\n✅ Success: {success} | ❌ Failed: {failed}", 
                                      chat_id=chat_id, message_id=status_msg.message_id)
            except:
                pass

    final_text = f"✅ Broadcast finished!\n\nTotal Users: {total}\n✅ Success: {success}\n❌ Failed: {failed}"
    try:
        if status_msg:
            bot.edit_message_text(final_text, chat_id=chat_id, message_id=status_msg.message_id)
        else:
            bot.reply_to(message, final_text)
    except:
        bot.reply_to(message, final_text)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    try:
        chat_id = message.chat.id
        if is_banned(chat_id): return
        
        data = load_data()
        if data.get("maintenance_mode", False) and not is_admin(chat_id):
            bot.send_message(chat_id, data.get("maintenance_message", "<b>⚠️ System under maintenance. Please try again later.</b>"), parse_mode="HTML")
            return
            
        if not is_subscribed(chat_id):
            send_force_join(chat_id)
            return
            
        text = str(message.text).strip()
        bot.clear_step_handler_by_chat_id(chat_id)
        
        texts = data.setdefault("texts", {})
        if text == texts.get("btn_get_number", "GET NUMBER"): show_services(chat_id)
        elif text == "Custom Number":
            try:
                data = load_data()
                last_fetch = data.get("last_number_fetch", {}).get(str(chat_id), 0)
                cooldown_sec = data.get("settings", {}).get("number_cooldown_seconds", 60)
                now = time.time()
                if last_fetch > 0 and (now - last_fetch) < cooldown_sec:
                    remaining = int(cooldown_sec - (now - last_fetch)) + 1
                    cool_msg = data.get("texts", {}).get("cooldown_message", "<b>⏳ Cooldown Active!</b>\n\n🕒 You can change again in <b>{time_left}s</b>.\n📌 Total Cooldown: <b>{cooldown}s</b>\n\nPress the button again when the time is up.")
                    popup_text = cool_msg.replace("{time_left}", str(remaining)).replace("{cooldown}", str(cooldown_sec)).replace("{seconds}", str(remaining))
                    bot.send_message(chat_id, popup_text, parse_mode="HTML")
                    return
            except Exception as e:
                print(f"Cooldown check error (Custom Number): {e}")
                pass
            process_custom_rng_step_1(message)
        elif text == texts.get("btn_balance", "BALANCE"): show_balance(chat_id)
        elif text == texts.get("btn_refer", "REFER AND EARN"): show_referral(chat_id)
        elif text == texts.get("btn_support", "SUPPORT"): show_support(chat_id)
        elif text == "LEADERBOARD": show_leaderboard(chat_id)
        elif text == texts.get("btn_renge_group", "Renge Group"):
            markup = InlineKeyboardMarkup().add(ibtn("Join Renge Group", url=texts.get("renge_group_link") or "https://t.me/+7JTfYe5oQAM4ODNl", style="primary", custom_emoji_id=get_emoji_id("emj_link")))
            bot.send_message(chat_id, f"{get_emoji_tag('emj_link')} <b>Click the button below to join our Renge Group:</b>", parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        print(f"handle_text error: {e}")
        pass

# ============================================
# --- CALLBACK HANDLERS ---
# ============================================
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    try:
        chat_id = call.message.chat.id
        msg_id = call.message.message_id
        if is_banned(chat_id): return
        data_call = call.data
        
        skip_generic_answer = data_call.startswith(("cp_", "chg_r|", "del_wal_", "req_wd_")) or data_call in ("chk_joined", "manual_get_otp_now")
        
        if not skip_generic_answer:
            try: bot.answer_callback_query(call.id)
            except: pass
            
        bot.clear_step_handler_by_chat_id(chat_id)

        if data_call.startswith("cp_"):
            bot.answer_callback_query(call.id, f"Copy: {data_call.split('cp_')[1]}", show_alert=True)
            
        elif data_call == "chk_joined":
            if is_subscribed(chat_id):
                bot.answer_callback_query(call.id, "Access Granted! Thanks for joining.", show_alert=True)
                try: bot.delete_message(chat_id, msg_id)
                except: pass
                bot.send_message(chat_id, load_data().get("texts", {}).get("welcome", 'Welcome'), reply_markup=get_main_menu(chat_id), parse_mode="HTML", disable_web_page_preview=True)
            else:
                bot.answer_callback_query(call.id, "You must join all channels first!", show_alert=True)
                
        elif data_call == "back_to_services": show_services(chat_id, msg_id)
        
        elif data_call == "close_inline":
            try: bot.delete_message(chat_id, msg_id)
            except: pass
            
        elif data_call == "cancel":
            bot.clear_step_handler_by_chat_id(chat_id)
            try: bot.delete_message(chat_id, msg_id)
            except: pass
            
        elif data_call.startswith("usr_s|"): show_countries(chat_id, data_call.split("|")[1], msg_id)
        
        elif data_call.startswith("usr_c|") or data_call.startswith("chg_r|"):
            if data_call.startswith("chg_r|"):
                try:
                    data = load_data()
                    last_fetch = data.get("last_number_fetch", {}).get(str(chat_id), 0)
                    cooldown_sec = data.get("settings", {}).get("number_cooldown_seconds", 60)
                    now = time.time()
                    if last_fetch > 0 and (now - last_fetch) < cooldown_sec:
                        remaining = int(cooldown_sec - (now - last_fetch)) + 1
                        bot.answer_callback_query(call.id, f"Please wait {remaining}s.", show_alert=True)
                        return
                except Exception:
                    pass
                
                try: bot.answer_callback_query(call.id)
                except: pass
                
            active_polls[str(chat_id)] = False
            parts = data_call.split("|")
            srv_id = parts[1]
            cnt_id = parts[2] if len(parts) > 2 else "custom"
            
            if srv_id == "custom" or cnt_id == "custom":
                range_val = None
                with active_sessions_lock:
                    sess = active_sessions.get(str(chat_id))
                    if sess: range_val = sess["service_info"].get("custom_range")
                if not range_val and len(parts) > 2: range_val = parts[2]
                
                if range_val and range_val != "custom":
                    threading.Thread(target=fetch_real_numbers, args=(chat_id, srv_id if srv_id != "custom" else None, None, msg_id, range_val, call.id)).start()
                else:
                    try: bot.delete_message(chat_id, msg_id)
                    except: pass
                    process_custom_rng_step_1(call.message, srv_id=srv_id if srv_id != "custom" else None)
            else:
                threading.Thread(target=fetch_real_numbers, args=(chat_id, srv_id, cnt_id, msg_id, None, call.id)).start()
                
        elif data_call.startswith("usr_custom_rng|"):
            process_custom_rng_step_1(call.message, data_call.split("|")[1], edit_msg_id=msg_id)

        elif data_call.startswith("add_wal_"):
            w_type = data_call.replace("add_wal_", "")
            text = f"<b>Please send your {w_type.capitalize()} number/address:</b>"
            markup = InlineKeyboardMarkup().add(ibtn("Cancel", callback_data="cancel", style="danger", custom_emoji_id=get_emoji_id("emj_cross")))
            try: bot.edit_message_text(text, chat_id=chat_id, message_id=msg_id, parse_mode="HTML", reply_markup=markup)
            except: pass
            bot.register_next_step_handler_by_chat_id(chat_id, process_add_wallet, w_type)
            
        elif data_call.startswith("del_wal_"):
            w_type = data_call.replace("del_wal_", "")
            data = load_data()
            if str(chat_id) in data.get("wallets", {}) and w_type in data["wallets"][str(chat_id)]:
                del data["wallets"][str(chat_id)][w_type]
                save_data(data)
                bot.answer_callback_query(call.id, f"{w_type.capitalize()} wallet deleted!", show_alert=True)
                show_balance(chat_id, msg_id)
            else:
                try: bot.answer_callback_query(call.id)
                except: pass
                
        elif data_call.startswith("req_wd_"):
            w_type = data_call.replace("req_wd_", "")
            data = load_data()
            uid_str = str(chat_id)
            bal = data.get("balances", {}).get(uid_str, 0.0)
            min_wd = data.get("settings", {}).get("min_withdraw", 0.3)
            wallets = data.get("wallets", {}).get(uid_str, {})
            
            if bal <= 0 or bal < min_wd:
                bot.answer_callback_query(call.id, f"Error: Balance must be at least {min_wd}$.", show_alert=True)
                return
                
            if w_type in wallets and wallets[w_type].strip():
                req_id = "wd_" + str(uuid.uuid4())[:8]
                data["balances"][uid_str] = round(bal - bal, 5) 
                data.setdefault("pending_withdrawals", {})[req_id] = {
                    "uid": uid_str, "amount": bal, "method": w_type, "address": wallets[w_type]
                }
                save_data(data)
                
                bot.answer_callback_query(call.id, f"Withdrawal request of {bal}$ submitted successfully!", show_alert=True)
                bot.send_message(chat_id, f"{get_emoji_tag('emj_successful')} <b>Withdrawal Request Sent!</b>\n\n<b>Amount:</b> {bal}$\n<b>Method:</b> {w_type.capitalize()}\n<b>Address:</b> <code>{wallets[w_type]}</code>\n\nPlease wait for admin approval.", parse_mode="HTML")
                show_balance(chat_id, msg_id)
                
                admin_msg = (
                    f"{get_emoji_tag('emj_wallet')} <b>NEW WITHDRAWAL REQUEST</b>\n\n"
                    f"{get_emoji_tag('emj_profile')} <b>User ID:</b> <code>{uid_str}</code>\n"
                    f"{get_emoji_tag('emj_wallet')} <b>Amount:</b> {bal}$\n"
                    f"<b>Method:</b> {w_type.capitalize()}\n"
                    f"<b>Address:</b> <code>{wallets[w_type]}</code>\n\n"
                    f"<i>Please open the Admin Panel Bot to approve or reject this withdrawal.</i>"
                )
                try: bot.send_message(ADMIN_ID, admin_msg, parse_mode="HTML")
                except: pass
            else:
                try: bot.answer_callback_query(call.id)
                except: pass
                text = f"<b>Please send your {w_type.capitalize()} number/address to complete withdrawal of {bal}$:</b>"
                markup = InlineKeyboardMarkup().add(ibtn("Cancel", callback_data="cancel", style="danger", custom_emoji_id=get_emoji_id("emj_cross")))
                try: bot.edit_message_text(text, chat_id=chat_id, message_id=msg_id, parse_mode="HTML", reply_markup=markup)
                except: bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
                bot.register_next_step_handler_by_chat_id(chat_id, process_smart_wallet_withdrawal, w_type, bal)

        elif data_call == "manual_get_otp_now":
            threading.Thread(target=manual_check_otps, args=(chat_id, call.id)).start()
            
        elif data_call == "finish_active_session":
            with active_sessions_lock:
                if str(chat_id) in active_sessions: del active_sessions[str(chat_id)]
                active_polls.pop(str(chat_id), None)
            try: bot.edit_message_text("<b>🛑 Session finished. You can now get new numbers!</b>", chat_id=chat_id, message_id=msg_id, parse_mode="HTML")
            except: pass
    except Exception as e:
        print(f"[handle_query ERROR] data={getattr(call, 'data', None)} err={e}")
        try:
            bot.answer_callback_query(call.id, "⚠️ Temporary error. Please try again.", show_alert=True)
        except:
            pass

# ============================================
# --- RUN THE BOT SAFELY ---
# ============================================
if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    try:
        bot.remove_webhook()
    except Exception as e:
        pass
        
    threading.Thread(target=global_otp_polling_loop, daemon=True).start()
    bot.infinity_polling()