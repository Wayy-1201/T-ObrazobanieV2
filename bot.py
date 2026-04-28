import os
from dotenv import load_dotenv
load_dotenv()

import telebot
from telebot import types
import config
import database as db
import llm
import game_data as GD

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
if not BOT_TOKEN:
    print(".env не содержит TELEGRAM_BOT_TOKEN")
    exit(1)

if not config.OPENROUTER_API_KEY:
    print("Укажите OpenRouter API")
    exit(1)

db.init_db()
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

user_state: dict[int, dict] = {}

def get_state(uid: int) -> dict:
    return user_state.setdefault(uid, {
        "mode": "book_select",
        "char_id": None,
        "note_char_id": None,
    })


def set_state(uid: int, **kwargs):
    get_state(uid).update(kwargs)


def send(chat_id, text: str, reply_markup=None):
    for i in range(0, len(text), 4000):
        chunk = text[i:i + 4000]
        bot.send_message(chat_id, chunk,
                         reply_markup=reply_markup if i == 0 else None)


def book_select_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.row(
        types.KeyboardButton("🩸 Пять поросят 🩸"),
        types.KeyboardButton("🔍 Шерлок Холмс 🔍"),
    )
    return markup


def book_confirm_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row(
        types.KeyboardButton("✅ Подтвердить выбор"),
        types.KeyboardButton("⬅️ Вернуться назад"),
    )
    return markup


def game_main_markup(talked: list):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.row(types.KeyboardButton("🏠 Место и обстоятельства"))
    markup.row(types.KeyboardButton("👥 Персонажи"))
    if len(talked) >= len(GD.CHARACTER_ORDER):
        markup.row(types.KeyboardButton("⚖️ Подвести итог"))
    markup.row(types.KeyboardButton("📝 Мои заметки"))
    return markup


def char_list_inline(talked: list):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for cid in GD.CHARACTER_ORDER:
        char = GD.CHARACTERS[cid]
        mark = "✅" if cid in talked else "❓"
        markup.add(types.InlineKeyboardButton(
            f"{mark} {char['name']}",
            callback_data=f"char_select:{cid}"
        ))
    return markup


def char_action_markup(char_id: str):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    markup.row(
        types.KeyboardButton("📖 Биография"),
        types.KeyboardButton("⬅️ Назад к меню"),
    )
    markup.row(types.KeyboardButton("✅ Завершить допрос"))
    return markup


def add_note_inline(char_id: str):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "📝 Добавить заметку", callback_data=f"add_note_prompt:{char_id}"
    ))
    return markup


@bot.message_handler(commands=["start"])
def cmd_start(message):
    uid = message.from_user.id
    username = message.from_user.username
    db.ensure_user(uid)
    if db.has_active_game(uid):
        set_state(uid, mode="start_menu", char_id=None)
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("▶️ Продолжить", callback_data="continue_game"),
            types.InlineKeyboardButton("🔄 Новая игра", callback_data="new_game"),
        )
        bot.send_message(message.chat.id,
             f"<b>Добро пожаловать обратно, {username} ! У вас есть незавершённое расследование</b>",
             reply_markup=markup , parse_mode="HTML")
    else:
        set_state(uid, mode="book_select", char_id=None)
        photo2 = open('imgs/start_picture.png', 'rb')
        bot.send_photo(chat_id = message.chat.id , photo=photo2 , parse_mode="HTML" , caption=f"<b>Добро пожаловать в детективные расследования от Т-Банк, {username} !\n\nВыберите дело, которое хотите расследовать.</b> Получайте Т-Коины за прохождения книг и покупайте промокоды на сайте", reply_markup=book_select_markup())



@bot.message_handler(func=lambda m: True, content_types=["text"])
def msg_text(message):
    uid = message.from_user.id
    state = get_state(uid)
    text = message.text.strip()
    chat_id = message.chat.id
    mode = state["mode"]

    if mode == "note_input":
        handle_note_input(message)
        return

    if mode == "start_menu":
        send(chat_id, "Используйте кнопки выше: ▶️ Продолжить или 🔄 Новая игра.")
        return

    if mode == "book_select":
        if text == "🩸 Пять поросят 🩸":
            set_state(uid, mode="book_confirm")
            photo2 = open('imgs/agata.png', 'rb')
            bot.send_photo(chat_id, parse_mode="HTML",photo = photo2 , caption = 
                 "Вы выбрали:\n<b>🐷 Пять поросят - Агата Кристи\n\n</b>"
                 "<b>Вы - Эркюль Пуаро ( Детектив )</b>. Шестнадцать лет назад Кэролайн Крейл "
                 "была осуждена за убийство мужа-художника - Эмиаса Крейла."
                 "Её дочь Карла уверена: мать невиновна "
                 "В тот день в поместье Олдербери было пятеро свидетелей."
                 "Все живы. Все готовы говорить.\n\n"
                 "<b>Подтвердите выбор или вернитесь назад</b>\n\n"

                "<b>✨ ПОМОЩЬ ✨\n\n</b>"
                "📚 На старте выберите книгу для расследования.\n\n"
                 "🎮 В ходе игры:\n"
                "🏠 Место и обстоятельства - фон дела\n"
                "👥 Персонажи - выбрать свидетеля для допроса\n"
                "⚖️ Подвести итог -  назвать убийцу (после всех допросов)\n"
                "📝 Мои заметки -  просмотреть сохранённые заметки\n\n"
                "🗣️ Во время допроса:\n"
                "📞 Просто напишите вопрос -  задать его персонажу\n"
                "📖 Биография -  узнать о персонаже\n"
                "📝 Добавить заметку -  появляется под каждым ответом\n"
                "✅ Завершить допрос -  вернуться к выбору персонажей\n"
                "⬅️ Назад - вернуться к списку персонажей\n\n"
                "▶ /start чтобы начать сначала или новую игру",
                 reply_markup=book_confirm_markup())
            



        elif text == "🔍 Шерлок Холмс 🔍":
            bot.send_message(chat_id, parse_mode="HTML", text = 
                 "🔍 <b> Дело Шерлока Холмса</b> пока в разработке.\n"
                 "Выберите другое расследование.",
                 reply_markup=book_select_markup())
        else:
            send(chat_id, "Выберите книгу из списка ниже:", reply_markup=book_select_markup())
        return

    if mode == "book_confirm":
        if text == "✅ Подтвердить выбор":
            _start_agatha_game(chat_id, uid)
        elif text == "⬅️ Вернуться назад":
            set_state(uid, mode="book_select")
            send(chat_id, "Выберите расследование:", reply_markup=book_select_markup())
        else:
            send(chat_id, "Используйте кнопки ниже.", reply_markup=book_confirm_markup())
        return

    if mode == "game":
        talked = db.get_talked_chars(uid)

        if text == "🏠 Место и обстоятельства":
            photo3 = open('imgs/pivo.png', 'rb')
            bot.send_photo(chat_id,photo = photo3 , parse_mode="HTML", caption= GD.CASE_SUMMARY ,  reply_markup=game_main_markup(talked))
            bot.send_message(chat_id=chat_id , text = GD.LOCATION_TEXT, reply_markup=game_main_markup(talked) , parse_mode="HTML")



        elif text == "👥 Персонажи":
            photo4 = open('imgs/characters.png', 'rb')
            bot.send_photo(chat_id, parse_mode="HTML" , caption= "<b>Выберите свидетеля для допроса:</b>", photo = photo4 ,reply_markup=char_list_inline(talked))

        elif text == "⚖️ Подвести итог":
            if len(talked) < len(GD.CHARACTER_ORDER):
                send(chat_id, "⚠️ Сначала допросите всех пятерых свидетелей.",
                     reply_markup=game_main_markup(talked))
            else:
                set_state(uid, mode="accusation_input")
                photo6 = open('imgs/syda.png', 'rb')
                bot.send_photo(chat_id, parse_mode="HTML", caption = 
                     "<b>📌 ОБВИНЕНИЕ\n\n</b>"
                     "Мсье Пуаро, вы изучили все показания.\n"
                     "Напишите имя убийцы и кратко объясните, почему вы так считаете.\n\n"
                     "Формат: Имя — причина",
                     photo=photo6,
                     reply_markup=types.ReplyKeyboardRemove())

        elif text == "📝 Мои заметки":
            _show_notes(chat_id, uid, reply_markup=game_main_markup(talked))

        else:
            send(chat_id, "Используйте кнопки меню ниже", reply_markup=game_main_markup(talked))
        return

    if mode == "interrogation":
        char_id = state["char_id"]
        char = GD.CHARACTERS[char_id]

        if text == "📖 Биография":
            bot.send_message(chat_id, parse_mode="HTML", text = f"{char['biography']}", reply_markup=char_action_markup(char_id))
            return

        if text == "⬅️ Назад к меню":
            talked = db.get_talked_chars(uid)
            set_state(uid, mode="game", char_id=None)
            send(chat_id, " ◀ Вы вернулись назад",
                 reply_markup=game_main_markup(talked))
            return

        if text == "✅ Завершить допрос":
            db.mark_talked(uid, char_id)
            talked = db.get_talked_chars(uid)
            set_state(uid, mode="game", char_id=None)
            send(chat_id, f"✅ Допрос {char['name']} завершён.",
                 reply_markup=game_main_markup(talked))
            return

        _ask_llm_and_reply(chat_id, uid, char_id, text)
        return

    if mode == "accusation_input":
        _handle_accusation(chat_id, uid, text)
        return

    send(chat_id, "Введите /start чтобы начать.", reply_markup=book_select_markup())



@bot.callback_query_handler(func=lambda c: True)
def callback_handler(call):
    uid = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data
    bot.answer_callback_query(call.id)

    if data == "continue_game":
        talked = db.get_talked_chars(uid)
        set_state(uid, mode="game", char_id=None)
        send(chat_id, "Продолжаем расследование!", reply_markup=game_main_markup(talked))

    elif data == "new_game":
        db.reset_user(uid)
        set_state(uid, mode="book_select", char_id=None)
        send(chat_id, "Выберите расследование:", reply_markup=book_select_markup())

    elif data.startswith("char_select:"):
        char_id = data.split(":")[1]
        _start_interrogation(chat_id, uid, char_id)

    elif data.startswith("add_note_prompt:"):
        char_id = data.split(":")[1]
        set_state(uid, mode="note_input", note_char_id=char_id)
        bot.send_message(chat_id,
                         "✏️ Напишите текст заметки (следующим сообщением):",
                         reply_markup=types.ForceReply(selective=True))



def handle_note_input(message):
    uid = message.from_user.id
    state = get_state(uid)
    char_id = state.get("note_char_id")
    text = message.text.strip()

    if text and char_id:
        db.add_note(uid, char_id, text)
        char = GD.CHARACTERS[char_id]
        bot.send_message(message.chat.id,
                         f"📝 Заметка сохранена для [{char['name']}]:\n{text}",
                         reply_markup=char_action_markup(char_id))
    else:
        bot.send_message(message.chat.id, "⚠️ Заметка не сохранена.",
                         reply_markup=char_action_markup(char_id) if char_id else None)

    set_state(uid, mode="interrogation", note_char_id=None)






def _start_agatha_game(chat_id: int, uid: int):
    db.reset_user(uid)
    set_state(uid, mode="game", char_id=None)
    photo2 = open('imgs/london.png', 'rb')
    bot.send_photo(chat_id=chat_id, photo=photo2,  parse_mode="HTML", caption = "<b> ⚡ ДЕЛО КРЕЙЛА ⚡\n</b>" + GD.INTRO_TEXT,reply_markup=game_main_markup([]))

def _start_interrogation(chat_id: int, uid: int, char_id: str):
    char = GD.CHARACTERS[char_id]
    history = db.get_history(uid, char_id)

    bot.send_message(chat_id, text = f"<b>ДОПРОС: {char['name']}\n\n {char['title']}</b>" , parse_mode="HTML",reply_markup=char_action_markup(char_id))
    if not history:
        
        bot.send_message(chat_id, f"💬 {char['name']}:\n\n{char['intro']}",
                         reply_markup=add_note_inline(char_id))
        db.add_message(uid, char_id, "assistant", char["intro"])
    else:
        bot.send_message(chat_id, "Вы продолжаете допрос. Задайте вопрос.",
                         reply_markup=add_note_inline(char_id))

    set_state(uid, mode="interrogation", char_id=char_id)




def _ask_llm_and_reply(chat_id: int, uid: int, char_id: str, question: str):
    char = GD.CHARACTERS[char_id]
    history = db.get_history(uid, char_id)

    bot.send_message(chat_id, "⌛ Пуаро задал вопрос... ")

    try:
        answer = llm.ask_character(char["system_prompt"], history, question)
    except Exception as e:
        send(chat_id, f"❌ Ошибка API: {e}", reply_markup=char_action_markup(char_id))
        return

    db.add_message(uid, char_id, "user", question)
    db.add_message(uid, char_id, "assistant", answer)

    bot.send_message(chat_id, f"💬 {char['name']}:\n\n{answer}",
                     reply_markup=add_note_inline(char_id))


def _show_notes(chat_id: int, uid: int, reply_markup=None):
    photo5 = open('imgs/notes.png', 'rb')
    notes = db.get_notes(uid)
    if not notes:
        bot.send_message(chat_id, "<b>📝 Заметок пока нет</b>", reply_markup=reply_markup , parse_mode="HTML")
        return
    lines = ["<b>📝 МОИ ЗАМЕТКИ\n</b>"]
    current = None
    for cid, content in notes:
        if cid != current:
            current = cid
            lines.append(f"\n[{GD.CHAR_NAMES.get(cid, cid)}]")
        lines.append(f"  • {content}")
    bot.send_photo(chat_id,photo= photo5 , parse_mode="HTML",caption="\n".join(lines), reply_markup=reply_markup)


def _check_reasoning_with_llm(killer_id: str, user_text: str) -> tuple[bool, str]:
    correct_reasoning = GD.CORRECT_REASONING.get(killer_id, "")
    prompt = (
        f"Ты — судья детективной игры по роману Агаты Кристи «Пять поросят».\n\n"
        f"Эталонное обоснование (полное правильное решение):\n{correct_reasoning}\n\n"
        f"Ответ игрока:\n{user_text}\n\n"
        f"Шаг 1. Есть ли в ответе вообще какое-либо обоснование (не просто имя)? "
        f"Если нет — сразу VERDICT: NO.\n\n"
        f"Шаг 2. Проверь ответ по трём обязательным компонентам:\n"
        f"  А) УБИЙЦА — назван правильный человек.\n"
        f"  Б) СПОСОБ/ОРУДИЕ — упомянут яд, отрава, кониин или что-то подобное "
        f"(не обязательно точное название, но суть должна быть).\n"
        f"  В) МОТИВ — объяснено почему: Эмиас уходил/отвергал/бросал убийцу, "
        f"ревность, невозможность смириться с потерей — суть должна присутствовать.\n\n"
        f"Для VERDICT: YES необходимо, чтобы присутствовали все три компонента — А, Б и В. "
        f"Если хотя бы один отсутствует или грубо искажён — VERDICT: NO.\n\n"
        f"Ответь СТРОГО в формате (две строки, ничего лишнего):\n"
        f"VERDICT: YES или NO\n"
        f"FEEDBACK: одно-два предложения от лица суда — что названо верно и чего не хватает."
    )
    try:
        result = llm.ask_character(
            system_prompt="Ты строгий но справедливый судья детективной игры. Отвечай только в указанном формате.",
            history=[],
            question=prompt,
        )
        verdict = False
        feedback = ""
        for line in result.splitlines():
            if line.startswith("VERDICT:"):
                verdict = "YES" in line.upper()
            elif line.startswith("FEEDBACK:"):
                feedback = line.replace("FEEDBACK:", "").strip()
        return verdict, feedback
    except Exception:
        return True, ""


def _handle_accusation(chat_id: int, uid: int, text: str):
    text_lower = text.lower()
    found_killer = None
    for kid, kname in GD.ACCUSATION_CHOICES:
        if any(part in text_lower for part in kname.lower().split() if len(part) > 3):
            found_killer = kid
            break

    if not found_killer:
        send(chat_id,
             "🤔 Не могу распознать имя подозреваемого. Попробуйте ещё раз.\n\n"
             "Введите одно из имён:\n" +
             "\n".join(f"• {kname}" for _, kname in GD.ACCUSATION_CHOICES),
             reply_markup=types.ReplyKeyboardRemove())
        return

    killer_name = dict(GD.ACCUSATION_CHOICES)[found_killer]

    send(chat_id, f"⚖️ Ваш ответ: {killer_name}\n\nСуд анализирует ваши доводы...")

    if found_killer == "caroline":
        send(chat_id, GD.ENDING_CAROLINE)
        _offer_new_game(chat_id, uid)
        return

    if found_killer != GD.CORRECT_KILLER:
        send(chat_id, "❌ НЕВЕРНО!\n\n" + GD.ENDING_WRONG)
        talked = db.get_talked_chars(uid)
        set_state(uid, mode="game")
        send(chat_id, "Пересмотрите показания и попробуйте снова.",
             reply_markup=game_main_markup(talked))
        return

    reasoning_ok, feedback = _check_reasoning_with_llm(found_killer, text)

    if reasoning_ok:
        db.add_tcoins(uid, 1)
        new_balance = db.get_tcoins(uid)
        conclusion = f"🎉 ВЕРНО!\n\n{GD.ENDING_CORRECT}\n\n🪙 +1 T-Коин! Баланс: {new_balance}"
        if feedback:
            conclusion += f"\n\n💭 Суд: {feedback}"
        photo = open('imgs/ending_correct.png', 'rb')
        bot.send_photo(chat_id, photo=photo , caption=conclusion , parse_mode="HTML")
        _offer_new_game(chat_id, uid)
    else:
        reply = "🤔 Обоснование неубедительно."
        if feedback:
            reply += f"\n\n💭 Суд: {feedback}"
        send(chat_id, reply, reply_markup=types.ReplyKeyboardRemove())


def _offer_new_game(chat_id: int, uid: int):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Новая игра", callback_data="new_game"))
    bot.send_message(chat_id, "Спасибо за расследование, мсье Пуаро.", reply_markup=markup)


# ── Запуск ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🕵️ Бот запущен...")
    bot.infinity_polling(timeout=30, long_polling_timeout=20)