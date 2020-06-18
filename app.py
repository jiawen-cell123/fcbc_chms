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
    nric = message.split()[1]
    name = db.child("chms").child("812E06111995").child(nric).child("pinfo").child("name").get()
    equipping = db.child("chms").child("812E06111995").child(nric).child("estatus").get()
    output = ""
    for i in equipping.each():
        output = name.val(), i.key(), i.val()
        print(output)
        update.message.reply_text(output)
    # print(output)
    # print(output)
    # update.message.reply_text(output)


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
    #main()

    db = firebase.database()
    nric = "812E"
    final_output = "" #final output of the string
    name = db.child("chms").child("812E06111995").child(nric).child("pinfo").child("name").get()
    # get name
    # this will give me Gerald Moses Lim, Boon Hao
    print(name.val())
    final_output += name.val() + "\n\n" # add name to the final output and \n\n is like pressing enter on your keyboard twice

    equipping = db.child("chms").child("812E06111995").child(nric).child("estatus").get()
    # equipping.val() will give a ordered dict very difficult to read
    '''OrderedDict([('EW', {'date': '21 Sep 2012', 'title': 'Encounter Weekend'}), 
    ('SWW', {'attendance': '20.0%', 'date': '"2014/10/24 - 2014/11/0', 'title': 'Spiritual Warfare Weekend'}), 
    ('XFXZ', {'attendance': '100.00%', 'date': '2020/01/19 - 2020/01/19', 'title': 'XFXZ Training 幸福小组训练'}), 
    ('ePE', {'attendance': '100.00%', 'date': '2014/04/13 /05/27', 'title': 'Post Encounter Online'}), 
    ('eSOL1FN', {'attendance': '100.00%', 'date': '2015/04/12 - 2015/06/09', 'title': 'SOL1 Foundations Online'})])
    '''
    # so we iterate over the items in the ordered dict instead, below is the output, realise its just a normal dictionary
    '''
    {'date': '21 Sep 2012', 'title': 'Encounter Weekend'}
    {'attendance': '20.0%', 'date': '"2014/10/24 - 2014/11/0', 'title': 'Spiritual Warfare Weekend'}
    {'attendance': '100.00%', 'date': '2020/01/19 - 2020/01/19', 'title': 'XFXZ Training 幸福小组训练'}
    {'attendance': '100.00%', 'date': '2014/04/13 - 2014/05/27', 'title': 'Post Encounter Online'}
    {'attendance': '100.00%', 'date': '2015/04/12 - 2015/06/09', 'title': 'SOL1 Foundations Online'}
    '''
    for item in equipping.each():
        title = item.val()['title']  #item.val() will return a {}, to access the element is like accessing the value of a dictionary
        date = item.val()['date']
        attendance = item.val()['attendance']
        # do some string formatting
        final_output += title + "\n\u2022" + date + "\n\u2022" + attendance + "\n\n"

    print (final_output)










