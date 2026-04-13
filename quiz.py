import telebot
import time
import random
import threading
import json
import os

# ================== YAHAN APNA DATA DAALO ==================
TOKEN = "8740586204:AAHaVnVgj2WoTlk3Oqrxze13Jl4oyQk2_zc"          # BotFather se liya hua token

# Owner ka Telegram User ID (zaruri hai)
# @userinfobot ko message bhejo aur apna ID yahan daal do
OWNER_ID = 8259919292   # ←←← YAHAN APNA PERSONAL TELEGRAM USER ID DAAL DO

# Files
GROUPS_FILE = "active_groups.json"
SCORES_FILE = "scores.json"

# ================== QUESTIONS ==================
questions_list = [
    {
        "question": "What is the capital of Uttar Pradesh?",
        "answer": "lucknow",
        "options": ["lucknow", "kanpur", "varanasi", "allahabad"]
    },
    {
        "question": "Who is known as the Father of Indian Constitution?",
        "answer": "dr br ambedkar",
        "options": ["dr br ambedkar", "mahatma gandhi", "jawaharlal nehru", "sardar patel"]
    },
    {
        "question": "What is the chemical symbol for sodium?",
        "answer": "na",
        "options": ["na", "so", "ne", "mg"]
    },
    {
        "question": "What is the SI unit of electric current?",
        "answer": "ampere",
        "options": ["ampere", "volt", "ohm", "watt"]
    },
    {
        "question": "In which year was the Battle of Plassey fought?",
        "answer": "1757",
        "options": ["1757", "1764", "1857", "1947"]
    },
    {
        "question": "Who discovered gravity?",
        "answer": "isaac newton",
        "options": ["isaac newton", "albert einstein", "galileo", "thomas edison"]
    },
    {
        "question": "What is the national flower of India?",
        "answer": "lotus",
        "options": ["lotus", "rose", "sunflower", "marigold"]
    },
    {
        "question": "What is the pH value of pure water?",
        "answer": "7",
        "options": ["7", "0", "14", "5"]
    },
    {
        "question": "Who was the first woman Prime Minister of India?",
        "answer": "indira gandhi",
        "options": ["indira gandhi", "sonia gandhi", "pratibha patil", "sushma swaraj"]
    },
    {
        "question": "What is the largest planet in our solar system?",
        "answer": "jupiter",
        "options": ["jupiter", "saturn", "earth", "mars"]
    }
    # YAHAN AUR 700+ QUESTIONS ADD KARO
]

# Global variables
bot = telebot.TeleBot(TOKEN)
scores = {}                    
remaining_questions = []
current_question = None
answered_users = set()
GROUP_CHAT_IDS = []           # Active groups (verified)
PENDING_GROUPS = {}           # group_id : group_title  (verification ke liye wait)

def load_groups():
    global GROUP_CHAT_IDS
    if os.path.exists(GROUPS_FILE):
        try:
            with open(GROUPS_FILE, "r", encoding="utf-8") as f:
                GROUP_CHAT_IDS = json.load(f)
        except:
            GROUP_CHAT_IDS = []
    else:
        GROUP_CHAT_IDS = [-1003536569613]  # Default purana group

def save_groups():
    with open(GROUPS_FILE, "w", encoding="utf-8") as f:
        json.dump(GROUP_CHAT_IDS, f, ensure_ascii=False, indent=2)

def load_scores():
    global scores
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                scores = {int(k): v for k, v in data.items()}
        except:
            scores = {}
    else:
        scores = {}

def save_scores():
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)

def get_username(user):
    if user.username:
        return f"@{user.username}"
    return user.first_name or "User"

def get_clickable_mention(user):
    name = get_username(user)
    if user.username:
        return name
    else:
        return f"[{name}](tg://user?id={user.id})"

# ================== SINGLE GROUP ME PUZZLE BHEJNE KA FUNCTION (Verification ke baad) ==================
def send_question_to(chat_id):
    """Sirf ek specific group mein ek puzzle bhejta hai"""
    if not remaining_questions:
        remaining_questions.extend(questions_list.copy())
        random.shuffle(remaining_questions)

    q = remaining_questions.pop(0)
    answered_users.clear()   # Reset for this question

    options = q['options'].copy()
    random.shuffle(options)

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    for opt in options:
        markup.add(telebot.types.InlineKeyboardButton(
            opt.capitalize(), 
            callback_data=f"answer:{opt.lower()}"
        ))

    message_text = f"""🧠 **NEW QUIZ TIME!** (1 minute only)

{q['question']}

Choose the correct answer below 👇"""

    try:
        bot.send_message(
            chat_id, 
            message_text, 
            parse_mode='Markdown',
            reply_markup=markup
        )
        print(f"✅ First puzzle sent to new group {chat_id}")
    except Exception as e:
        print(f"Error sending to {chat_id}: {e}")

# ================== SAB GROUPS ME PUZZLE BHEJNE KA FUNCTION (Normal scheduler) ==================
def broadcast_question():
    global current_question, answered_users, remaining_questions

    if not remaining_questions:
        remaining_questions = questions_list.copy()
        random.shuffle(remaining_questions)

    current_question = remaining_questions.pop(0)
    answered_users = set()

    options = current_question['options'].copy()
    random.shuffle(options)

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    for opt in options:
        markup.add(telebot.types.InlineKeyboardButton(
            opt.capitalize(), 
            callback_data=f"answer:{opt.lower()}"
        ))

    message_text = f"""🧠 **NEW QUIZ TIME!** (1 minute only)

{current_question['question']}

Choose the correct answer below 👇"""

    for chat_id in GROUP_CHAT_IDS:
        try:
            bot.send_message(
                chat_id, 
                message_text, 
                parse_mode='Markdown',
                reply_markup=markup
            )
        except Exception as e:
            print(f"Error sending to {chat_id}: {e}")

def end_question():
    global current_question
    if current_question:
        correct_ans = current_question['answer'].capitalize()
        for chat_id in GROUP_CHAT_IDS:
            try:
                bot.send_message(
                    chat_id,
                    f"⏰ **Time's up!**\n\nCorrect answer: **{correct_ans}**",
                    parse_mode='Markdown'
                )
            except:
                pass
    current_question = None

# ================== NEW GROUP DETECTION + VERIFY ==================
@bot.my_chat_member_handler()
def bot_added_to_group(update):
    chat = update.chat
    new_member = update.new_chat_member
    old_member = update.old_chat_member

    if (new_member.user.id == bot.get_me().id and 
        new_member.status in ['member', 'administrator'] and 
        old_member.status not in ['member', 'administrator']):

        group_id = chat.id
        group_title = chat.title or "Unknown Group"

        # Agar already active hai to kuch mat karo
        if group_id in GROUP_CHAT_IDS:
            return

        # Pending mein daal do
        PENDING_GROUPS[group_id] = group_title

        # Owner ko DM mein VERIFY button bhejo
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(
            "✅ Enable Quiz in this group", 
            callback_data=f"verify:{group_id}"
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            "❌ Ignore / Don't enable", 
            callback_data=f"ignore:{group_id}"
        ))

        try:
            bot.send_message(
                OWNER_ID,
                f"🆕 **Bot added to a NEW group!**\n\n"
                f"**Group Name:** {group_title}\n"
                f"**Chat ID:** `{group_id}`\n\n"
                f"Kya is group mein Quiz shuru karna hai?",
                parse_mode='Markdown',
                reply_markup=markup
            )
            print(f"📨 Verification request sent to owner for group {group_id}")
        except Exception as e:
            print(f"Could not notify owner: {e}")

# Verification handler (DM se button click)
@bot.callback_query_handler(func=lambda call: call.data.startswith("verify:") or call.data.startswith("ignore:"))
def handle_verification(call):
    if call.from_user.id != OWNER_ID:
        bot.answer_callback_query(call.id, "Sirf owner hi verify kar sakta hai!", show_alert=True)
        return

    action, group_id_str = call.data.split(":", 1)
    group_id = int(group_id_str)
    group_title = PENDING_GROUPS.get(group_id, "Unknown Group")

    bot.answer_callback_query(call.id)

    if action == "verify":
        # Active list mein add kar do
        if group_id not in GROUP_CHAT_IDS:
            GROUP_CHAT_IDS.append(group_id)
            save_groups()

        # Pending se hata do
        PENDING_GROUPS.pop(group_id, None)

        bot.send_message(
            OWNER_ID,
            f"✅ **Group activated!**\n\n"
            f"**{group_title}** mein ab Quiz shuru ho gaya hai.\n"
            f"Pehla puzzle turant bhej diya gaya hai.",
            parse_mode='Markdown'
        )

        # Turant ek puzzle bhej do sirf is group mein
        send_question_to(group_id)

    else:  # ignore
        PENDING_GROUPS.pop(group_id, None)
        bot.send_message(
            OWNER_ID,
            f"❌ **Group ignored.**\n\n{group_title} mein quiz nahi chalega.",
            parse_mode='Markdown'
        )

# Callback handler for quiz answers (same as before)
@bot.callback_query_handler(func=lambda call: call.data.startswith("answer:"))
def handle_callback(call):
    global current_question, answered_users

    if not current_question:
        bot.answer_callback_query(call.id, "⏰ Time's up!", show_alert=True)
        return

    user_id = call.from_user.id
    user = call.from_user
    given_answer = call.data.split(":", 1)[1]

    if user_id in answered_users:
        bot.answer_callback_query(call.id, "❗ You have already answered!", show_alert=True)
        return

    answered_users.add(user_id)

    correct_answer = current_question['answer'].lower()
    correct_display = current_question['answer'].capitalize()

    if user_id not in scores:
        scores[user_id] = {"score": 0, "name": get_username(user)}
    else:
        scores[user_id]["name"] = get_username(user)

    clickable_name = get_clickable_mention(user)

    if given_answer == correct_answer:
        scores[user_id]["score"] += 1
        result_text = f"✅ **Correct Answer!** 🎉\n{clickable_name} +1 star"
        alert_text = "Correct! 🎉"
    else:
        scores[user_id]["score"] -= 1
        result_text = f"❌ **Wrong Answer!**\n{clickable_name} -1 star\n\n**Correct Answer:** {correct_display}"
        alert_text = "Wrong!"

    bot.answer_callback_query(call.id, alert_text, show_alert=False)

    for chat_id in GROUP_CHAT_IDS:
        try:
            bot.send_message(
                chat_id,
                f"{result_text}\n**Total stars:** {scores[user_id]['score']} ⭐",
                parse_mode='Markdown'
            )
        except:
            pass

    save_scores()

# Leaderboard & My Stars (same)
@bot.message_handler(commands=['leaderboard'])
def show_leaderboard(message):
    if message.chat.id not in GROUP_CHAT_IDS:
        return
    # ... (same code as before)

@bot.message_handler(commands=['mystars'])
def my_stars(message):
    if message.chat.id not in GROUP_CHAT_IDS:
        return
    # ... (same code as before)

# Scheduler - har 1 ghante mein sab active groups mein puzzle
def question_scheduler():
    time.sleep(5)
    while True:
        broadcast_question()
        time.sleep(3600)

# Bot start
if __name__ == "__main__":
    load_groups()
    load_scores()
    remaining_questions = questions_list.copy()
    random.shuffle(remaining_questions)

    print("🚀 Quiz Bot Started with Verification System!")
    print("Naye group mein bot add karo → Owner ko DM mein Verify button aayega")
    print("Verify karte hi us group mein turant ek puzzle bhej diya jayega")
    print("Baaki sab groups ke saath 1 hour schedule same rahega")

    scheduler_thread = threading.Thread(target=question_scheduler, daemon=True)
    scheduler_thread.start()

    bot.infinity_polling(allowed_updates=['message', 'callback_query', 'my_chat_member'])
