import telegram
from telegram.ext import Updater, CommandHandler, Filters
import pyrebase
from telegram import ChatAction
from functools import wraps
from bs4 import BeautifulSoup
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
bot = telegram.Bot(token = '1232203331:AAGRJxNgfTclfie4UQlglsofl2uzBR00-TY')



def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context, *args, **kwargs)

    return command_func

@send_typing_action
def start(update, context):
    bot.send_photo(chat_id=update.message.chat_id, photo="https://fcbc.org.sg/sites/default/files/fcbc_logo.jpg",caption="Welcome to FCBC CHMS Bot"+"\n"+"How can I help you ?" )

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
    name = " ".join(message.split()[1:])
    result = db.child("glmw").child("pinfo").child(name).get()
    output = ""
    for i in result.each():
        output += "\u2022" + i.val() + "\n"
    update.message.reply_text(output)

@send_typing_action
def estatus(update, context):
    # estatus 0812E
    db = firebase.database()
    teamId = context.user_data['teamId']
    list_of_nric = db.child("chms").child(teamId).get()
    message = update.message.text
    nric = message.split()[1].upper()
    found_nric = False
    for keys in list_of_nric.each():
            if nric == keys.key():
                final_output = " "
                name = db.child("chms").child(teamId).child(nric).child("pinfo").child("name").get()
                equipping = db.child("chms").child(teamId).child(nric).child("estatus").get()
                final_output += name.val() + "\n\n"
                for items in equipping.each():
                    title = items.val()["title"]
                    date = items.val()["date"]
                    if "attendance" not in items.val():
                        attendance = "NA"
                    else:
                        attendance = items.val()["attendance"]
                    final_output += title + "\n\u2022" + date + "\n\u2022" + attendance + "\n\n"
                found_nric = True
                break

    if found_nric:
        update.message.reply_text(final_output)
    else:
        update.message.reply_text("User does not exist." + "\n" + "Kindly check the last 4 digits of your NRIC !!")


@send_typing_action
def thoughtOfTheWeek(update, context):
    page = requests.get("https://fcbc.org.sg/celebration/our-thoughts-this-week")
    soup = BeautifulSoup(page.content, 'html.parser')
    header = soup.find_all('h1')[0].get_text()
    image = soup.find_all("img")
    name = ""
    for hit in soup.findAll(class_="views-field views-field-body"):
        output = ""
        output = header + "\n" + hit.text
    for i in image:
        src = i["src"]
        if "jpg" in src:
            name = src
    # get the source of the image
    url = "fcbc.org.sg" + name
    #combining fcbc.org.sg to source of the image
    print(output)
    bot.send_photo(chat_id=update.message.chat_id, photo=url)
    update.message.reply_text(output)
    #must use update.message.chat_id to send picture using telegram bot


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
    main()


# Assuming you keep your tokens in environment variables:
    # YOUVERSION_DEVELOPER_TOKEN = os.environ["morm_UDvP5k-ZR24Ak45D7-mKRY"]
    #
    # headers = {
    #     "accept": "application/json",
    #     "x-youversion-developer-token": "morm_UDvP5k-ZR24Ak45D7-mKRY",
    #     "accept-language": "en",
    # }
    #
    # response = requests.get(
    #     "https://developers.youversionapi.com/1.0/versions",
    #     headers=headers
    # )
    #
    # print(response.content)
    #
    #

