from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from questions import GRAMMAR_MATERIALS, TESTS

TEST_QUESTIONS = []


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
    buttons_dict["Stop test"] = "test:stop_test"
    return create_inline_keyboard(buttons_dict, row_size=2)


def create_materials_keyboard(materials):
    buttons_dict = {item["name"]: "materials:" + str(item["id"]) for item in materials}
    buttons_dict["Back to the menu"] = "command:start"
    return create_inline_keyboard(buttons_dict, row_size=2)


async def show_start_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    main_keyboard_dict = {
        "Select a Test": "command:select_test",
        "View Grammar Materials": "command:view_materials"
    }
    reply_markup = create_inline_keyboard(main_keyboard_dict, row_size=2)
    if update.message:
        await update.message.reply_text("Welcome! Choose an option:", reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.edit_message_text("Welcome! Choose an option:", reply_markup=reply_markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        reply_markup = create_inline_keyboard({"close": "command:start"})
        await query.edit_message_text(f"Test completed! Your score: {score}/{len(TEST_QUESTIONS)}", reply_markup=reply_markup)


async def test_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TEST_QUESTIONS
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")

    if len(data) > 1 and data[0] == "test":
        if data[1] == "start_test":
            for test in TESTS:
                if test["title"] == data[2]:
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
            reply_markup = create_inline_keyboard({"close": "command:start"})
            await query.edit_message_text(f"Test stopped! Your score: {score}/{len(TEST_QUESTIONS)}", reply_markup=reply_markup)
            context.user_data.pop("score")
            context.user_data.pop("current_question")

async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")

    if len(data) > 1 and data[0] == "command":
        if data[1] == "select_test":
            context.user_data["current_question"] = 0
            context.user_data["score"] = 0
            buttons = {option["title"]: "test:start_test:" + option["title"] for option in TESTS}
            reply_markup = create_inline_keyboard(buttons)
            await query.edit_message_text(f"Select test: ", reply_markup=reply_markup)

        elif data[1] == "view_materials":
            reply_markup = create_materials_keyboard(GRAMMAR_MATERIALS)
            await query.edit_message_text("Available Grammar Materials:", reply_markup=reply_markup)

        elif data[1] == "start":
            await show_start_message(update, context)


async def materials_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split(":")
    print(data[1])

    await show_material(update, context, int(data[1]))


async def show_material(update: Update, context: ContextTypes.DEFAULT_TYPE, material_id):
    query = update.callback_query
    for material in GRAMMAR_MATERIALS:
        if material["id"] == material_id:
            reply_markup = create_inline_keyboard({"Go to the materials": "command:view_materials",
                                                   "Go to the start": "command:start"})
            await query.edit_message_text(material["description"], reply_markup=reply_markup)
        else:
            await query.edit_message_text("Material not found. Make sure you typed it correctly.")
