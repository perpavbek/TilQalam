from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from handlers import start, command_handler, test_handler, show_material, materials_handler
import config


def main():
    application = Application.builder().token(config.BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(command_handler, pattern="^(command:.*)$"))
    application.add_handler(CallbackQueryHandler(test_handler, pattern="^(test:.*)$"))
    application.add_handler(CallbackQueryHandler(materials_handler, pattern="^(materials:.*)$"))

    application.run_polling()


if __name__ == "__main__":
    main()