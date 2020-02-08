from telegram.ext import Updater, CommandHandler
from secrets import TOKEN, SOCKS4

def hello(update, context):
    update.message.reply_text(
        'Hello {}'.format(update.message.from_user.first_name))


updater = Updater(TOKEN, use_context=True, request_kwargs={'proxy_url': SOCKS4})

updater.dispatcher.add_handler(CommandHandler('hello', hello))

updater.start_polling()
updater.idle()
