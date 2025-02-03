import asyncio
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
from questions import GRAMMAR_MATERIALS, TESTS
import gemini
TEST_QUESTIONS = []
USERS = []

def create_inline_keyboard(buttons_dict, row_size=2):
    buttons = [(text, callback) for text, callback in buttons_dict.items() if text and callback]

    keyboard = [buttons[i:i + row_size] for i in range(0, len(buttons), row_size)]

    inline_keyboard = [
        [InlineKeyboardButton(text, callback_data=callback) for text, callback in row]
        for row in keyboard
    ]

    return InlineKeyboardMarkup(inline_keyboard)


def create_test_keyboard(question):
    buttons_dict = {option: "test:test_answer:" + option for option in question["options"]}
    buttons_dict["Тесті тоқтату"] = "test:stop_test"
    return create_inline_keyboard(buttons_dict, row_size=2)


def create_materials_keyboard(materials):
    buttons_dict = {item["name"]: "materials:select_material:" + str(item["id"]) for item in materials}
    if int(materials[0]["id"]) == 1:
        buttons_dict["Келесі бет➡️"] = f"materials:page:{int(materials[0]["id"] / 4) + 1}"
    elif int(materials[-1]["id"]) == len(GRAMMAR_MATERIALS):
        buttons_dict["⬅️Алдыңғы бет"] = f"materials:page:{int(materials[0]["id"] / 4) - 1}"
    else:
        buttons_dict["⬅️Алдыңғы бет"] = f"materials:page:{int(materials[0]["id"] / 4) - 1}"
        buttons_dict["Келесі бет➡️"] = f"materials:page:{int(materials[0]["id"] / 4) + 1}"

    buttons_dict["📋Мәзірге оралу"] = "command:start"

    return create_inline_keyboard(buttons_dict, row_size=2)

def create_select_test_keyboard(tests):
    buttons_dict = {item["title"]: "test:start_test:" + str(item["id"]) for item in tests}
    if int(tests[0]["id"]) == 1:
        buttons_dict["Келесі бет➡️"] = f"test:page:{int(tests[0]["id"] / 4) + 1}"
    elif int(tests[-1]["id"]) == len(TESTS):
        buttons_dict["⬅️Алдыңғы бет"] = f"test:page:{int(tests[0]["id"] / 4) - 1}"
    else:
        buttons_dict["⬅️Алдыңғы бет"] = f"test:page:{int(tests[0]["id"] / 4) - 1}"
        buttons_dict["Келесі бет➡️"] = f"test:page:{int(tests[0]["id"] / 4) + 1}"

    buttons_dict["📋Мәзірге оралу"] = "command:start"

    return create_inline_keyboard(buttons_dict, row_size=2)

async def chat_handler(update: Update, context: CallbackContext):
    if context.user_data.get("chat", "off") == "on":
        sent_message = await update.message.reply_text("Күте тұрыңыз, мен жауап жасап жатырмын...", parse_mode="Markdown")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, gemini.chat_sessions[context.user_data.get("user_id", 0)].send_message,
                                            f"Менің сұрақтарыма адам ретінде және тек қазақша жауап бер. Сіз қазақ тілінде адам ретінде жауап бересіз деп айтудың қажеті жоқ. {update.message.text}")
    reply_markup = create_inline_keyboard({"👾Сөйлесуді тоқтату": "command:stop_chat"})
    await sent_message.edit_text(result.text, parse_mode="Markdown", reply_markup=reply_markup)

async def show_start_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    main_keyboard_dict = {
        "✅Тестті таңдау": "test:page:0",
        "✍️Грамматикалық Материалдары": "materials:page:0",
        "🤖AI-мен сөйлесу" : "command:start_chat"
    }
    reply_markup = create_inline_keyboard(main_keyboard_dict, row_size=2)
    if update.message:
        await update.message.reply_text("Сәлеметсіз бе! Функцияны таңдаңыз.", reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.edit_message_text("Сәлеметсіз бе! Функцияны таңдаңыз.", reply_markup=reply_markup)


async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = random.randint(1, 1000)
    while(user_id in USERS):
        user_id = random.randint(1, 1000)
    USERS.append(user_id)
    context.user_data["user_id"] = user_id
    await show_start_message(update, context)


async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    current_question = context.user_data.get("current_question", 0)

    if current_question < len(TEST_QUESTIONS):
        question = TEST_QUESTIONS[current_question]
        reply_markup = create_test_keyboard(question)
        await query.edit_message_text(question["question"], reply_markup=reply_markup)

    else:
        score = context.user_data.get("score", 0)
        reply_markup = create_inline_keyboard({"Жабу": "command:start"})
        await query.edit_message_text(f"Тест аяқталды! Сіздің ұпайыңыз:{score}/{len(TEST_QUESTIONS)}", reply_markup=reply_markup)


async def test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TEST_QUESTIONS
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")

    if len(data) > 1 and data[0] == "test":
        if data[1] == "start_test":
            for test in TESTS:
                if str(test["id"]) == data[2]:
                    context.user_data["score"] = 0
                    context.user_data["current_question"] = 0
                    TEST_QUESTIONS = test["questions"]
                    await send_question(update, context)

        elif data[1] == "test_answer":
            current_question = context.user_data.get("current_question", 0)
            if current_question < len(TEST_QUESTIONS):
                correct_answer = TEST_QUESTIONS[current_question]["answer"]
                if data[2] == correct_answer:
                    context.user_data["score"] += 1

                context.user_data["current_question"] += 1
                await send_question(update, context)
        elif data[1] == "stop_test":
            score = context.user_data.get("score", 0)
            reply_markup = create_inline_keyboard({"Жабу": "command:start"})
            await query.edit_message_text(f"Тест тоқтады! Сіздің ұпайыңыз:{score}/{len(TEST_QUESTIONS)}", reply_markup=reply_markup)

        elif data[1] == "page":
            page = int(data[2])
            reply_markup = create_select_test_keyboard(TESTS[page * 4: page * 4 + 4])
            await query.edit_message_text(f"Тестті таңдаңыз:", reply_markup=reply_markup)

async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")

    if len(data) > 1 and data[0] == "command":

        if data[1] == "start":
            await show_start_message(update, context)

        elif data[1] == "start_chat":
            context.user_data["chat"] = "on"
            gemini.add_chat_session(context.user_data.get("user_id", 0))
            reply_markup = create_inline_keyboard({"👾Сөйлесуді тоқтату": "command:stop_chat"})
            await query.edit_message_text(f"Кез келген сұрақ бойынша AI-ден сұраңыз", reply_markup=reply_markup)

        elif data[1] == "stop_chat":
            context.user_data["chat"] = "off"
            await show_start_message(update, context)

async def materials_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split(":")
    if data[1] == "select_material":
        await show_material(update, context, int(data[2]))
    if data[1] == "page":
        page = int(data[2])
        reply_markup = create_materials_keyboard(GRAMMAR_MATERIALS[page * 4: page * 4 + 4])
        await query.edit_message_text("Қол жетімді грамматика материалдары:", reply_markup=reply_markup)



async def show_material(update: Update, context: ContextTypes.DEFAULT_TYPE, material_id):
    query = update.callback_query
    for material in GRAMMAR_MATERIALS:
        if material["id"] == material_id:
            reply_markup = create_inline_keyboard({"Материалдарға өту": "command:view_materials",
                                                   "Бастауға оралу": "command:start"})
            await query.edit_message_text(material["description"], reply_markup=reply_markup)
            return
    await query.edit_message_text("Материал табылмады. Дұрыс енгізгеніңізге көз жеткізіңіз.")