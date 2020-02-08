from bot import TelegramBot

if __name__ == '__main__':
    bot = TelegramBot(from_config=True)
    bot.run()
