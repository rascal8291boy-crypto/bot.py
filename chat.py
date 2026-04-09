import telebot
import sqlite3
import random
from telebot import types
from datetime import date, timedelta

API_TOKEN = '8740586204:AAGPGB9L9hegac3Kz0kX_bWlshHruBoAB1I'
bot = telebot.TeleBot(API_TOKEN)

# Hangman game states
hangman_games = {}

# Hangman ASCII stages
HANGMAN_STAGES = [
    """+---+\n|   |\n    |\n    |\n    |\n    |\n=========""",
    """+---+\n|   |\nO   |\n    |\n    |\n    |\n=========""",
    """+---+\n|   |\nO   |\n|   |\n    |\n    |\n=========""",
    """+---+\n|   |\nO   |\n/|   |\n    |\n    |\n=========""",
    """+---+\n|   |\nO   |\n/|\\  |\n    |\n    |\n=========""",
    """+---+\n|   |\nO   |\n/|\\  |\n/    |\n    |\n=========""",
    """+---+\n|   |\nO   |\n/|\\  |\n/ \\  |\n    |\n========="""
]

# Word list for Hangman
WORDS = ["apple", "banana", "mango", "orange", "grape", "pineapple", "cherry", "lemon", "watermelon", "strawberry", "peach", "kiwi", "melon", "coconut", "papaya"]

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
    conn.commit()
    conn.close()

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
        types.BotCommand("ranking", "Today & Last Week Message Ranking 📊")
    ]
    bot.set_my_commands(commands)

# ====================== MAIN MENU ======================
def main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    add_btn = types.InlineKeyboardButton(text="➕ Add Me to Group", url="https://t.me/manipulator_chat_ranking_bot?startgroup=start")
    settings_btn = types.InlineKeyboardButton(text="⚙️ Settings", callback_data="open_settings")
    owner_btn = types.InlineKeyboardButton(text="👤 Owner", url="tg://openmessage?user_id=8259919292")
    markup.add(add_btn)
    markup.add(settings_btn, owner_btn)
    return markup

# ====================== WELCOME MESSAGE (UPDATED) ======================
@bot.message_handler(commands=['start'])
def welcome(message):
    if message.chat.type == 'private':
        photo_url = "https://kommodo.ai/i/Gkpo2cF3C64NabDJdeoY"   # Your anime picture
        
        caption = (
            "Hey **MANIPULATER**,\n"
            "This is **Manipulator Ranking Bot**! 👋\n\n"
            "Messages bhejo, XP kamao aur leaderboard pe climb karo! 🔥\n"
            "Group mein add karke apne doston ke saath compete karo 🏆"
        )
        
        markup = main_menu_markup()
        
        try:
            bot.send_photo(
                message.chat.id,
                photo=photo_url,
                caption=caption,
                parse_mode='Markdown',
                reply_markup=markup
            )
        except:
            # Agar photo na chale to text fallback
            bot.reply_to(message, "Hey! Welcome to Manipulator Ranking Bot 👇", reply_markup=markup)
    
    else:
        bot.reply_to(message, f"👋 Hello **{message.chat.title}**!\n\nEarn XP by sending messages and climb the leaderboard!", parse_mode='Markdown')


# ====================== MESSAGE STATS ======================
def get_message_stats(chat_id, period="today"):
    conn = sqlite3.connect('ranking.db')
    c = conn.cursor()
    
    if period == "today":
        today_str = date.today().isoformat()
        c.execute("""
            SELECT u.name, SUM(dm.message_count) as msgs
            FROM daily_messages dm
            JOIN users u ON dm.user_id = u.user_id
            WHERE dm.chat_id = ? AND dm.date = ?
            GROUP BY u.user_id, u.name
            ORDER BY msgs DESC
            LIMIT 10
        """, (chat_id, today_str))
    else:  # last week
        start_date = (date.today() - timedelta(days=6)).isoformat()
        c.execute("""
            SELECT u.name, SUM(dm.message_count) as msgs
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

# ====================== SHOW RANKING ======================
def show_ranking_data(obj, period="today"):
    if hasattr(obj, 'message'):   # CallbackQuery
        message = obj.message
        chat_id = message.chat.id
        message_id = message.message_id
        is_edit = True
    else:                         # Normal Message
        message = obj
        chat_id = message.chat.id
        message_id = None
        is_edit = False

    chat_title = message.chat.title or "Group"
    stats = get_message_stats(chat_id, period)

    if not stats:
        text = f"📊 **{period.upper()} MESSAGE RANKING**\n\n❌ Aaj koi message nahi mila!\nMessages bhejo 🔥"
    else:
        text = f"🏆 **{period.upper()} MESSAGE RANKING** 🏆\n👥 **{chat_title}**\n━━━━━━━━━━━━━━━━━━━━\n\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, (name, msgs) in enumerate(stats, 1):
            medal = medals[i-1] if i <= 3 else f"{i}."
            text += f"{medal} **{name}**\n   💬 `{msgs}` messages\n\n"
        
        total = sum(msgs for _, msgs in stats)
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += f"📊 **Total Messages:** `{total}`\n"

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📅 Today", callback_data="ranking_today"),
        types.InlineKeyboardButton("📆 Last Week", callback_data="ranking_lastweek")
    )

    if is_edit:
        bot.edit_message_text(text, chat_id, message_id, parse_mode='Markdown', reply_markup=markup)
    else:
        bot.reply_to(message, text, parse_mode='Markdown', reply_markup=markup)

# ====================== OTHER COMMANDS ======================
@bot.message_handler(commands=['profile', 'stats', 'rank'])
def show_profile(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('ranking.db')
    c = conn.cursor()
    c.execute("SELECT xp, level FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    
    if res:
        xp, level = res
        c.execute("SELECT COUNT(*) FROM users WHERE xp > ?", (xp,))
        global_rank = c.fetchone()[0] + 1
        conn.close()

        text = f"👤 **{message.from_user.first_name}'s Profile**\n━━━━━━━━━━━━━━━━━━━━\n🌍 **Global Rank:** #{global_rank}\n🆙 **Level:** `{level}`\n⭐ **Total XP:** `{xp}`\n📊 **Progress:** `{xp % 100}%`\n━━━━━━━━━━━━━━━━━━━━"
        bot.reply_to(message, text, parse_mode='Markdown')
    else:
        conn.close()
        bot.reply_to(message, "❌ No data found. Send some messages first!")

@bot.message_handler(commands=['rankings'])
def show_rankings(message):
    if message.chat.type not in ['group', 'supergroup']:
        return bot.reply_to(message, "❌ Ye command sirf groups mein chalti hai!")
    conn = sqlite3.connect('ranking.db')
    c = conn.cursor()
    c.execute("SELECT name, xp, level FROM users ORDER BY xp DESC LIMIT 10")
    users = c.fetchall()
    conn.close()

    text = "🏆 **GROUP LEADERBOARD** 🏆\n━━━━━━━━━━━━━━━━━━━━\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (name, xp, level) in enumerate(users, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        text += f"{medal} **{name}**\n   Level `{level}` • `{xp}` XP\n\n"
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['ranking'])
def show_ranking(message):
    if message.chat.type not in ['group', 'supergroup']:
        return bot.reply_to(message, "❌ Ye command sirf groups mein chalti hai!")
    show_ranking_data(message, "today")

@bot.message_handler(commands=['hangman'])
def start_hangman(message):
    if message.chat.type not in ['group', 'supergroup']:
        return bot.reply_to(message, "❌ Hangman sirf groups mein khela ja sakta hai!")
    chat_id = message.chat.id
    word = random.choice(WORDS).lower()
    hangman_games[chat_id] = {
        "word": word,
        "guessed": set(),
        "wrong": 0,
        "current": ["_" if c.isalpha() else c for c in word]
    }
    text = "🕹️ **HANGMAN STARTED!** 🕹️\n\nGuess the fruit:\n" + " ".join(hangman_games[chat_id]["current"]) + "\n\nEk letter bhejo (jaise: a)"
    bot.reply_to(message, text)

@bot.message_handler(commands=['settings'])
def settings_cmd(message):
    if message.chat.type != 'private':
        return bot.reply_to(message, "⚙️ Settings sirf private chat mein khol sakte hain.")
    callback_query(None, is_cmd=True, msg=message)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call, is_cmd=False, msg=None):
    if (call and call.data == "open_settings") or is_cmd:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("🇮🇳 Hindi", callback_data="lang_done"))
        markup.add(types.InlineKeyboardButton("🇺🇸 English", callback_data="lang_done"))
        markup.add(types.InlineKeyboardButton("⬅️ Back", callback_data="back_to_main"))
        text = "⚙️ **Settings**\nApni bhasha chunein:"
        target_id = call.message.chat.id if call else msg.chat.id
        target_mid = call.message.message_id if call else None
        if is_cmd:
            bot.send_message(target_id, text, reply_markup=markup)
        else:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call and call.data == "lang_done":
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ Back", callback_data="open_settings"))
        bot.edit_message_text("✅ Language updated!", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call and call.data == "back_to_main":
        bot.edit_message_text("Hey! Main Ranking Bot hoon.", call.message.chat.id, call.message.message_id, reply_markup=main_menu_markup())

    elif call and call.data in ["ranking_today", "ranking_lastweek"]:
        period = "today" if call.data == "ranking_today" else "lastweek"
        show_ranking_data(call, period)

# ====================== MAIN MESSAGE HANDLER ======================
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id

    if message.chat.type in ['group', 'supergroup'] and not message.text.startswith('/'):
        user_id = message.from_user.id
        name = message.from_user.first_name
        xp_gain = random.randint(5, 15)

        conn = sqlite3.connect('ranking.db')
        c = conn.cursor()

        # XP System
        c.execute("SELECT xp, level FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        if row is None:
            c.execute("INSERT INTO users (user_id, name, xp, level) VALUES (?, ?, ?, ?)", (user_id, name, xp_gain, 1))
        else:
            new_xp = row[0] + xp_gain
            new_lvl = (new_xp // 100) + 1
            c.execute("UPDATE users SET xp=?, level=?, name=? WHERE user_id=?", (new_xp, new_lvl, name, user_id))
            if new_lvl > row[1]:
                bot.send_message(chat_id, f"🎊 **{name}**, Level **{new_lvl}** up ho gaya! 🔥")

        # Daily Message Count
        today_str = date.today().isoformat()
        c.execute("""INSERT INTO daily_messages (user_id, chat_id, date, message_count)
                     VALUES (?, ?, ?, 1)
                     ON CONFLICT(user_id, chat_id, date) 
                     DO UPDATE SET message_count = message_count + 1""", 
                  (user_id, chat_id, today_str))

        # Milestone Announcement
        c.execute("SELECT SUM(message_count) FROM daily_messages WHERE chat_id=? AND date=?", (chat_id, today_str))
        total_today = c.fetchone()[0] or 0

        if total_today >= 500 and total_today % 500 == 0:
            bot.send_message(chat_id, f"🎉 **GROUP MILESTONE!** 🎉\nAaj **{total_today}** messages ho gaye! Bahut badhiya 🔥")

        conn.commit()
        conn.close()

    # Hangman Logic
    if chat_id in hangman_games:
        game = hangman_games[chat_id]
        guess = message.text.strip().lower()
        if len(guess) != 1 or not guess.isalpha():
            return
        if guess in game["guessed"]:
            return bot.reply_to(message, "❌ Ye letter pehle guess kar chuke ho!")
        
        game["guessed"].add(guess)
        if guess in game["word"]:
            for i, char in enumerate(game["word"]):
                if char == guess:
                    game["current"][i] = guess
            bot.reply_to(message, f"✅ Sahi! **{guess}**")
        else:
            game["wrong"] += 1
            bot.reply_to(message, f"❌ Galat!\n{HANGMAN_STAGES[game['wrong']]}")

        current_display = " ".join(game["current"])
        bot.send_message(chat_id, f"**Current:** {current_display}\nGalat: {game['wrong']}/6")

        if "_" not in game["current"]:
            bot.send_message(chat_id, f"🎉 **Jeet gaye!** Word tha: **{game['word']}** 🏆")
            del hangman_games[chat_id]
        elif game["wrong"] >= 6:
            bot.send_message(chat_id, f"😢 Game Over! Word tha: **{game['word']}**")
            del hangman_games[chat_id]

if __name__ == "__main__":
    init_db()
    set_bot_menu()
    print("Bot is running... 🔥")
    bot.infinity_polling()
