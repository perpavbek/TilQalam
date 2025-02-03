import config
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers import start_bot, command_handler, test_handler, chat_handler, materials_handler
import google.generativeai as genai
import gemini

genai.configure(api_key=config.GEMINI_TOKEN)

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

gemini.model = genai.GenerativeModel(
  model_name="gemini-2.0-flash-exp",
  generation_config=generation_config,
)

def main():
    application = Application.builder().token(config.BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_bot))
    application.add_handler(CallbackQueryHandler(command_handler, pattern="^(command:.*)$"))
    application.add_handler(CallbackQueryHandler(test_handler, pattern="^(test:.*)$"))
    application.add_handler(CallbackQueryHandler(materials_handler, pattern="^(materials:.*)$"))
    application.add_handler(MessageHandler(filters.TEXT, chat_handler))

    application.run_polling()


if __name__ == "__main__":
    main()
