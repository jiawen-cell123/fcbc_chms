from telegram.ext import Updater, CommandHandler, Filters
import pyrebase
from telegram import ChatAction
from functools import wraps
import requests
from bs4 import BeautifulSoup
import os
import requests


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
    # /loginChms 812E06111995
    db = firebase.database()
    message  = update.message.text
    key = " ".join(message.split()[1:])
    print(key)
    result = db.child("chms").get()
    found_id = False
    for i in result.each():
        if key == i.key():
            # {key: value}
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
    nric = " ".join(message.split()[1:]).upper()
    result = db.child("chms").child("812E06111995").child(nric).child("pinfo").get()
    if result.val():
        output = ""
        output = (result.each())[2].val() + "\n" + "\u2022 " + (result.each())[1].val() + "\n" + "\u2022 " + (result.each())[0].val()
        update.message.reply_text(output)
    else:
        update.message.reply_text("You have entered an invalid IC number")


@send_typing_action
def estatus(update, context):
    # estatus 0812E
    teamId = context.user_data['teamId']

    db = firebase.database()
    message = update.message.text
    id = message.split()[1]
    nric = message.split()[2]
    final_output = " "
    name = db.child("chms").child(teamId).child(nric.upper()).child("pinfo").child("name").get()
    equipping = db.child("chms").child(teamId).child(nric.upper()).child("estatus").get()
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


@send_typing_action
def thoughtOfTheWeek(update, context):
    print("totw")

@send_typing_action
def verseOfTheDay(update, context):
    print("votd")

def main():
    updater = Updater(API_KEY, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('getpinfo', getpinfo))
    dp.add_handler(CommandHandler('estatus', estatus))
    dp.add_handler((CommandHandler('login', loginChms)))
    dp.add_handler((CommandHandler('totw', thoughtOfTheWeek)))
    dp.add_handler((CommandHandler('votd', verseOfTheDay)))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
#
if __name__ == '__main__':
    # main()

    # page = requests.get("https://fcbc.org.sg/celebration/our-thoughts-this-week")
    # soup = BeautifulSoup(page.content, 'html.parser')
    # print(soup.prettify())
    # print(soup.find_all('h1')[0].get_text())
    # print(soup.find_all(match_class(["field-content"])))

    # db = firebase.database()
    # name = db.child("chms").child("812E06111995").child("324G").child("pinfo").child("name").get()
    # if (name.val() == None):
    #     print("user doesnt exist")


    # Assuming you keep your tokens in environment variables:
    # YOUVERSION_DEVELOPER_TOKEN = os.environ["morm_UDvP5k-ZR24Ak45D7-mKRY"]

    headers = {
        "accept": "application/json",
        "x-youversion-developer-token": "morm_UDvP5k-ZR24Ak45D7-mKRY",
        "accept-language": "en",
    }

    response = requests.get(
        "https://developers.youversionapi.com/1.0/versions",
        headers=headers
    )

    print(response.content)



