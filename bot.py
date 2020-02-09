from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.vendor.ptb_urllib3.urllib3 import disable_warnings
from telegram.vendor.ptb_urllib3.urllib3.exceptions import InsecureRequestWarning
from model import StyleTransferModel
from os.path import join, dirname
from yaml import safe_load
from io import BytesIO
import logging

first_image_file = {}

class TelegramBot:

    def __init__(self, token: str=None, proxy_url: str=None, from_config: bool=False):
        if from_config:
            config = self._get_config()
        elif all(token, proxy_url):
            config = {'token': token, 'proxy_url': proxy_url}
        self.updater = self.connect(config)
        self.model = StyleTransferModel()

    def _get_config(self):
        try:
            with open(join(dirname(__file__), 'config.yml')) as f:
                return safe_load(f)
        except:
            raise Exception('Couldn\'t find config.yml in project dir!')

    def start(self, update, context):
        update.message.reply_text(
            f'''Hello from Style Transfer Bot, {update.message.from_user.first_name}!\n
            To start your style transfer task send me the first image from which image style will be borrowed.\n
            Then send an another image to process and you will get this image styled as the first image in result.''')

    def hello(self, update, context):
        update.message.reply_text(
            f'Hello {update.message.from_user.first_name}')

    def process_photo(self, update, context):
        chat_id = update.message.chat_id
        print(f'Got image from {chat_id}')
        image_info = update.message.photo[-1]
        image_file = context.bot.get_file(image_info)

        if chat_id in first_image_file:
            content_image_stream, style_image_stream, output_stream = BytesIO(), BytesIO(), BytesIO()
            first_image_file[chat_id].download(out=content_image_stream)
            del first_image_file[chat_id]
            image_file.download(out=style_image_stream)
            output = self.model.transfer_style(content_image_stream, style_image_stream)
            output.save(output_stream, format='PNG') 
            output_stream.seek(0)
            context.bot.send_photo(chat_id, photo=output_stream)
            print('Sent Photo to user')

        else:
            first_image_file[chat_id] = image_file

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
            self.updater.dispatcher.add_handler(CommandHandler('start', self.start))
            self.updater.dispatcher.add_handler(CommandHandler('hello', self.hello))
            self.updater.dispatcher.add_handler(MessageHandler(Filters.photo, self.process_photo))
            self.updater.start_polling()
            self.updater.idle()
        except:
            raise Exception('Connection has failed. Please provide valid token and proxy.')
