from telegram.ext import Updater, CommandHandler, Filters
import pyrebase
from telegram import ChatAction
from functools import wraps


config = {
  "apiKey": "AIzaSyB008v4XejOl06TBFdRe3VjtxbbnfvLRCk",
  "authDomain": "fcbc-chms.firebaseapp.com",
  "databaseURL": "https://fcbc-chms.firebaseio.com",
  "projectId": "fcbc-chms",
  "storageBucket": "fcbc-chms.appspot.com",
  "messagingSenderId": "821279803740",
  "appId": "1:821279803740:web:2c212f82f5436d45031999",
  "measurementId": "G-9C0W55BY70"
};

firebase = pyrebase.initialize_app(config)

API_KEY = "1232203331:AAGRJxNgfTclfie4UQlglsofl2uzBR00-TY"



def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context, *args, **kwargs)

    return command_func

@send_typing_action
def start(update,context):
    update.message.reply_text("Welcome to FCBC CHMS Bot"+"\n"+"How can I help you ?")

@send_typing_action
def loginChms(update, context):
    db = firebase.database()
    message  = update.message.text
    key = " ".join(message.split()[1:])
    print(key)
    result = db.child("chms").get()
    found_id = False
    for i in result.each():
        if key == i.key():
            context.user_data["teamId"] = key
            found_id = True
            break
    if found_id:
        update.message.reply_text("login successful")
    else:
        update.message.reply_text("login unsuccessful")

@send_typing_action
def getpinfo(update, context):
    db = firebase.database()
    message = update.message.text
    name = " ".join(message.split()[1:])
    result = db.child("glmw").child("pinfo").child(name).get()
    output = ""
    for i in result.each():
        output += "\u2022" + i.val() + "\n"
    update.message.reply_text(output)


@send_typing_action
def estatus(update, context):
    db = firebase.database()
    message = update.message.text
    id = message.split()[1]
    nric = message.split()[2]
    final_output = " "
    name = db.child("chms").child(id.upper()).child(nric.upper()).child("pinfo").child("name").get()
    equipping = db.child("chms").child(id.upper()).child(nric.upper()).child("estatus").get()
    final_output += name.val() + "\n\n"
    for items in equipping.each():
        title = items.val()["title"]
        date = items.val()["date"]
        if "attendance" not in items.val():
            attendance = "NA"
        else:
            attendance = items.val()["attendance"]
        final_output += title + "\n\u2022" + date + "\n\u2022" + attendance + "\n\n"
    print(final_output)
    update.message.reply_text(final_output)



def main():
    updater = Updater(API_KEY, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('getpinfo', getpinfo))
    dp.add_handler(CommandHandler('estatus', estatus))
    dp.add_handler((CommandHandler('login', loginChms)))


    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
#
if __name__ == '__main__':
    main()

    # db = firebase.database()
    # nric = "143g"
    # id = "572C03061996"
    # final_output = " "
    # name = db.child("chms").child(id.upper()).child(nric.upper()).child("pinfo").child("name").get()
    # equipping = db.child("chms").child(id.upper()).child(nric.upper()).child("estatus").get()
    # print(name.val())
    # for items in equipping.each():
    #     title = items.val()["title"]
    #     date = items.val()["date"]
    #     if "attendance" not in items.val():
    #         attendance = ""
    #     else:
    #         attendance = items.val()["attendance"]
    #     final_output = title + date + attendance
    #     print(final_output)

    # print(final_output)