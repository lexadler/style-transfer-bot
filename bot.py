from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.vendor.ptb_urllib3.urllib3 import disable_warnings
from telegram.vendor.ptb_urllib3.urllib3.exceptions import InsecureRequestWarning
from os.path import join, dirname
from yaml import safe_load
from io import BytesIO
import logging

class TelegramBot:

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

    def process_photo(self, update, context):
        chat_id = update.message.chat_id
        print("Got image from {}".format(chat_id))
        image_info = update.message.photo[-1]
        image_file = context.bot.get_file(image_info)
        content_image_stream = BytesIO()
        image_file.download(out=content_image_stream)
        content_image_stream.seek(0)
        context.bot.send_photo(chat_id, photo=content_image_stream)

    def connect(self, config: dict):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO)
        disable_warnings(InsecureRequestWarning)
        return Updater(token = config.get('token'), use_context=True, request_kwargs={'proxy_url': config.get('proxy_url'), 'connect_timeout': 10.0, 'read_timeout': 10.0,
                                                                                                                            'urllib3_proxy_kwargs': {
                                                                                                                                                        'assert_hostname': 'False',
                                                                                                                                                        'cert_reqs': 'CERT_NONE'
                                                                                                                                                    }})

    def run(self):
        try:
            self.updater.dispatcher.add_handler(CommandHandler('hello', self.hello))
            self.updater.dispatcher.add_handler(MessageHandler(Filters.photo, self.process_photo))
            self.updater.start_polling()
            self.updater.idle()
        except:
            raise Exception('Connection has failed. Please provide valid token and proxy.')