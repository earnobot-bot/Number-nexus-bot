import logging
import requests
import asyncio
import pyotp
import pandas as pd
import os
import json
import random
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import BadRequest

# --- কনফিগারেশন ---
BOT_TOKEN = "8863510519:AAG66NYWEDnTujN45Uuf4pAZ2Dn9hGvGF-k"
ADMIN_ID = 6703675335
API_KEY = "nxa_bfa68b4cf78247617af5664f54629dba589728ad"
BASE_URL = "http://185.190.142.81/api/v1"

HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

LOG_GROUP = "@otp_group_public" 

# গলোবাল ভেরিয়বল (১৬টি লোকেশন)
COUNTRIES_DATA = {
    "ghana_1": {"name": "Ghana 🇬🇭", "range": "233244XXX", "prefix": "233", "is_default": True},
    "guinea_1": {"name": "Guinea 🇬🇳", "range": "224621XXXX", "prefix": "224", "is_default": True},
    "iraq_1": {"name": "Iraq 🇮🇶", "range": "964770XXXX", "prefix": "964", "is_default": True},
    "kyivstar_1": {"name": "Kyivstar 🇺🇦", "range": "38067XXXXX", "prefix": "380", "is_default": True},
    "madagascar_1": {"name": "Madagascar 🇲🇬", "range": "261342651XXX", "prefix": "261", "is_default": True},
    "mali_1": {"name": "Mali 🇲🇱", "range": "22376XXXX", "prefix": "223", "is_default": True},
    "malitel_1": {"name": "Malitel 🇲🇱", "range": "22366XXXX", "prefix": "223", "is_default": True},
    "myanmar_1": {"name": "Myanmar 🇲🇲", "range": "95942XXXX", "prefix": "95", "is_default": True},
    "nigeria_1": {"name": "Nigeria 🇳🇬", "range": "234803XXXXX", "prefix": "234", "is_default": True},
    "palestine_1": {"name": "Palestine 🇵🇸", "range": "97059XXXX", "prefix": "970", "is_default": True},
    "syria_2": {"name": "Syria 🇸🇾", "range": "963974999XXX", "prefix": "963", "is_default": True},
    "tanzania_1": {"name": "Tanzania 🇹🇿", "range": "25565XXXX", "prefix": "255", "is_default": True},
    "tunisiana_1": {"name": "Tunisiana 🇹🇳", "range": "21622XXXX", "prefix": "216", "is_default": True},
    "uzbekistan_1": {"name": "Uzbekistan 🇺🇿", "range": "99890XXXX", "prefix": "998", "is_default": True},
    "venezuela_1": {"name": "Venezuela 🇻🇪", "range": "58414XXXX", "prefix": "58", "is_default": True},
    "vietnam_1": {"name": "Vietnam 🇻🇳", "range": "8491XXXXX", "prefix": "84", "is_default": True},
    "yemen_1": {"name": "Yemen 🇾🇪", "range": "96773XXXX", "prefix": "967", "is_default": True},
    "zimbabwe_1": {"name": "Zimbabwe 🇿🇼", "range": "263777155XXX", "prefix": "263", "is_default": True}
}
SERVICE_STATUS = True 
ADMIN_SETTINGS = {}

USER_OTP_COUNT = {}
USER_LANG = {} 
PENDING_VPN_REQUESTS = {}
ALL_USERS = set() 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- ল্যাঙ্গুয়েজ স্ট্রিং ডিকশনারি ---
STRINGS = {
    "en": {
        "welcome": "👋 Welcome! /language\n\n✅ Choose a country from the buttons below.",
        "select_country": "🌍 Choose a country from the buttons below:",
        "btn_get_num": "📫 Get number",
        "btn_countries": "🌍 Countries",
        "btn_2fa": "🔐 2FA Code",
        "btn_dup": "🫆 Duplicate Checker",
        "btn_vpn": "🛡️ Free VPN",
        "btn_language": "🌐 Language",
        "btn_admin": "⚙️ Admin Panel",
        "access_denied": "⚠️ Access Denied! Join our channel first.",
        "service_off": "🛑 Service is currently offline.",
        "requesting": '<tg-emoji emoji-id="5341498088408234504">💯</tg-emoji>Requesting number for',
        "no_numbers": "⚠️ Notice: No numbers available for",
        "enter_secret": '<tg-emoji emoji-id="5296369303661067030">🔒</tg-emoji> Enter Secret Key:',
        "upload_xlsx": "📂 Upload .xlsx file.",
        "lang_changed": "✅ Language changed successfully to English!"
    },
    "ir": {
        "welcome": "👋 خوش آمدید! /language\n\n✅ کشوری را از دکمه های زیر انتخاب کنید.",
        "select_country": "🌍 کشوری را از دکمه های زیر انتخاب کنید:",
        "btn_get_num": "📫 Get number",
        "btn_countries": "🌍 کشورها",
        "btn_2fa": "🔐 کد 2FA",
        "btn_dup": "🫆 بررسی تکراری",
        "btn_vpn": "🛡️ وی پی ان رایگان",
        "btn_language": "🌐 زبان (Language)",
        "btn_admin": "⚙️ پنল مدیریت",
        "access_denied": "⚠️ دسترسی مسدود شد! ابتدا عضو کانال شوید.",
        "service_off": "🛑 سرویس در حال حاضر غیرفعال است.",
        "requesting": '<tg-emoji emoji-id="5341498088408234504">💯</tg-emoji>Requesting number for',
        "no_numbers": "⚠️ توجه: شماره ای موجود نیست برای",
        "enter_secret": '<tg-emoji emoji-id="5296369303661067030">🔒</tg-emoji> Enter Secret Key:',
        "upload_xlsx": "📂 ফাইল .xlsx ফাইলটি আপলোড করুন।",
        "lang_changed": "✅ زبان با موفقیت به فارسی تغییر یافت!"
    }
}

# --- মেম্বারশিপ চেক ফাংশন ---
async def is_subscribed(context, user_id):
    try:
        member = await context.bot.get_chat_member(chat_id=LOG_GROUP, user_id=user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception:
        return False

# --- কিবোর্ডস ---
def get_main_keyboard(user_id):
    lang = USER_LANG.get(user_id, "en")
    keyboard = [
        [KeyboardButton(STRINGS[lang]["btn_get_num"]), KeyboardButton(STRINGS[lang]["btn_countries"])],
        [KeyboardButton(STRINGS[lang]["btn_2fa"]), KeyboardButton(STRINGS[lang]["btn_vpn"])],
        [KeyboardButton(STRINGS[lang]["btn_dup"]), KeyboardButton(STRINGS[lang]["btn_language"])]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([KeyboardButton(STRINGS[lang]["btn_admin"])])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_join_keyboard():
    keyboard = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{LOG_GROUP.replace('@', '')}")]]
    return InlineKeyboardMarkup(keyboard)

def get_countries_keyboard():
    grouped = {}
    for key, data in COUNTRIES_DATA.items():
        name = data["name"].strip()
        if name not in grouped:
            grouped[name] = []
        grouped[name].append(key)
    
    keyboard = []
    names = list(grouped.keys())
    for i in range(0, len(names), 2):
        row = []
        name1 = names[i]
        count1 = len(grouped[name1])
        
        if count1 > 1:
            label1 = f"{name1} ({count1:02d})"
            cb1 = f"group_{name1}"
        else:
            label1 = f"{name1}"
            cb1 = f"sel_{grouped[name1][0]}"
        row.append(InlineKeyboardButton(label1, callback_data=cb1))
        
        if i + 1 < len(names):
            name2 = names[i+1]
            count2 = len(grouped[name2])
            if count2 > 1:
                label2 = f"{name2} ({count2:02d})"
                cb2 = f"group_{name2}"
            else:
                label2 = f"{name2}"
                cb2 = f"sel_{grouped[name2][0]}"
            row.append(InlineKeyboardButton(label2, callback_data=cb2))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def get_sub_countries_keyboard(country_name):
    keyboard = []
    sub_list = {k: v for k, v in COUNTRIES_DATA.items() if v["name"].lower() == country_name.lower()}
    idx = 1
    items = list(sub_list.items())
    for i in range(0, len(items), 2):
        row = []
        key1, data1 = items[i]
        row.append(InlineKeyboardButton(f"{country_name} - {idx}", callback_data=f"sel_{key1}"))
        idx += 1
        if i + 1 < len(items):
            key2, data2 = items[i+1]
            row.append(InlineKeyboardButton(f"{country_name} - {idx}", callback_data=f"sel_{key2}"))
            idx += 1
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_countries")])
    return InlineKeyboardMarkup(keyboard)

def get_language_keyboard():
    keyboard = [
        [InlineKeyboardButton("🇮🇷 ایران", callback_data="lang_ir"), 
         InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_number_panel_keyboard(country_key):
    keyboard = [
        [
            InlineKeyboardButton("🔄 New Number", callback_data=f"sel_{country_key}"),
            InlineKeyboardButton("📢 Codes Group", url=f"https://t.me/{LOG_GROUP.replace('@', '')}")
        ],
        [InlineKeyboardButton("⬅️ Back to Countries", callback_data="back_to_countries")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- এডমিন কিবোর্ডস ---
def get_admin_main_keyboard():
    status_text = "🟢 Service: ON" if SERVICE_STATUS else "🔴 Service: OFF"
    keyboard = [
        [InlineKeyboardButton("➕ Add Country", callback_data="adm_add"), InlineKeyboardButton("❌ Remove Country", callback_data="adm_rem")],
        [InlineKeyboardButton("⚙️ Set Defaults", callback_data="adm_set_def"), InlineKeyboardButton(status_text, callback_data="adm_toggle")],
        [InlineKeyboardButton("📊 Bot Stats", callback_data="adm_stats"), InlineKeyboardButton("📣 Broadcast", callback_data="adm_broadcast")],
        [InlineKeyboardButton("🔙 Back", callback_data="adm_back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_default_setting_keyboard():
    keyboard = []
    for key, data in COUNTRIES_DATA.items():
        status = "✅" if data.get("is_default", False) else "❌"
        keyboard.append([InlineKeyboardButton(f"{data['name']} ({key}) {status}", callback_data=f"toggle_def_{key}")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="adm_back")])
    return InlineKeyboardMarkup(keyboard)

# --- ওটিপি ট্র্যাকিং ---
async def track_otp(context, chat_id, num_id, phone, country_name):
    for i in range(150):
        await asyncio.sleep(4)
        try:
            url = f"{BASE_URL}/numbers/{num_id}/sms"
            loop = asyncio.get_event_loop()
            
            def fetch_sms():
                try:
                    res = requests.get(url, headers=HEADERS, timeout=12)
                    return res.json()
                except:
                    return None

            response = await loop.run_in_executor(None, fetch_sms)
            
            if response and response.get("otp"):
                otp_code = response["otp"]
                full_text = response.get("full_text", f"{otp_code} is your verification code")
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                USER_OTP_COUNT[chat_id] = USER_OTP_COUNT.get(chat_id, 0) + 1

                user_msg = (
                    f"✨ Message OTP Received ✨\n\n"
                    f"🌍 Country: {country_name}\n"
                    f"☎ Number: <code>{phone}</code>\n"
                    f"🕒 Time: {current_time}\n\n"
                    f"🔐 Code: <code>{otp_code}</code>\n\n"
                    f"{full_text}"
                )
                await context.bot.send_message(chat_id=chat_id, text=user_msg, parse_mode='HTML')
                
                masked_phone = f"{phone[:4]}****{phone[-3:]}"
                channel_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 Main Channel", url="https://t.me/your_main_channel"),
                     InlineKeyboardButton("🤖 Number Bot", url=f"https://t.me/{context.bot.username}")]
                ])

                group_msg = (
                    f"✨ OTP Received ✨\n\n"
                    f"⏰ Time: {current_time}\n"
                    f"📞 Number: {masked_phone}\n"
                    f"🌐 Country: {country_name}\n"
                    f"🛠 Service: 📩 SMS Received\n\n"
                    f"🔑 OTP Code: {otp_code}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"💬 {full_text}\n"
                    f"━━━━━━━━━━━━━━━━━━━━"
                )
                await context.bot.send_message(chat_id=LOG_GROUP, text=group_msg, reply_markup=channel_keyboard)
                return 
        except:
            continue

# --- ডুপ্লিকেট চেকর ---
async def process_duplicate_checker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document:
        return
    
    file_name = update.message.document.file_name
    if not file_name.endswith('.xlsx'):
        await update.message.reply_text("❌ Please upload a valid .xlsx file.")
        return

    file = await update.message.document.get_file()
    input_file = f"input_{update.message.chat_id}.xlsx"
    output_file = f"result_{update.message.chat_id}.xlsx"
    await file.download_to_drive(input_file)
    
    status_msg = await update.message.reply_text("⚙️ Initializing analysis... 0%")
    try:
        for p in [20, 45, 70, 90]:
            await asyncio.sleep(0.5)
            await status_msg.edit_text(f"⚙️ Processing data... {p}%")
            
        # ইনপুট ফাইলটি রিড করা হচ্ছে (সব কলামসহ)
        df = pd.read_excel(input_file, header=None)
        
        # প্রথম কলামের (যা ইউজারনেম) ডুপ্লিকেট চেক করার সুবিধার্থে সব ডেটাকে স্ট্রিপ করা হচ্ছে
        df[0] = df[0].astype(str).str.strip()
        
        # প্রথম কলামের বেসিসে ইউনিক রো এবং ডুপ্লিকেট রো আলাদাকরণ
        unique_df = df.drop_duplicates(subset=[0], keep='first')
        duplicate_df = df[df.duplicated(subset=[0], keep='first')]
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            unique_df.to_excel(writer, sheet_name='Sheet1', index=False, header=False)
            if len(duplicate_df) > 0:
                duplicate_df.to_excel(writer, sheet_name='Sheet2', index=False, header=False)
        
        await status_msg.edit_text(f"⚙️ Processing complete! 100%")
        summary = (
            f"📊 Data Analysis Report\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Unique IDs: {len(unique_df)} \n"
            f"🚫 Duplicate IDs: {len(duplicate_df)} \n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📂 Check the attached file for details."
        )
        await update.message.reply_document(document=open(output_file, 'rb'), caption=summary)
        await status_msg.delete()
        context.user_data['state'] = None
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: Failed to process the file.")
        print(f"Error: {e}")
    finally:
        if os.path.exists(input_file): os.remove(input_file)
        if os.path.exists(output_file): os.remove(output_file)

# --- নম্বর রিকোয়েস্ট লজিক ---
async def request_number(msg_or_query, context, user_id, country_key=None):
    lang = USER_LANG.get(user_id, "en")
    if not await is_subscribed(context, user_id):
        return await (msg_or_query.message.reply_text if isinstance(msg_or_query, Update) else msg_or_query.message.edit_text)(
            STRINGS[lang]["access_denied"], reply_markup=get_join_keyboard()
        )
    if not SERVICE_STATUS:
        text = STRINGS[lang]["service_off"]
        if isinstance(msg_or_query, Update): await msg_or_query.message.reply_text(text)
        else: await msg_or_query.message.edit_text(text)
        return
    if country_key is None:
        default_keys = [k for k, v in COUNTRIES_DATA.items() if v.get("is_default")]
        if not default_keys:
            text = "⚠️ Notice: No default countries set by Admin."
            if isinstance(msg_or_query, Update): await msg_or_query.message.reply_text(text)
            else: await msg_or_query.message.edit_text(text)
            return
        country_key = random.choice(default_keys)
    
    loop = asyncio.get_event_loop()
    country_info = COUNTRIES_DATA.get(country_key)
    country_name = country_info['name']
    
    status_text = f"{STRINGS[lang]['requesting']} {country_name} <tg-emoji emoji-id=\"5258088414770645443\">🟧</tg-emoji>"
    
    if isinstance(msg_or_query, Update): 
        msg = await msg_or_query.message.reply_text(status_text, parse_mode='HTML')
    else: 
        msg = msg_or_query.message
        await msg.edit_text(status_text, parse_mode='HTML')
        
    try:
        endpoint = f"{BASE_URL}/numbers/get"
        payload = {"range": country_info["range"], "format": "national"}
        
        def do_request():
            try:
                res = requests.post(endpoint, json=payload, headers=HEADERS, timeout=15)
                if res.status_code != 200:
                    res = requests.get(endpoint, params=payload, headers=HEADERS, timeout=15)
                return res
            except:
                return requests.get(endpoint, params=payload, headers=HEADERS, timeout=15)
            
        response = await loop.run_in_executor(None, do_request)
        r = response.json()
        
        if r and (r.get("success") is True or "number" in r):
            raw_phone = str(r.get("number")).replace("+", "").replace(" ", "").strip()
            
            clean_range = re.sub(r'\D', '', country_info["range"])
            prefix = country_info["prefix"] if country_info["prefix"] else clean_range[:3]
            
            # প্যানেলের আসল নম্বরের সাথে হুবহু মিল রাখার জন্য অতিরিক্ত '0' বা প্রিলিমিনারি ভুল ফরম্যাট ফিক্সিং লজিক
            if raw_phone.startswith(prefix):
                phone = raw_phone
            else:
                # যদি র-নম্বরের শুরুতে লোকাল '0' থাকে, সেটা বাদ দিয়ে কান্ট্রি কোড যুক্ত করা
                if raw_phone.startswith("0"):
                    raw_phone = raw_phone[1:]
                
                if raw_phone.startswith(prefix[-1]) and not raw_phone.startswith(prefix):
                    phone = f"{prefix[:-1]}{raw_phone}"
                else:
                    phone = f"{prefix}{raw_phone}"
                    
            num_id = r.get("id") if r.get("id") else raw_phone 
            
            display_text = (
                f'🌍 Country: {country_name}\n\n'
                f'<tg-emoji emoji-id="5343673308955042746">➖</tg-emoji> Number: <code>{phone}</code>\n\n'
                f'<tg-emoji emoji-id="5197269100878907942">✍️</tg-emoji> Long press to copy.'
            )
            await msg.edit_text(display_text, reply_markup=get_number_panel_keyboard(country_key), parse_mode='HTML')
            asyncio.create_task(track_otp(context, user_id, num_id, phone, country_name))
        else:
            await msg.edit_text(f"{STRINGS[lang]['no_numbers']} {country_name}.", reply_markup=get_countries_keyboard())
    except Exception as e:
        logging.error(f"Request Number Error: {e}")
        await msg.edit_text("❌ Connection Error. Please try again.")

# --- হ্যান্ডলারস ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ALL_USERS.add(user_id) 
    lang = USER_LANG.get(user_id, "en")
    if not await is_subscribed(context, user_id):
        return await update.message.reply_text(STRINGS[lang]["access_denied"], reply_markup=get_join_keyboard())
    await update.message.reply_text(STRINGS[lang]["welcome"], reply_markup=get_countries_keyboard())
    await context.bot.send_message(chat_id=user_id, text="🏠 Main Menu", reply_markup=get_main_keyboard(user_id))

async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ALL_USERS.add(user_id)
    if not await is_subscribed(context, user_id):
        lang = USER_LANG.get(user_id, "en")
        return await update.message.reply_text(STRINGS[lang]["access_denied"], reply_markup=get_join_keyboard())
    await update.message.reply_text("🌐 Select Language / انتخاب زبان:", reply_markup=get_language_keyboard())

# --- ইউজার ডেটা এক্সপোর্ট কমান্ড ( can only be accessed by admin ) ---
async def user_data_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    status_msg = await update.message.reply_text("📊 Extracting user dataset... Please wait.")
    
    user_list = list(ALL_USERS)
    data_rows = []
    
    for uid in user_list:
        try:
            chat = await context.bot.get_chat(chat_id=uid)
            username = f"@{chat.username}" if chat.username else "No Username"
        except:
            username = "Unknown"
            
        data_rows.append([uid, username])
        
    output_file = f"user_sheet_{user_id}.xlsx"
    try:
        df = pd.DataFrame(data_rows)
        df.to_excel(output_file, index=False, header=False)
        
        await update.message.reply_document(
            document=open(output_file, 'rb'), 
            caption=f"✅ Total {len(user_list)} users data generated successfully."
        )
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text("❌ Error generating user dataset sheet.")
    finally:
        if os.path.exists(output_file): 
            os.remove(output_file)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message
    if not user_msg or not user_msg.text:
        return  
        
    text = user_msg.text
    user_id = update.effective_user.id
    ALL_USERS.add(user_id)
    lang = USER_LANG.get(user_id, "en")
    
    # ব্রডকাস্ট সিস্টেম
    if context.user_data.get('state') == 'ADM_BROADCAST' and user_id == ADMIN_ID:
        count = 0
        status_msg = await update.message.reply_text("📣 Starting Secure Broadcast...")
        for uid in ALL_USERS:
            try:
                await context.bot.copy_message(chat_id=uid, from_chat_id=user_msg.chat_id, message_id=user_msg.message_id)
                count += 1
                await asyncio.sleep(0.05)
            except: continue
        await status_msg.edit_text(f"✅ Broadcast complete! Sent to {count} users.")
        context.user_data['state'] = None
        return

    if not await is_subscribed(context, user_id): 
        return await update.message.reply_text(STRINGS[lang]["access_denied"], reply_markup=get_join_keyboard())

    if text in ["📫 Get number"]:
        await request_number(update, context, user_id)
    elif text in ["🌍 Countries", "🌍 کشورها"]:
        await update.message.reply_text(STRINGS[lang]["select_country"], reply_markup=get_countries_keyboard())
    elif text in ["⚙️ Admin Panel", "⚙️ پنল مدیریت"] and user_id == ADMIN_ID:
        await update.message.reply_text("🛠 Admin Panel", reply_markup=get_admin_main_keyboard())
    elif text in ["🌐 Language", "🌐 زبان (Language)"]:
        await update.message.reply_text("🌐 Select Language / انتخاب زبان:", reply_markup=get_language_keyboard())
    elif text in ["🔐 2FA Code", "🔐 کد 2FA"]:
        context.user_data['state'] = 'AWAITING_2FA'
        await update.message.reply_text(STRINGS[lang]["enter_secret"], parse_mode='HTML')
    elif text in ["🫆 Duplicate Checker", "🫆 بررسی تکراری"]:
        context.user_data['state'] = 'AWAITING_FILE'
        await update.message.reply_text(f"{STRINGS[lang]['upload_xlsx']}")
    elif text in ["🛡️ Free VPN", "🛡️ وی پی ان رایگان"]:
        vpn_text = (
            f"<tg-emoji emoji-id=\"5841267724285646096\">🆓</tg-emoji> <b>Exclusive Premium Free VPN Service</b> <tg-emoji emoji-id=\"5841267724285646096\">🆓</tg-emoji>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎁 <b>Good News!</b> We release and upload high-speed <b>Premium VPN configs & accounts every single day</b> completely for free in our official Telegram channel!\n\n"
            f"⚡ <b>What you will get:</b>\n"
            f"✅ Daily fresh premium updates\n"
            f"✅ High-speed configurations\n"
            f"✅ Unlimited bandwidth & secure browsing\n\n"
            f"👉 Make sure to stay joined in our official channel/group to enjoy premium VPN services daily without spending a single penny!"
        )
        vpn_kb = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join For Claim", url="https://t.me/otp_group_public/157")]])
        await update.message.reply_text(vpn_text, reply_markup=vpn_kb, parse_mode='HTML')

    # এডমিন অ্যাকশন
    elif context.user_data.get('state') == 'ADM_ADD_DATA' and user_id == ADMIN_ID:
        lines = text.split('\n')
        success_count = 0
        failed_count = 0
        added_list = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                parts = line.split("-")
                if len(parts) == 2:
                    name = parts[0].strip()
                    r_range = parts[1].strip()
                    
                    clean_range = re.sub(r'\D', '', r_range)
                    prefix = clean_range[:3] if clean_range else "000"
                    
                    clean_key = re.sub(r'[^\w\s]', '', name).strip().lower().replace(" ", "_")
                    if not clean_key:
                        clean_key = "country"
                        
                    existing = [k for k in COUNTRIES_DATA.keys() if k.startswith(clean_key)]
                    key = f"{clean_key}_{len(existing) + 1}"
                    
                    COUNTRIES_DATA[key] = {"name": name, "range": r_range, "prefix": prefix, "is_default": False}
                    added_list.append(f"• {name} ({r_range})")
                    success_count += 1
                else:
                    failed_count += 1
            except Exception:
                failed_count += 1

        response_msg = f"📊 Country Process Report:\n━━━━━━━━━━━━━━━━━━━━\n"
        if success_count > 0:
            response_msg += f"✅ Successfully Added ({success_count}):\n" + "\n".join(added_list) + "\n"
        if failed_count > 0:
            response_msg += f"\n❌ Failed to process {failed_count} line(s). Please check format (Name - Range)."
            
        await update.message.reply_text(response_msg)
        context.user_data['state'] = None

    elif context.user_data.get('state') == 'ADM_REM_KEY' and user_id == ADMIN_ID:
        key = text.strip().lower()
        if key in COUNTRIES_DATA:
            del COUNTRIES_DATA[key]
            await update.message.reply_text(f"✅ Removed: {key}")
        else:
            await update.message.reply_text("❌ Key not found.")
        context.user_data['state'] = None
        
    elif context.user_data.get('state') == 'AWAITING_2FA':
        try:
            totp = pyotp.TOTP(text.replace(" ", ""))
            code = totp.now()
            await update.message.reply_text(f"🔐 Your 2FA Code: <code>{code}</code>", parse_mode='HTML')
        except:
            await update.message.reply_text("❌ Invalid Secret Key.")
        context.user_data['state'] = None

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if not await is_subscribed(context, user_id):
        await query.answer()
        lang = USER_LANG.get(user_id, "en")
        try:
            await query.message.edit_text(STRINGS[lang]["access_denied"], reply_markup=get_join_keyboard())
        except BadRequest:
            await query.message.reply_text(STRINGS[lang]["access_denied"], reply_markup=get_join_keyboard())
        return

    await query.answer()
    global SERVICE_STATUS

    if query.data.startswith("lang_"):
        selected_lang = query.data.replace("lang_", "")
        USER_LANG[user_id] = selected_lang
        await query.message.delete()
        await context.bot.send_message(
            chat_id=user_id, 
            text=STRINGS[selected_lang]["lang_changed"], 
            reply_markup=get_main_keyboard(user_id)
        )
    elif query.data.startswith("sel_"):
        await request_number(query, context, user_id, query.data.replace("sel_", ""))
    elif query.data.startswith("group_"):
        country_name = query.data.replace("group_", "")
        await query.message.edit_text(f"📍 Select Service for {country_name}:", reply_markup=get_sub_countries_keyboard(country_name))
    elif query.data == "back_to_countries":
        lang = USER_LANG.get(user_id, "en")
        await query.message.edit_text(STRINGS[lang]["select_country"], reply_markup=get_countries_keyboard())

    if user_id == ADMIN_ID:
        if query.data == "adm_broadcast":
            context.user_data['state'] = 'ADM_BROADCAST'
            await query.message.reply_text("📢 Send or Forward ANY message. The bot will send it to all users hiding your name:")
        elif query.data == "adm_toggle":
            SERVICE_STATUS = not SERVICE_STATUS
            await query.message.edit_reply_markup(reply_markup=get_admin_main_keyboard())
        elif query.data == "adm_add":
            context.user_data['state'] = 'ADM_ADD_DATA'
            await query.message.reply_text("✍️ Format:\n`Name - Range`\n\n💡 You can add single or MULTIPLE lines at once (with Flag):\nExample:\n`🇸🇱 Sierra leone - 23276216XXX`\n`🇹🇭 Thailand - 66883896XXX`", parse_mode='Markdown')
        elif query.data == "adm_rem":
            context.user_data['state'] = 'ADM_REM_KEY'
            keys_list = "\n".join([f"• `{k}`" for k in COUNTRIES_DATA.keys()])
            await query.message.reply_text(f"🗑️ Enter the key to remove:\n\n{keys_list}", parse_mode='Markdown')
        elif query.data == "adm_set_def":
            await query.message.edit_text("⚙️ Choose to toggle default status:", reply_markup=get_default_setting_keyboard())
        elif query.data.startswith("toggle_def_"):
            key = query.data.replace("toggle_def_", "")
            if key in COUNTRIES_DATA:
                COUNTRIES_DATA[key]["is_default"] = not COUNTRIES_DATA[key].get("is_default", False)
                await query.message.edit_reply_markup(reply_markup=get_default_setting_keyboard())
        elif query.data == "adm_back" or query.data == "adm_back_main":
            await query.message.edit_text("🛠 Admin Panel", reply_markup=get_admin_main_keyboard())
        elif query.data == "adm_stats":
            await query.message.reply_text(f"📊 Stats:\nTotal Users: {len(ALL_USERS)}\nCountries: {len(COUNTRIES_DATA)}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler(["language", "lan"], language_command, filters=filters.ChatType.PRIVATE))
    
    app.add_handler(CommandHandler("user_data", user_data_command, filters=filters.ChatType.PRIVATE))
    
    app.add_handler(MessageHandler(filters.Document.ALL & filters.ChatType.PRIVATE, process_duplicate_checker))
    
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_text))
    
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling()

if __name__ == "__main__":
    main()
