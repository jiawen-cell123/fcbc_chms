from telegram.ext import Updater, CommandHandler, Filters
import pyrebase
from telegram import ChatAction
from functools import wraps

config = {
  "apiKey": "",
  "authDomain": "fcbc-chms.firebaseapp.com",
  "databaseURL": "https://fcbc-chms.firebaseio.com",
  "projectId": "fcbc-chms",
  "storageBucket": "fcbc-chms.appspot.com",
  "messagingSenderId": "821279803740",
  "appId": "1:821279803740:web:2c212f82f5436d45031999",
  "measurementId": "G-9C0W55BY70"
};

firebase = pyrebase.initialize_app(config)

API_KEY = ""

def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context, *args, **kwargs)

    return command_func

@send_typing_action
def getinfo (update,context):
    db = firebase.database()
    result = db.child("glmw").child("pinfo").child("gerald").get()
    output = ""
    for i in result.each():
        print(i.val())
        output += i.val() + "\n"
    update.message.reply_text(output)


def main():
    updater = Updater(API_KEY, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    printhello_handler = CommandHandler('get', getinfo)
    dp.add_handler(printhello_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()

