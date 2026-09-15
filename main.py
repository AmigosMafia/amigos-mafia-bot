import telebot
import random
import time
from threading import Thread
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

# ----------------- SOZLAMALAR -----------------
BOT_TOKEN = "8717794353:AAGPFmf1EiFs1oAJCuv3n2rKvZv47Z0IuKs"
BOT_USERNAME = "Amigos_Mafia_bot" 

bot = telebot.TeleBot(BOT_TOKEN)

# Ma'lumotlar bazasi
games = {}
users_db = {}

def setup_bot_commands():
    commands = [
        BotCommand("start", "O'yinni boshlash / Botni ishga tushirish"),
        BotCommand("game", "Yangi o'yin yaratish"),
        BotCommand("roles", "O'yin rollarini ko'rish"),
        BotCommand("profile", "Sizning profilingiz va statistikangiz"),
        BotCommand("pay", "Pul o'tkazish (reply orqali)"),
        BotCommand("give", "Olmos o'tkazish (reply orqali)"),
        BotCommand("leave", "O'yindan chiqish"),
        BotCommand("stop", "O'yinni to'xtatish")
    ]
    try:
        bot.set_my_commands(commands)
    except Exception as e:
        print(f"Menyu sozlashda xatolik: {e}")

def safe_answer_callback(call_id, text="", show_alert=False):
    try:
        bot.answer_callback_query(call_id, text=text, show_alert=show_alert)
    except Exception:
        pass

def get_or_create_user(user_id, name):
    if user_id not in users_db:
        users_db[user_id] = {
            "name": name,
            "coins": 100,
            "gems": 0,
            "games": 0,
            "wins": 0
        }
    return users_db[user_id]


# ----------------- BUYRUQLAR -----------------

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    get_or_create_user(user_id, user_name)
    
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("join_"):
        chat_id = int(args[1].replace("join_", ""))
        
        if chat_id in games and games[chat_id]["is_registration"]:
            game = games[chat_id]
            if user_id not in game["players"]:
                game["players"][user_id] = user_name
                
                players_list = "\n".join([f"• {name}" for name in game["players"].values()])
                count = len(game["players"])
                
                new_text = (
                    f"✨ **YANGI O'YIN BOSHLANDI!** ✨\n\n"
                    f"🎮 **Rejim:** Classic\n"
                    f"🚀 Shaharni mafiyadan tozalash vaqti keldi! O'yinga qo'shiling va o'z mahoratingizni ko'rsating!\n\n"
                    f"**Ro'yxatdagi o'yinchilar ({count}):**\n{players_list}"
                )
                
                markup = InlineKeyboardMarkup()
                join_url = f"https://t.me/{BOT_USERNAME}?start=join_{chat_id}"
                join_btn = InlineKeyboardButton("🎮 Qo'shilish", url=join_url)
                start_btn = InlineKeyboardButton("🚀 O'yinni boshlash", callback_data=f"start_game_{chat_id}")
                markup.add(join_btn)
                markup.add(start_btn)
                
                try:
                    bot.edit_message_text(new_text, chat_id, game["message_id"], parse_mode="Markdown", reply_markup=markup)
                except Exception:
                    pass
                
                markup_pm = InlineKeyboardMarkup()
                markup_pm.add(InlineKeyboardButton("🟢 Guruhga o'tish", url=f"https://t.me/c/{str(chat_id).replace('-100', '')}"))
                bot.send_message(user_id, "✅ **Siz o'yinga muvaffaqiyatli qo'shildingiz!**", parse_mode="Markdown", reply_markup=markup_pm)
                return
            else:
                bot.send_message(user_id, "ℹ️ Siz allaqachon ushbu o'yinga qo'shilgansiz!")
                return
        else:
            bot.send_message(user_id, "❌ Afsuski, ro'yxatga olish tugagan yoki o'yin topilmadi.")
            return

    bot.send_message(
        user_id, 
        f"Salom, **{user_name}**! Amigos Mafia botiga xush kelibsiz! 🎲\n\n"
        "O'yinni boshlash uchun botni guruhga qo'shing va guruhda `/game` buyrug'ini yuboring.\n"
        "Menyu va rollar haqida bilish uchun `/roles` va `/profile` buyruqlaridan foydalaning.",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['game'])
def start_game_registration(message):
    if message.chat.type in ['group', 'supergroup']:
        chat_id = message.chat.id
        
        markup = InlineKeyboardMarkup()
        join_url = f"https://t.me/{BOT_USERNAME}?start=join_{chat_id}"
        join_btn = InlineKeyboardButton("🎮 Qo'shilish", url=join_url)
        start_btn = InlineKeyboardButton("🚀 O'yinni boshlash", callback_data=f"start_game_{chat_id}")
        markup.add(join_btn)
        markup.add(start_btn)
        
        msg = bot.send_message(
            chat_id, 
            "✨ **YANGI O'YIN BOSHLANDI!** ✨\n\n"
            "🎮 **Rejim:** Classic\n"
            "🚀 Shaharni mafiyadan tozalash vaqti keldi! O'yinga qo'shiling va o'z mahoratingizni ko'rsating!\n\n"
            "👇 **Qo'shilish uchun pastdagi tugmani bosing:**\n\n"
            "**Ro'yxatdagilar (0):**\n_Hali hech kim qo'shilmadi_",
            parse_mode="Markdown",
            reply_markup=markup
        )
        
        games[chat_id] = {
            "players": {},            
            "is_registration": True,  
            "message_id": msg.message_id,
            "roles": {},              
            "night_actions": {},      
            "votes": {}               
        }
    else:
        bot.send_message(message.chat.id, "⚠️ O'yinni faqat guruhda `/game` buyrug'i orqali yaratishingiz mumkin!")

@bot.message_handler(commands=['profile'])
def profile_cmd(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    u = get_or_create_user(user_id, user_name)
    
    text = (
        f"👤 **{u['name']} profili**\n\n"
        f"💵 **Dollar:** {u['coins']}\n"
        f"💎 **Olmos:** {u['gems']}\n\n"
        f"🛡 **Himoyalar:** Yo'q\n"
        f"📊 **Statistika:**\n"
        f"🎯 G'alabalar: {u['wins']}\n"
        f"🎲 Jami o'yinlar: {u['games']}\n\n"
        f"🃏 **Faol rollar:** Yo'q"
    )
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🛒 Do'kon", callback_data="shop"), InlineKeyboardButton("💵 Xarid qilish", callback_data="buy_coins"))
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['roles'])
def roles_cmd(message):
    text = (
        "📜 **Amigos Mafia: O'yin Rollari**\n\n"
        "🕶 **Mafia** — Tinch aholini yo'qotadi va tuni bilan boshqaradi.\n"
        "🕵️‍♂️ **Detektiv** — Har tun bir kishining rolini tekshiradi.\n"
        "👨‍⚕️ **Shifokor** — Har tun bir kishini mafiyadan qutqaradi.\n"
        "👨‍🌾 **Tinch aholi** — Kunduzi ovoz berish orqali mafiyani aniqlaydi."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['leave'])
def leave_cmd(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if chat_id in games and games[chat_id]["is_registration"]:
        if user_id in games[chat_id]["players"]:
            del games[chat_id]["players"][user_id]
            bot.send_message(chat_id, "✅ Siz o'yindan chiqdingiz.")
        else:
            bot.send_message(chat_id, "Siz hali ro'yxatdan o'tmagansiz.")
    else:
        bot.send_message(chat_id, "Hozirda ro'yxatga olish jarayoni ketmayapti.")

@bot.message_handler(commands=['stop'])
def stop_cmd(message):
    chat_id = message.chat.id
    if chat_id in games:
        del games[chat_id]
        bot.send_message(chat_id, "🛑 **O'yin to'xtatildi.**")
    else:
        bot.send_message(chat_id, "Aktiv o'yin topilmadi.")

@bot.message_handler(commands=['pay'])
def pay_coins_cmd(message):
    user_id = message.from_user.id
    sender = get_or_create_user(user_id, message.from_user.first_name)
    
    if not message.reply_to_message:
        bot.reply_to(
            message, 
            "⚠️ Pul o'tkazish uchun biror foydalanuvchining xabariga **javob (reply)** qilib yozing.\n"
            "Masalan: `/pay 50`", 
            parse_mode="Markdown"
        )
        return
        
    target_user = message.reply_to_message.from_user
    
    if target_user.is_bot:
        bot.reply_to(message, "❌ Botlarga pul o'tkaza olmaysiz!")
        return
        
    if target_user.id == user_id:
        bot.reply_to(message, "❌ O'zingizga pul o'tkaza olmaysiz!")
        return
        
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(message, "⚠️ Summani to'g'ri kiriting!\nMasalan: `/pay 50`", parse_mode="Markdown")
        return
        
    amount = int(args[1])
    if amount <= 0:
        bot.reply_to(message, "⚠️ Noldan katta summa kiriting!")
        return
        
    if sender["coins"] < amount:
        bot.reply_to(message, f"❌ Hisobingizda yetarli pul yo'q!\nSizda: **{sender['coins']}** dollar bor.", parse_mode="Markdown")
        return
        
    receiver = get_or_create_user(target_user.id, target_user.first_name)
    
    sender["coins"] -= amount
    receiver["coins"] += amount
    
    bot.reply_to(
        message, 
        f"💸 **PUL O'TKAZILDI!**\n\n"
        f"👤 **Yuboruvchi:** {message.from_user.first_name}\n"
        f"👤 **Qabul qiluvchi:** {target_user.first_name}\n"
        f"💵 **Summa:** {amount} dollar\n\n"
        f"Sizning balansingiz: **{sender['coins']}** dollar",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['give'])
def give_gems_cmd(message):
    user_id = message.from_user.id
    sender = get_or_create_user(user_id, message.from_user.first_name)
    
    if not message.reply_to_message:
        bot.reply_to(
            message, 
            "⚠️ Olmos o'tkazish uchun biror foydalanuvchining xabariga **javob (reply)** qilib yozing.\n"
            "Masalan: `/give 5`", 
            parse_mode="Markdown"
        )
        return
        
    target_user = message.reply_to_message.from_user
    
    if target_user.is_bot:
        bot.reply_to(message, "❌ Botlarga olmos o'tkaza olmaysiz!")
        return
        
    if target_user.id == user_id:
        bot.reply_to(message, "❌ O'zingizga olmos o'tkaza olmaysiz!")
        return
        
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(message, "⚠️ Olmos miqdorini to'g'ri kiriting!\nMasalan: `/give 5`", parse_mode="Markdown")
        return
        
    amount = int(args[1])
    if amount <= 0:
        bot.reply_to(message, "⚠️ Noldan katta miqdor kiriting!")
        return
        
    if sender["gems"] < amount:
        bot.reply_to(message, f"❌ Hisobingizda yetarli olmos yo'q!\nSizda: **{sender['gems']}** olmos bor.", parse_mode="Markdown")
        return
        
    receiver = get_or_create_user(target_user.id, target_user.first_name)
    
    sender["gems"] -= amount
    receiver["gems"] += amount
    
    bot.reply_to(
        message, 
        f"💎 **OLMOS O'TKAZILDI!**\n\n"
        f"👤 **Yuboruvchi:** {message.from_user.first_name}\n"
        f"👤 **Qabul qiluvchi:** {target_user.first_name}\n"
        f"💎 **Miqdor:** {amount} olmos\n\n"
        f"Sizning balansingiz: **{sender['gems']}** olmos",
        parse_mode="Markdown"
    )


# ----------------- CALLBACK HANDLER -----------------

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if call.data.startswith("start_game_"):
        chat_id = int(call.data.replace("start_game_", ""))
        
        if chat_id not in games:
            safe_answer_callback(call.id, "O'yin topilmadi.", show_alert=True)
            return
            
        game = games[chat_id]
        
        if not game["is_registration"]:
            safe_answer_callback(call.id, "O'yin allaqachon boshlangan.", show_alert=True)
            return

        if len(game["players"]) < 4:
            safe_answer_callback(call.id, "O'yinni boshlash uchun kamida 4 ta o'yinchi kerak!", show_alert=True)
        else:
            game["is_registration"] = False
            safe_answer_callback(call.id, "O'yin boshlanmoqda!")
            
            player_ids = list(game["players"].keys())
            random.shuffle(player_ids)
            
            roles = {}
            roles[player_ids[0]] = "🕶 Mafia"
            roles[player_ids[1]] = "🕵️‍♂️ Detektiv"
            roles[player_ids[2]] = "👨‍⚕️ Shifokor"
            for p_id in player_ids[3:]:
                roles[p_id] = "👨‍🌾 Tinch aholi"
                
            game["roles"] = roles
            
            for p_id in player_ids:
                u = get_or_create_user(p_id, game["players"][p_id])
                u["games"] += 1
            
            failed_users = []
            for p_id, role in roles.items():
                try:
                    bot.send_message(
                        p_id, 
                        f"🤫 **Sizning rolingiz:** {role}\n\nO'yin qoidalariga rioya qiling va rolingizni hech kimga aytmang!",
                        parse_mode="Markdown"
                    )
                except Exception:
                    failed_users.append(game["players"][p_id])
            
            msg = f"🔥 **O'yin boshlandi!** Rollar barcha o'yinchilarning shaxsiy xabarlariga yuborildi.\n\n"
            if failed_users:
                msg += f"⚠️ Quyidagi o'yinchilar botga shaxsiy xabar yubormagani uchun rol ololmadi: {', '.join(failed_users)}.\n"
            
            msg += "🌃 **Tungi bosqich boshlandi...**\nShahar uyquga ketdi. Tun 60 soniya davom etadi!"
            bot.send_message(chat_id, msg, parse_mode="Markdown")
            
            Thread(target=run_night_phase, args=(chat_id,)).start()


def run_night_phase(chat_id):
    time.sleep(60)
    bot.send_message(chat_id, "☀️ **Tong otdi!**\n\nShahar uyg'ondi. Kechasi sodir bo'lgan voqealar tahlil qilinmoqda...")
    time.sleep(3)
    bot.send_message(
        chat_id, 
        "🗣 **Kunduzgi muhokama boshlandi!**\n\nSizda shubhali o'yinchilarni muhokama qilish uchun **90 soniya** vaqt bor.",
        parse_mode="Markdown"
    )
    time.sleep(90)
    bot.send_message(chat_id, "⏳ **Muhokama vaqti tugadi!** Ovoz berish bosqichi boshlanmoqda...")

# ----------------- BOTNI ISHGA TUSHIRISH (HAR DOIM ENG PASTDA!) -----------------
setup_bot_commands()

while True:
    try:
        print("Amigos Mafia boti uzilishlarsiz ishlamoqda...")
        bot.polling(none_stop=True, interval=1, timeout=20)
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        time.sleep(5)
