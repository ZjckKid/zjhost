import telebot
import json
import random
import string
import time
import os

from dotenv import load_dotenv
load_dotenv()

# Конфігурація бота
BOT_TOKEN = os.getenv("ADMIN_TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_TELEGRAM_ID")


bot = telebot.TeleBot(BOT_TOKEN)

# Файли для зберігання даних
ADMIN_CODES_DB = "bot_data/admin_codes.json"

# Створюємо папку якщо не існує
os.makedirs("bot_data", exist_ok=True)

def load_json(filepath):
    """Завантажує JSON файл"""
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(filepath, data):
    """Зберігає дані в JSON файл"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_code():
    """Генерує унікальний 6-значний код"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Привітання"""
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "У вас немає доступу до цього бота.")
        return
    
    response = (
        "🔐 <b>Адмін Бот ZJH</b>\n\n"
        "Цей бот використовується для авторизації в адмін-панелі.\n\n"
        "Коли ви натискаєте кнопку авторизації на сайті, "
        "я надішлю вам код для входу.\n\n"
        "<b>Команди:</b>\n"
        "/cancel - Скасувати останній код\n"
        "/codes - Переглянути активні коди\n"
        "/stats - Статистика кодів\n"
        "/clear - Очистити всі прострочені коди"
    )
    bot.reply_to(message, response, parse_mode="HTML")

@bot.message_handler(commands=['cancel'])
def cancel_code(message):
    """Скасування останнього коду"""
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        codes = load_json(ADMIN_CODES_DB)
        
        # Знаходимо останній активний код
        active_codes = [(code, data) for code, data in codes.items() 
                       if not data.get('used', False) and 
                       time.time() - data.get('timestamp', 0) < 600]
        
        if not active_codes:
            bot.reply_to(message, "❌ Немає активних кодів для скасування.", parse_mode="HTML")
            return
        
        # Сортуємо по часу створення
        active_codes.sort(key=lambda x: x[1]['timestamp'], reverse=True)
        latest_code = active_codes[0][0]
        
        # Видаляємо код
        del codes[latest_code]
        save_json(ADMIN_CODES_DB, codes)
        
        bot.reply_to(message, 
                    f"✅ Код <code>{latest_code}</code> успішно скасовано!",
                    parse_mode="HTML")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Помилка: {str(e)}", parse_mode="HTML")

@bot.message_handler(commands=['codes'])
def list_codes(message):
    """Список активних кодів"""
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        codes = load_json(ADMIN_CODES_DB)
        
        # Знаходимо активні коди
        active_codes = []
        for code, data in codes.items():
            if not data.get('used', False):
                time_left = 600 - (time.time() - data.get('timestamp', 0))
                if time_left > 0:
                    active_codes.append((code, time_left))
        
        if not active_codes:
            bot.reply_to(message, "📭 Немає активних кодів.", parse_mode="HTML")
            return
        
        response = "🔑 <b>Активні коди:</b>\n\n"
        for code, time_left in sorted(active_codes, key=lambda x: x[1], reverse=True):
            minutes = int(time_left // 60)
            seconds = int(time_left % 60)
            response += f"<code>{code}</code> - залишилось {minutes}:{seconds:02d}\n"
        
        bot.reply_to(message, response, parse_mode="HTML")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Помилка: {str(e)}", parse_mode="HTML")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    """Статистика кодів"""
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        codes = load_json(ADMIN_CODES_DB)
        
        total_codes = len(codes)
        used_codes = sum(1 for data in codes.values() if data.get('used', False))
        active_codes = sum(1 for code, data in codes.items() 
                          if not data.get('used', False) and 
                          time.time() - data.get('timestamp', 0) < 600)
        expired_codes = sum(1 for code, data in codes.items() 
                           if not data.get('used', False) and 
                           time.time() - data.get('timestamp', 0) >= 600)
        
        response = (
            f"📊 <b>Статистика кодів:</b>\n\n"
            f"🔢 Всього кодів: {total_codes}\n"
            f"✅ Використано: {used_codes}\n"
            f"🔓 Активних: {active_codes}\n"
            f"⏰ Прострочених: {expired_codes}"
        )
        
        bot.reply_to(message, response, parse_mode="HTML")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Помилка: {str(e)}", parse_mode="HTML")

@bot.message_handler(commands=['clear'])
def clear_expired(message):
    """Очищення прострочених кодів"""
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        codes = load_json(ADMIN_CODES_DB)
        
        # Видаляємо прострочені та використані коди
        new_codes = {}
        removed = 0
        
        for code, data in codes.items():
            # Залишаємо тільки активні невикористані коди
            if not data.get('used', False) and time.time() - data.get('timestamp', 0) < 600:
                new_codes[code] = data
            else:
                removed += 1
        
        save_json(ADMIN_CODES_DB, new_codes)
        
        bot.reply_to(message, 
                    f"🗑️ Очищено {removed} прострочених/використаних кодів.\n"
                    f"📦 Залишилось {len(new_codes)} активних кодів.",
                    parse_mode="HTML")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Помилка: {str(e)}", parse_mode="HTML")

def send_admin_code(user_id):
    """Надсилає код адміністратору"""
    try:
        if user_id != ADMIN_ID:
            return None
        
        # Генеруємо код
        code = generate_code()
        codes = load_json(ADMIN_CODES_DB)
        
        # Зберігаємо код
        codes[code] = {
            'timestamp': time.time(),
            'used': False,
            'type': 'admin'
        }
        save_json(ADMIN_CODES_DB, codes)
        
        # Відправляємо код
        message = (
            f"🔐 <b>Код для входу в адмін-панель:</b>\n\n"
            f"<code>{code}</code>\n\n"
            f"⏱ Код дійсний протягом 10 хвилин.\n"
            f"❌ Скасувати: /cancel"
        )
        
        bot.send_message(ADMIN_ID, message, parse_mode="HTML")
        return code
        
    except Exception as e:
        print(f"Error sending admin code: {str(e)}")
        return None

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Обробка всіх інших повідомлень"""
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ У вас немає доступу до цього бота.")
        return
    
    bot.reply_to(message, 
                "ℹ️ Використовуйте команди для роботи з ботом.\n\n"
                "Доступні команди:\n"
                "/start - Допомога\n"
                "/codes - Активні коди\n"
                "/cancel - Скасувати код\n"
                "/stats - Статистика\n"
                "/clear - Очистити прострочені",
                parse_mode="HTML")

if __name__ == "__main__":
    print("Адмін бот ZJH запущено")
    print(f"Адмін ID: {ADMIN_ID}")
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("\n\nБот зупинено користувачем")
    except Exception as e:
        print(f"\n\nПомилка: {str(e)}")
