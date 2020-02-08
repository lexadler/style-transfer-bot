from telegram.ext import Updater, CommandHandler
from os.path import join, dirname
from yaml import safe_load
import logging

class TelegramGANBot:

    def __init__(self, token: str=None, proxy_url: str=None, from_config: bool=False):
        if from_config:
            config = self._get_config()
        elif all(token, proxy_url):
            config = {'token': token, 'proxy_url': proxy_url}
        self.updater = self.connect(config)

    def _get_config(self):
        try:
            with open(join(dirname(__file__), 'config.yml')) as f:
                return safe_load(f)
        except:
            raise Exception('Couldn\'t find config.yml in project dir!')

    def hello(self, update, context):
        update.message.reply_text(
            'Hello {}'.format(update.message.from_user.first_name))

    def connect(self, config: dict):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO)
        return Updater(token = config.get('token'), use_context=True, request_kwargs={'proxy_url': config.get('proxy_url')})

    def run(self):
        try:
            self.updater.dispatcher.add_handler(CommandHandler('hello', self.hello))
            self.updater.start_polling()
            self.updater.idle()
        except:
            raise Exception('Connection has failed. Please provide valid token and proxy.')