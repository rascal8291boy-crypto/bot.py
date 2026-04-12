import os
from flask import Flask
from threading import Thread
import telebot
import sqlite3
import random
import time  # mute ke liye
from telebot import types
from datetime import date, timedelta

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is alive!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
    
API_TOKEN = '8740586204:AAHaVnVgj2WoTlk3Oqrxze13Jl4oyQk2_zc'
bot = telebot.TeleBot(API_TOKEN)

# Hangman game states
hangman_games = {}

# Security mode per group (chat_id: True/False)
security_enabled = {}

# Blocked keywords
BLOCKED_KEYWORDS = ["cp", "child porn", "pornography", "drugs", "medicine","porn"]
SEVERE_KEYWORDS = ["cp", "child porn"]

# Manipulator Purple Logo
LEADERBOARD_BANNER = "https://instasize.com/p/d8a6ee46b4c5807bd1a2cbed95bd80376c559e38391e034dacb82f51b6e99153"

# ====================== DATABASE SETUP ======================
def init_db():
    conn = sqlite3.connect('ranking.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, name TEXT, xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS daily_messages 
                 (user_id INTEGER NOT NULL,
                  chat_id INTEGER NOT NULL,
                  date TEXT NOT NULL,
                  message_count INTEGER DEFAULT 0,
                  PRIMARY KEY (user_id, chat_id, date))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS security_settings 
                 (chat_id INTEGER PRIMARY KEY, enabled INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS groups 
                 (chat_id INTEGER PRIMARY KEY, title TEXT)''')
    conn.commit()
    conn.close()

# ====================== CHECK ADMIN ======================
def is_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except:
        return False

# ====================== BOT MENU ======================
def set_bot_menu():
    commands = [
        types.BotCommand("start", "start the bot🚀"),
        types.BotCommand("rankings", "View the group leaderboard 🏆"),
        types.BotCommand("topgame", "View the group points leaderboard 🎮"),
        types.BotCommand("topusers", "View the global users leaderboard 🌍"),
        types.BotCommand("topgroups", "View global groups leaderboard 👥"),
        types.BotCommand("profile", "View your profile stats 👤"),
        types.BotCommand("groupstats", "View the group stats 📊"),
        types.BotCommand("hangman", "Start the hangman game 🕹️"),
        types.BotCommand("settings", "Configure the bot ⚙️"),
        types.BotCommand("security", "Toggle group security mode 🔒")
    ]
    bot.set_my_commands(commands)

# ====================== MAIN MENU ======================
def main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    add_btn = types.InlineKeyboardButton(text="➕ Add Me to Group", url="https://t.me/manipulator_chat_ranking_bot?startgroup=start")
    settings_btn = types.InlineKeyboardButton(text="⚙️ Settings", callback_data="open_settings")
    owner_btn = types.InlineKeyboardButton(text="SUPPORT", url="https://t.me/manipulater_support")
    markup.add(add_btn)
    markup.add(settings_btn, owner_btn)
    return markup

# ====================== WELCOME MESSAGE ======================
@bot.message_handler(commands=['start'])
def welcome(message):
    if message.chat.type == 'private':
        photo_url = "https://instasize.com/p/d8a6ee46b4c5807bd1a2cbed95bd80376c559e38391e034dacb82f51b6e99153"
        caption = (
            "Hey **MANIPULATER**,\n"
            "This is **Manipulator Ranking Bot**! 👋\n\n"
            "Send messages, earn XP and climb the leaderboard! 🔥\n"
            "Add me to your group and compete with your friends 🏆"
        )
        markup = main_menu_markup()
        try:
            bot.send_photo(message.chat.id, photo=photo_url, caption=caption, parse_mode='Markdown', reply_markup=markup)
        except:
            bot.reply_to(message, "Hey! Welcome to Manipulator Ranking Bot 👇", reply_markup=markup)
    else:
        bot.reply_to(message, f"👋 Hello **{message.chat.title}**!\n\nEarn XP by sending messages and climb the leaderboard!", parse_mode='Markdown')

# ====================== SECURITY COMMAND ======================
@bot.message_handler(commands=['security'])
def security_command(message):
    if message.chat.type not in ['group', 'supergroup']:
        return bot.reply_to(message, "❌ Security command only works in groups!")
    
    if not is_admin(message.chat.id, message.from_user.id):
        return bot.reply_to(message, "❌ Only group admins can use /security command!")
    
    chat_id = message.chat.id
    if chat_id not in security_enabled:
        security_enabled[chat_id] = False
    
    security_enabled[chat_id] = not security_enabled[chat_id]
    status = "✅ ENABLED" if security_enabled[chat_id] else "❌ DISABLED"

    conn = sqlite3.connect('ranking.db')
    c = conn.cursor()
    enabled_val = 1 if security_enabled[chat_id] else 0
    c.execute("INSERT OR REPLACE INTO security_settings (chat_id, enabled) VALUES (?, ?)", (chat_id, enabled_val))
    conn.commit()
    conn.close()
    
    bot.reply_to(message, f"🔒 **GROUP SECURITY MODE:** {status}\n\n"
                         f"Blocked words: tos breaking word\n"
                         f"Bot {'Only tos breaking messages will be deleted ' if security_enabled[chat_id] else 'nothing'}.\n\n"
                         f"Note: Grant the bot 'Delete Messages' and 'Restrict Members' permissions to enable all features.")

# ====================== TOP GROUPS FUNCTION ======================
def get_top_groups(period="today"):
    conn = sqlite3.connect('ranking.db')
    c = conn.cursor()
    today_str = date.today().isoformat()
    
    if period == "today":
        date_filter = "dm.date = ?"
        params = (today_str,)
        total_query = "SELECT COALESCE(SUM(message_count), 0) FROM daily_messages WHERE date = ?"
        total_params = (today_str,)
    elif period == "week":
        start_date = (date.today() - timedelta(days=6)).isoformat()
        date_filter = "dm.date >= ?"
        params = (start_date,)
        total_query = "SELECT COALESCE(SUM(message_count), 0) FROM daily_messages WHERE date >= ?"
        total_params = (start_date,)
    else:  # overall
        date_filter = "1=1"
        params = ()
        total_query = "SELECT COALESCE(SUM(message_count), 0) FROM daily_messages"
        total_params = ()
    
    c.execute(f"""
        SELECT g.chat_id, g.title, SUM(dm.message_count) as total
        FROM daily_messages dm
        JOIN groups g ON dm.chat_id = g.chat_id
        WHERE {date_filter}
        GROUP BY g.chat_id, g.title
        ORDER BY total DESC
        LIMIT 10
    """, params)
    stats = c.fetchall()
    
    c.execute(total_query, total_params)
    total_msgs = c.fetchone()[0] or 0
    
    conn.close()
    return stats, total_msgs

# ====================== TOPGROUPS COMMAND ======================
@bot.message_handler(commands=['topgroups'])
def show_topgroups(message):
    stats, total_msgs = get_top_groups("today")
    
    if not stats:
        caption = "**MANIPULATER RANKING BOT**\n**GLOBAL GROUPS LEADERBOARD** 👥\n\n❌ No messages yet today!\nStart sending messages 🔥\n\n━━━━━━━━━━━━━━━━━━━━"
    else:
        text = "**TOP GROUPS today** 🌍\n\n"
        for i, (chat_id, title, msgs) in enumerate(stats, 1):
            text += f"{i}. **{title}** • `{msgs}` messages\n"
        text += f"\n📊 **Today messages:** `{total_msgs}`\n━━━━━━━━━━━━━━━━━━━━"
        caption = f"**MANIPULATER RANKING BOT**\n**GLOBAL GROUPS LEADERBOARD** 👥\n\n{text}"
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("📅 Today", callback_data="topgroups_today"),
        types.InlineKeyboardButton("📆 Week", callback_data="topgroups_week"),
  types.InlineKeyboardButton("🌍 Overall", callback_data="topgroups_overall")
    )
    
    try:
        bot.send_photo(message.chat.id, photo=LEADERBOARD_BANNER, caption=caption, parse_mode='Markdown', reply_markup=markup)
    except:
        bot.reply_to(message, caption, parse_mode='Markdown', reply_markup=markup)

def show_topgroups_data(call, period):
    stats, total_msgs = get_top_groups(period)
    
    if not stats:
        text = "❌ No messages yet!\n"
    else:
        period_text = "today" if period == "today" else "this week" if period == "week" else "overall"
        text = f"**TOP GROUPS {period_text}** 🌍\n\n"
        for i, (chat_id, title, msgs) in enumerate(stats, 1):
            text += f"{i}. **{title}** • `{msgs}` messages\n"
        
        total_label = "Today messages" if period == "today" else "This week messages" if period == "week" else "Total messages ever"
        text += f"\n📊 **{total_label}:** `{total_msgs}`\n━━━━━━━━━━━━━━━━━━━━"
    
    caption = f"**MANIPULATER RANKING BOT**\n**GLOBAL GROUPS LEADERBOARD** 👥\n\n{text}"
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("📅 Today", callback_data="topgroups_today"),
        types.InlineKeyboardButton("📆 Week", callback_data="topgroups_week"),
        types.InlineKeyboardButton("🌍 Overall", callback_data="topgroups_overall")
    )
    
    try:
        bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption=caption, parse_mode='Markdown', reply_markup=markup)
    except:
        bot.edit_message_text(caption, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=markup)

# ====================== TOP USERS FUNCTION (naya global top users) ======================
def get_top_users(period="overall"):
    conn = sqlite3.connect('ranking.db')
    c = conn.cursor()
    today_str = date.today().isoformat()
    
    if period == "today":
        c.execute("""
            SELECT u.user_id, u.name, SUM(dm.message_count) as total
            FROM daily_messages dm
            JOIN users u ON dm.user_id = u.user_id
            WHERE dm.date = ?
            GROUP BY u.user_id, u.name
            ORDER BY total DESC
            LIMIT 10
        """, (today_str,))
        stats = c.fetchall()
        total_query = "SELECT COALESCE(SUM(message_count), 0) FROM daily_messages WHERE date = ?"
        total_params = (today_str,)
    elif period == "week":
        start_date = (date.today() - timedelta(days=6)).isoformat()
        c.execute("""
            SELECT u.user_id, u.name, SUM(dm.message_count) as total
            FROM daily_messages dm
            JOIN users u ON dm.user_id = u.user_id
            WHERE dm.date >= ?
            GROUP BY u.user_id, u.name
            ORDER BY total DESC
            LIMIT 10
        """, (start_date,))
        stats = c.fetchall()
        total_query = "SELECT COALESCE(SUM(message_count), 0) FROM daily_messages WHERE date >= ?"
        total_params = (start_date,)
    else:  # overall (global)
        c.execute("""
            SELECT u.user_id, u.name, SUM(dm.message_count) as total
            FROM daily_messages dm
            JOIN users u ON dm.user_id = u.user_id
            GROUP BY u.user_id, u.name
            ORDER BY total DESC
            LIMIT 10
        """)
        stats = c.fetchall()
        total_query = "SELECT COALESCE(SUM(message_count), 0) FROM daily_messages"
        total_params = ()
    
    c.execute(total_query, total_params)
    total_msgs = c.fetchone()[0] or 0
    conn.close()
    return stats, total_msgs

# ====================== TOPUSERS COMMAND ======================
@bot.message_handler(commands=['topusers'])
def show_topusers(message):
    stats, total_msgs = get_top_users("overall")
    
    if not stats:
        caption = "**MANIPULATER RANKING BOT**\n**GLOBAL USERS LEADERBOARD** 🌍\n\n❌ No messages yet!\nStart sending messages 🔥\n\n━━━━━━━━━━━━━━━━━━━━"
    else:
        text = "**GLOBAL LEADERBOARD** 🌍\n\n"
        for i, (user_id, name, msgs) in enumerate(stats, 1):
            clickable = f"[{name}](tg://user?id={user_id})"
            text += f"{i}. {clickable} • `{msgs}` messages\n"
        text += f"\n📊 **Total messages:** `{total_msgs}`\n━━━━━━━━━━━━━━━━━━━━"
        caption = f"**MANIPULATER RANKING BOT**\n**GLOBAL USERS LEADERBOARD** 🌍\n\n{text}"
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("📅 Today", callback_data="topusers_today"),
        types.InlineKeyboardButton("📆 Week", callback_data="topusers_week"),
        types.InlineKeyboardButton("🌍 Overall", callback_data="topusers_overall")
    )
    
    try:
        bot.send_photo(message.chat.id, photo=LEADERBOARD_BANNER, caption=caption, parse_mode='Markdown', reply_markup=markup)
    except:
        bot.reply_to(message, caption, parse_mode='Markdown', reply_markup=markup)

def show_topusers_data(call, period):
    stats, total_msgs = get_top_users(period)
    
    if not stats:
        text = "❌ No messages yet!\n"
    else:
        period_text = "today" if period == "today" else "this week" if period == "week" else "overall"
        text = f"**GLOBAL LEADERBOARD {period_text.upper()}** 🌍\n\n"
        for i, (user_id, name, msgs) in enumerate(stats, 1):
            clickable = f"[{name}](tg://user?id={user_id})"
            text += f"{i}. {clickable} • `{msgs}` messages\n"
        
        total_label = "Today messages" if period == "today" else "This week messages" if period == "week" else "Total messages ever"
        text += f"\n📊 **{total_label}:** `{total_msgs}`\n━━━━━━━━━━━━━━━━━━━━"
    
    caption = f"**MANIPULATER RANKING BOT**\n**GLOBAL USERS LEADERBOARD** 🌍\n\n{text}"
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("📅 Today", callback_data="topusers_today"),
        types.InlineKeyboardButton("📆 Week", callback_data="topusers_week"),
        types.InlineKeyboardButton("🌍 Overall", callback_data="topusers_overall")
    )
    
    try:
        bot.edit_message_caption(call.message.chat.id, call.message.message_id, caption=caption, parse_mode='Markdown', reply_markup=markup)
    except:
        bot.edit_message_text(caption, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=markup)

# ====================== MESSAGE STATS ======================
def get_message_stats(chat_id, period="today"):
    conn = sqlite3.connect('ranking.db')
    c = conn.cursor()
    if period == "today":
        today_str = date.today().isoformat()
        c.execute("""
            SELECT u.user_id, u.name, SUM(dm.message_count) as msgs
            FROM daily_messages dm
            JOIN users u ON dm.user_id = u.user_id
            WHERE dm.chat_id = ? AND dm.date = ?
            GROUP BY u.user_id, u.name
            ORDER BY msgs DESC
            LIMIT 10
        """, (chat_id, today_str))
    else:
        start_date = (date.today() - timedelta(days=6)).isoformat()
        c.execute("""
            SELECT u.user_id, u.name, SUM(dm.message_count) as msgs
            FROM daily_messages dm
            JOIN users u ON dm.user_id = u.user_id
            WHERE dm.chat_id = ? AND dm.date >= ?
            GROUP BY u.user_id, u.name
            ORDER BY msgs DESC
            LIMIT 10
        """, (chat_id, start_date))
    stats = c.fetchall()
    conn.close()
    return stats

def make_clickable_name(user_id, name):
    return f"[{name}](tg://user?id={user_id})"

# ====================== PROFILE COMMAND ======================
@bot.message_handler(commands=['profile', 'stats', 'rank'])
def show_profile(message):
    user_id = message.from_user.id
    name = message.from_user.first_name

    conn = sqlite3.connect('ranking.db')
    c = conn.cursor()
    c.execute("SELECT xp, level FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()

    if not res:
        return bot.reply_to(message, "❌ No data found. Send some messages first to build your profile!")

    xp, level = res

    conn = sqlite3.connect('ranking.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE xp > ?", (xp,))
    global_rank = c.fetchone()[0] + 1
    conn.close()

    today_str = date.today().isoformat()
    week_start = (date.today() - timedelta(days=6)).isoformat()

    conn = sqlite3.connect('ranking.db')
    c = conn.cursor()
    c.execute("""SELECT COALESCE(SUM(message_count), 0) FROM daily_messages WHERE user_id = ? AND chat_id = ? AND date = ?""", (user_id, message.chat.id, today_str))
    today_msgs = c.fetchone()[0]

    c.execute("""SELECT COALESCE(SUM(message_count), 0) FROM daily_messages WHERE user_id = ? AND chat_id = ? AND date >= ?""", (user_id, message.chat.id, week_start))
    week_msgs = c.fetchone()[0]

    c.execute("SELECT COALESCE(SUM(message_count), 0) FROM daily_messages WHERE user_id = ?", (user_id,))
    global_msgs = c.fetchone()[0]
    conn.close()

    text = f"👤 **YOUR PROFILE**\n━━━━━━━━━━━━━━━━━━━━\n"
    text += f"• **Messages sent here:** `{today_msgs} (today: {today_msgs}, this week: {week_msgs})`\n"
    text += f"• **Messages sent globally:** `{global_msgs} (today: {today_msgs}, this week: {week_msgs})`\n"
    text += f"• **Position here:** `1° on 2 (today: 1°, this week: 1°)`\n"
    text += f"• **Global position:** `{global_rank} (today: {global_rank}, this week: {global_rank})`\n"
    text += f"━━━━━━━━━━━━━━━━━━━━\n"
    text += f"🆙 **Level:** `{level}`\n"
    text += f"⭐ **Total XP:** `{xp}`\n"
    text += f"📊 **Progress:** `{xp % 100}%` to next level\n"
    text += f"━━━━━━━━━━━━━━━━━━━━"

    photo_file_id = None
    try:
        photos = bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0 and photos.photos and photos.photos[0]:
            biggest_photo = max(photos.photos[0], key=lambda p: p.file_size)
            photo_file_id = biggest_photo.file_id
    except:
        pass

    try:
        if photo_file_id:
            bot.send_photo(message.chat.id, photo=photo_file_id, caption=text, parse_mode='Markdown')
        else:
            bot.reply_to(message, text, parse_mode='Markdown')
    except:
        bot.reply_to(message, text, parse_mode='Markdown')

# ====================== RANKINGS ======================
def show_rankings(message):
    if message.chat.type not in ['group', 'supergroup']:
        return bot.reply_to(message, "❌ This command only works in groups!")
    
    chat_id = message.chat.id
    stats = get_message_stats(chat_id, "today")

    # Header section
    header = "<b>MANIPULATER RANKING BOT</b>\n<b>GROUP LEADERBOARD</b> 🏆\n\n"
    footer = "\n━━━━━━━━━━━━━━━━━━━━"

    if not stats:
        caption = f"{header}❌ No messages yet today!\nStart sending messages 🔥{footer}"
    else:
        text = ""
        for i, (user_id, name, msgs) in enumerate(stats, 1):
            # HTML का उपयोग करके नाम को क्लिकेबल बनाना (आईडी नहीं दिखेगी)
            # यहाँ 'name' को escape करना जरूरी है ताकि नाम में < या > होने पर कोड न फटे
            safe_name = name.replace('<', '&lt;').replace('>', '&gt;')
            clickable = f'<a href="tg://user?id={user_id}">{safe_name}</a>'
            text += f"{i}. {clickable} • <code>{msgs} messages</code>\n"
            
        total_msgs = sum(msgs for _, _, msgs in stats)
        text += f"\n📊 <b>Total messages:</b> <code>{total_msgs}</code>"
        caption = f"{header}{text}{footer}"

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📅 Today", callback_data="ranking_today"),
        types.InlineKeyboardButton("📆 Week", callback_data="ranking_lastweek"),
        types.InlineKeyboardButton("🌍 Overall", callback_data="topgroups_overall")
    )

    try:
        # यहाँ parse_mode='HTML' कर दिया है क्योंकि यह Markdown से बेहतर काम करता है
        bot.send_photo(chat_id, photo=LEADERBOARD_BANNER, caption=caption, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        # अगर फोटो नहीं जाती तो टेक्स्ट मैसेज भेजें
        bot.reply_to(message, caption, parse_mode='HTML')


@bot.message_handler(commands=['hangman'])
def start_hangman(message):
    if message.chat.type not in ['group', 'supergroup']:
        return bot.reply_to(message, "❌ Hangman can only be played in groups!")
    chat_id = message.chat.id
    word = "apple"
    hangman_games[chat_id] = {
        "word": word,
        "guessed": set(),
        "wrong": 0,
        "current": ["_" if c.isalpha() else c for c in word]
    }
    text = "🕹️ **HANGMAN STARTED!** 🕹️\n\nGuess the fruit:\n" + " ".join(hangman_games[chat_id]["current"]) + "\n\nSend one letter (example: a)"
    bot.reply_to(message, text)

@bot.message_handler(commands=['settings'])
def settings_cmd(message):
    callback_query(None, is_cmd=True, msg=message)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call, is_cmd=False, msg=None):
    if (call and call.data == "open_settings") or is_cmd:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("🇮🇳 Hindi", callback_data="lang_hindi"))
        markup.add(types.InlineKeyboardButton("🇺🇸 English", callback_data="lang_english"))
        markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="back_to_main"))
        text = "⚙️ **Settings**\nChoose your language:"
        target_id = call.message.chat.id if call else msg.chat.id
        if is_cmd:
            bot.send_message(target_id, text, reply_markup=markup)
        else:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call and call.data in ["lang_english", "lang_hindi"]:
        lang = "English" if call.data == "lang_english" else "Hindi"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Back", callback_data="open_settings"))
        bot.edit_message_text(f"✅ Language updated to {lang}!", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call and call.data == "back_to_main":
        bot.edit_message_text("Hey! I am the Ranking Bot.", call.message.chat.id, call.message.message_id, reply_markup=main_menu_markup())

    elif call and call.data in ["ranking_today", "ranking_lastweek"]:
        period = "today" if call.data == "ranking_today" else "lastweek"
        show_ranking_data(call, period)
    
    elif call and call.data in ["topgroups_today", "topgroups_week", "topgroups_overall"]:
        period = "today" if call.data == "topgroups_today" else "week" if call.data == "topgroups_week" else "overall"
        show_topgroups_data(call, period)
    
    # Naya topusers callback
    elif call and call.data in ["topusers_today", "topusers_week", "topusers_overall"]:
        period = "today" if call.data == "topusers_today" else "week" if call.data == "topusers_week" else "overall"
        show_topusers_data(call, period)

# ====================== MAIN MESSAGE HANDLER ======================
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    
    # Group title update
    if message.chat.type in ['group', 'supergroup']:
        try:
            conn = sqlite3.connect('ranking.db')
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO groups (chat_id, title) VALUES (?, ?)", 
                      (chat_id, message.chat.title or f"Group {chat_id}"))
            conn.commit()
            conn.close()
        except:
            pass

    # ====================== SECURITY MODERATION ======================
    if message.chat.type in ['group', 'supergroup'] and chat_id in security_enabled and security_enabled[chat_id]:
        text_to_check = ""
        if message.text:
            text_to_check = message.text.lower()
        elif message.caption:
            text_to_check = message.caption.lower()

        if message.document and message.document.file_name:
            if text_to_check: text_to_check += " "
            text_to_check += message.document.file_name.lower()
        if message.sticker and message.sticker.emoji:
            if text_to_check: text_to_check += " "
            text_to_check += message.sticker.emoji.lower()
        if message.animation and getattr(message.animation, 'file_name', None):
            if text_to_check: text_to_check += " "
            text_to_check += message.animation.file_name.lower()

        if any(kw in text_to_check for kw in BLOCKED_KEYWORDS):
            user_id = message.from_user.id
            name = message.from_user.first_name
            clickable = make_clickable_name(user_id, name)
            
            is_severe = any(kw in text_to_check for kw in SEVERE_KEYWORDS)
            reason = "Contains blocked keywords (Telegram TOS violation)"

            deleted = False
            try:
                bot.delete_message(chat_id, message.message_id)
                deleted = True
            except:
                bot.send_message(chat_id, "⚠️ **MODERATION ALERT**\nBot 'Delete Messages' give the all admin rights! Please promote the bot.")

            notify = f"🚨 **TOS VIOLATION DETECTED!**\nMessage from {clickable} {'deleted' if deleted else 'detected'}.\nReason: {reason}"
            
            if is_severe:
                notify += "\n**Severe violation - User muted for 24 hours!**"
                try:
                    until = int(time.time()) + 86400
                    bot.restrict_chat_member(chat_id, user_id, can_send_messages=False, until_date=until)
                    notify += "\nUser successfully muted."
                except:
                    notify += "\n(Muting failed - bot needs 'Restrict Members' right)"

            bot.send_message(chat_id, notify, parse_mode='Markdown')
            return

    # ====================== NORMAL XP & HANGMAN ======================
    if message.chat.type in ['group', 'supergroup'] and not message.text.startswith('/'):
        user_id = message.from_user.id
        name = message.from_user.first_name
        xp_gain = random.randint(5, 15)

        conn = sqlite3.connect('ranking.db')
        c = conn.cursor()

        c.execute("SELECT xp, level FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        if row is None:
            c.execute("INSERT INTO users (user_id, name, xp, level) VALUES (?, ?, ?, ?)", (user_id, name, xp_gain, 1))
        else:
            new_xp = row[0] + xp_gain
            new_lvl = (new_xp // 100) + 1
            c.execute("UPDATE users SET xp=?, level=?, name=? WHERE user_id=?", (new_xp, new_lvl, name, user_id))
            if new_lvl > row[1]:
                clickable_name = f"[{name}](tg://user?id={user_id})"
                bot.send_message(
            chat_id, 
            f"🎊⚡ LEVEL UP!  **{clickable_name}** reached Level {new_lvl}!\n"
            f"🏆 Keep grinding & rule the leaderboard! 👑🔥",
            parse_mode="Markdown"
        )
        today_str = date.today().isoformat()
        c.execute("""INSERT INTO daily_messages (user_id, chat_id, date, message_count)
                     VALUES (?, ?, ?, 1)
                     ON CONFLICT(user_id, chat_id, date) 
                     DO UPDATE SET message_count = message_count + 1""", 
                  (user_id, chat_id, today_str))

        c.execute("SELECT SUM(message_count) FROM daily_messages WHERE chat_id=? AND date=?", (chat_id, today_str))
        total_today = c.fetchone()[0] or 0

        if total_today >= 500 and total_today % 500 == 0:
            bot.send_message(chat_id, f"🎉 **GROUP MILESTONE!** 🎉\nToday we reached **{total_today}** messages! Great job 🔥")

        conn.commit()
        conn.close()

    # Hangman Logic
    if chat_id in hangman_games:
        game = hangman_games[chat_id]
        guess = message.text.strip().lower()
        if len(guess) != 1 or not guess.isalpha():
            return
        if guess in game["guessed"]:
            return bot.reply_to(message, "❌ You already guessed this letter!")
        
        game["guessed"].add(guess)
        if guess in game["word"]:
            for i, char in enumerate(game["word"]):
                if char == guess:
                    game["current"][i] = guess
            bot.reply_to(message, f"✅ Correct! **{guess}**")
        else:
            game["wrong"] += 1
            bot.reply_to(message, f"❌ Wrong!")

        current_display = " ".join(game["current"])
        bot.send_message(chat_id, f"**Current:** {current_display}\nWrong: {game['wrong']}/6")

        if "_" not in game["current"]:
            bot.send_message(chat_id, f"🎉 **You won!** The word was: **{game['word']}** 🏆")
            del hangman_games[chat_id]
        elif game["wrong"] >= 6:
            bot.send_message(chat_id, f"😢 Game Over! The word was: **{game['word']}**")
            del hangman_games[chat_id]

# ====================== EDITED MESSAGE HANDLER ======================
@bot.edited_message_handler(func=lambda message: True)
def handle_edited_messages(message):
    chat_id = message.chat.id

    if message.chat.type in ['group', 'supergroup'] and chat_id in security_enabled and security_enabled[chat_id]:
        text_to_check = ""
        if message.text:
            text_to_check = message.text.lower()
        elif message.caption:
            text_to_check = message.caption.lower()

        if message.document and message.document.file_name:
            if text_to_check: text_to_check += " "
            text_to_check += message.document.file_name.lower()
        if message.sticker and message.sticker.emoji:
            if text_to_check: text_to_check += " "
            text_to_check += message.sticker.emoji.lower()
        if message.animation and getattr(message.animation, 'file_name', None):
            if text_to_check: text_to_check += " "
            text_to_check += message.animation.file_name.lower()

        if any(kw in text_to_check for kw in BLOCKED_KEYWORDS):
            user_id = message.from_user.id
            name = message.from_user.first_name
            clickable = make_clickable_name(user_id, name)
            
            is_severe = any(kw in text_to_check for kw in SEVERE_KEYWORDS)
            reason = "Contains blocked keywords (Telegram TOS violation)"

            deleted = False
            try:
                bot.delete_message(chat_id, message.message_id)
                deleted = True
            except:
                bot.send_message(chat_id, "⚠️ **MODERATION ALERT**\nBot 'Delete Messages' give the all admin rights! Please promote the bot.")

            notify = f"🚨 **TOS VIOLATION DETECTED!**\nMessage from {clickable} {'deleted' if deleted else 'detected'}.\nReason: {reason}"
            
            if is_severe:
                notify += "\n**Severe violation - User muted for 24 hours!**"
                try:
                    until = int(time.time()) + 86400
                    bot.restrict_chat_member(chat_id, user_id, can_send_messages=False, until_date=until)
                    notify += "\nUser successfully muted."
                except:
                    notify += "\n(Muting failed - bot needs 'Restrict Members' right)"

            bot.send_message(chat_id, notify, parse_mode='Markdown')
            return

if __name__ == "__main__":
    init_db()
    
    conn = sqlite3.connect('ranking.db')
    c = conn.cursor()
    c.execute("SELECT chat_id, enabled FROM security_settings")
    for row in c.fetchall():
        security_enabled[row[0]] = bool(row[1])
    conn.close()
    
    set_bot_menu()
    print("Bot is running... 🔥")
    keep_alive()
    bot.infinity_polling()
