import telegram
from telegram.ext import Updater, CommandHandler, Filters, MessageHandler
import pyrebase
from telegram import ChatAction
from functools import wraps
from bs4 import BeautifulSoup
import requests
from uuid import uuid4
import re
import datetime
import pyshorteners


# environmental variables
BOT_TOKEN = "1232203331:AAGRJxNgfTclfie4UQlglsofl2uzBR00-TY"
BIBLE_API_TOKEN = "643c03c56dfaef821ef0247f1aa2dde0"
FIREBASE_TOKEN = "AIzaSyB008v4XejOl06TBFdRe3VjtxbbnfvLRCk"
# PORT = int(os.environ.get('PORT', '8443'))

# initialisation
config = {
    "apiKey": FIREBASE_TOKEN,
    "authDomain": "fcbc-chms.firebaseapp.com",
    "databaseURL": "https://fcbc-chms.firebaseio.com",
    "projectId": "fcbc-chms",
    "storageBucket": "fcbc-chms.appspot.com",
    "messagingSenderId": "821279803740",
    "appId": "1:821279803740:web:2c212f82f5436d45031999",
    "measurementId": "G-9C0W55BY70"
}
firebase = pyrebase.initialize_app(config)
bot = telegram.Bot(token=BOT_TOKEN)
db = firebase.database()
pyshort = pyshorteners.Shortener()

# constants
TOTW_URL = "https://fcbc.org.sg/celebration/our-thoughts-this-week"
VOTD_URL = "https://www.bible.com/verse-of-the-day"
CELL_WORD_URL = "https://www.fcbc.org.sg/pastoral-care/4ws-for-cell-groups"
superscript_map = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶",
    "7": "⁷", "8": "⁸", "9": "⁹"}
trans = str.maketrans(
    ''.join(superscript_map.keys()),
    ''.join(superscript_map.values()))
queries_regex = {'book': '^([\w\s]+[a-z])\W(\d+)$', 'verse': '^([\w\s]+[a-z])\W(\d+)\W(\d+)$',
                 'passage': '^([\w\s]+[a-z])\W(\d+)\W(\d+)\W(\d+)$'}
monthConversions = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
                    7: "July", 8: "August", 9: "September", 10: "October", 11: "November",
                    12: "December"}


def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context, *args, **kwargs)

    return command_func


@send_typing_action
def start(update, context):
    bot.send_photo(chat_id=update.message.chat_id, photo=open('background.jpg', 'rb'),
                   caption="Hello {}, welcome to FCBC Telebot✌️. I can do a few things: \n\n😇 /get <bible passage> "
                           "\n🎵 /lyrics <song title> \n🎶 /songs <song artist> \n💌 /votd \n💭 /totw "
                           "\n\n📋 Press /list to see the full list of commands.\n\nℹ️ Press /about to know more about this bot.".format(
                       update.message.from_user.first_name))


@send_typing_action
def getpinfo(update, context):
    user = update.message.from_user.first_name
    message = update.message.text
    nric = " ".join(message.split()[1:]).upper()
    p_info = db.child("pinfo").child(nric).get()
    if nric == "":
        update.message.reply_text("Sorry {}, please enter a valid 4 Digit NRIC".format(user))
    else:
        if nric in db.child("pinfo").get().val():
            address = p_info.val()["address"]
            dob = p_info.val()["dob"]
            name = p_info.val()["name"]
            final_output = "Hi {}, here is your personal information: \n\n<b>{}</b>\n\u2022{}\n\u2022{}".format(user,
                                                                                                                name,
                                                                                                                dob,
                                                                                                                address)
            bot.send_message(chat_id=update.message.chat_id, text=final_output, parse_mode=telegram.ParseMode.HTML)
        else:
            update.message.reply_text("Hi {}, we are unable to retrieve your equipping status, please contact the "
                                      "admin for assistance.")


@send_typing_action
def estatus(update, context):
    user = update.message.from_user.first_name
    message = update.message.text
    nric = " ".join(message.split()[1:]).upper()
    if nric == "":
        update.message.reply_text("Sorry {}, please enter a valid 4 Digit NRIC".format(user))
    else:
        if nric in db.child("estatus").get().val():
            final_output = ""
            name = db.child("pinfo").child(nric).child("name").get()
            equipping = db.child("estatus").child(nric).get()
            final_output += "Hi {}, here is your equipping status: <b>{}</b>\n\n".format(user, name.val())
            for items in equipping.each():
                title = items.val()["title"]
                date = items.val()["date"]
                if "attendance" not in items.val():
                    attendance = "NA"
                else:
                    attendance = items.val()["attendance"]
                final_output += "<b>{}</b>\n\u2022{}\n\u2022{}\n\n".format(title, date, attendance)
            bot.send_message(chat_id=update.message.chat_id, text=final_output, parse_mode=telegram.ParseMode.HTML)
        else:
            update.message.reply_text("Hi {}, we are unable to retrieve your equipping status, please contact the "
                                      "admin for assistance.".format(user))


@send_typing_action
def getBirthdays(update, context):
    user = update.message.from_user.first_name
    chatId = update.message.chat_id
    final_output = "<b>List of birthdays:</b>\n"
    icList = db.child("chat").child(chatId).get()
    if icList.val() is None:
        bot.send_message(chat_id=update.message.chat_id, text="Sorry {}, no birthday records has been added to this "
                                                              "group chat".format(user))
    else:
        birthdays = {}
        for i in icList.each():
            birthdays[i.val()['name']] = i.val()['birthday']
        birthday_sorted = {name: birthday for name, birthday in sorted(birthdays.items(), key=lambda item: item[1])}
        current_day = datetime.datetime.now().day
        current_month = datetime.datetime.now().month
        months_output = ""
        for i in range(1, 13):
            temp_month = monthConversions[i]
            temp_month_output = ""
            for birthday in birthday_sorted:
                dmy = birthday_sorted[birthday].split("-")
                day = int(dmy[0].lstrip('0'))
                month = int(dmy[1])
                get_month = monthConversions[month]  # Prints george
                if get_month == temp_month and month == current_month:
                    temp_month_output += "{} - {}".format(day, birthday)
                    if day == current_day:
                        temp_month_output += " 🎂\n"
                    elif day - current_day > 0:
                        temp_month_output += " ({} day(s) left!)\n".format(day - current_day)
                    else:
                        temp_month_output += "\n"
                elif get_month == temp_month:
                    temp_month_output += "{} - {}\n".format(day, birthday)
            if temp_month_output != "":
                temp_month_output = "\n<b>{}</b>\n".format(temp_month) + temp_month_output
            months_output += temp_month_output
        final_output += months_output
        bot.send_message(chat_id=update.message.chat_id, text=final_output, parse_mode=telegram.ParseMode.HTML)


@send_typing_action
def thoughtOfTheWeek(update, context):
    page = requests.get(TOTW_URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    header = soup.find_all('h1')[0].get_text()
    image = soup.find_all("img")
    name = ""
    content = ""
    hit = soup.find("div", class_="field-content")
    para = hit.find_all('p')
    for i in para:
        content += i.get_text() + "\n\n"
    for i in image:
        src = i["src"]
        if "jpg" in src:
            name = src
    # get the source of the image
    url = "fcbc.org.sg" + name
    content = '<b>Thought of the week</b>\n\n<a href="{}">{}</a>{}'.format(url, header, content)
    bot.send_message(chat_id=update.message.chat_id,
                     text=content,
                     parse_mode=telegram.ParseMode.HTML)


@send_typing_action
def getTopSongs(update, context):
    message = update.message.text
    user = update.message.from_user.first_name
    query = " ".join(message.split()[1:])
    context.chat_data['lyrics_data'] = {}
    url = 'https://www.musixmatch.com/search/{}/tracks'.format(query)
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0'}

    soup = BeautifulSoup(requests.get(url, headers=headers).content, 'html.parser')

    if soup.find(class_="empty"):
        bot.send_message(chat_id=update.message.chat_id,
                         text="Sorry {}, we couldn't find what you were looking for.".format(user))
        return

    output_top_tracks = "<b>Top search results on {}:</b>\n\n".format(query)
    for t, s in list(zip(soup.select('.media-card-title'), soup.select('.media-card-subtitle')))[:5]:
        title = t.text
        artist = s.text
        href = t.a['href']
        uuid = str(uuid4()).upper()[:4]
        output_top_tracks = output_top_tracks + "💿 " + title + "\n" + "🎤 " + artist + "\n" + "/lyric3" + uuid + "\n\n"
        # store in temp db
        context.chat_data['lyrics_data']["lyric3" + uuid] = {'title': title, 'artist': artist, 'href': href}
    bot.send_message(chat_id=update.message.chat_id,
                     text=output_top_tracks,
                     parse_mode=telegram.ParseMode.HTML)


@send_typing_action
def getSongLyrics(update, context):
    message = update.message.text
    user = update.message.from_user
    query = " ".join(message.split()[1:])
    # query = 'ride'
    search_page = requests.get("https://www.musixmatch.com/search/{}/tracks".format(query),
                               headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(search_page.content, 'html.parser')

    if soup.find(class_="empty"):
        bot.send_message(chat_id=update.message.chat_id,
                         text="Sorry {}, we couldn't find what you were looking for.".format(user.first_name))
        return
    best_result = soup.find(class_="showArtist showCoverart")
    song_title = best_result.find("a", class_="title").get_text()
    song_artist = best_result.find("a", class_="artist").get_text()
    song_href = best_result.find("a", href=True)['href']
    # print(href)
    lyrics_page = requests.get("https://www.musixmatch.com{}".format(song_href), headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(lyrics_page.content, 'html.parser')
    lyrics_content = soup.find_all(class_="mxm-lyrics__content")
    lyrics_output = "<b>{} by {}</b> 🎵\n\n".format(song_title, song_artist)
    for lyrics in lyrics_content:
        lyrics_output = lyrics_output + lyrics.get_text() + "\n"
    bot.send_message(chat_id=update.message.chat_id, text=lyrics_output, parse_mode=telegram.ParseMode.HTML)


@send_typing_action
def scrapeLyrics(update, context):
    message = update.message.text
    query = message[1:]
    song_info = context.chat_data['lyrics_data'].get(query, False)
    lyrics_page = requests.get("https://www.musixmatch.com{}".format(song_info['href']),
                               headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(lyrics_page.content, 'html.parser')
    lyrics_content = soup.find_all(class_="mxm-lyrics__content")
    lyrics_output = "{} by {} 🎵\n\n".format(song_info['title'], song_info['artist'])
    for lyrics in lyrics_content:
        lyrics_output = lyrics_output + lyrics.get_text() + "\n"
    update.message.reply_text(lyrics_output)


@send_typing_action
def verseOfTheDay(update, context):
    user = update.message.from_user
    page = requests.get(VOTD_URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    verse = soup.find(class_="usfm fw7 mt0 mb0 gray f7 ttu").get_text()
    verse_query = re.findall('(.+) ', verse)[0]
    # print(verse_query)
    returned_output = formatQuery(verse_query)
    if returned_output == -1 or returned_output is None:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Sorry {}, something is wrong, please contact the admin".format(user.first_name))
        return
    verse_output = "<b>Verse of the Day</b>" + "\n\n" + returned_output
    # print(verse_output)
    bot.send_message(chat_id=update.message.chat_id,
                     text=verse_output,
                     parse_mode=telegram.ParseMode.HTML)


@send_typing_action
def getBibleVerses(update, context):
    # chapter - https://www.biblestudytools.com/psalms/1.html ([\w\s]+[a-z])\W(\d+)
    # single verse - https://www.biblestudytools.com/psalms/1-1.html ([\w\s]+[a-z])\W(\d+)\W(\d+)
    # passage - https://www.biblestudytools.com/psalms/passage/?q=psalm+1:1-4 ([\w\s]+[a-z])\W(\d+)\W(\d+)\W(\d+)
    message = update.message.text
    user = update.message.from_user
    query = " ".join(message.split()[1:])
    if query == "":
        update.message.reply_text("Sorry {}, please enter a bible verse or passage".format(user.first_name))
    else:
        returned_output = formatQuery(query)
        if returned_output == -1:
            bot.send_message(chat_id=update.message.chat_id,
                             text="Sorry {}, I have detected an incorrect passage format, here are a few "
                                  "examples:\n\n\u2022john "
                                  "3:16\n\u2022jeremiah 29 11\n\u20221 cor 13:4-13".format(user.first_name))
            return
        elif returned_output is None:
            bot.send_message(chat_id=update.message.chat_id,
                             text="Sorry {}, we couldn't find what you were looking for".format(user.first_name),
                             parse_mode=telegram.ParseMode.HTML)
            return
        content_output_1, content_output_2 = checkMaximumLength(returned_output)
        if content_output_2 == "":
            bot.send_message(chat_id=update.message.chat_id,
                             text=content_output_1,
                             parse_mode=telegram.ParseMode.HTML)
        else:
            content_list = [content_output_1, content_output_2]
            for i in content_list:
                bot.send_message(chat_id=update.message.chat_id,
                                 text=i,
                                 parse_mode=telegram.ParseMode.HTML)


def apiBible(query):
    output = ""
    search_page = requests.get(query, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(search_page.content, 'html.parser')
    content = soup.find(class_='scripture verse-padding')
    if content == None:
        return None
    title = soup.find('h1')
    output += "<b>{} (NIV)</b>".format(title.text)
    content = soup.find(class_='scripture verse-padding')
    verse_content = content.find_all(re.compile('h2|div'))
    for idx, obj in enumerate(verse_content):
        obj_name = obj.name
        if obj_name == 'h2':
            if verse_content[idx - 1].name != 'h2':
                output += "\n\n"
            output += '<b>{}</b>\n\n'.format(obj.text.strip())
        elif obj_name == 'div':
            unwanted = obj.find('a')
            if unwanted != None:
                unwanted.extract()
            verse_num_obj = obj.find('span', class_='verse-number')
            verse_num = verse_num_obj.getText().strip()
            verse_obj = obj.find('span', class_=re.compile('verse-{}'.format(verse_num)))
            verse = verse_obj.getText().strip()
            if verse_content[idx - 1].name != 'h2':
                if idx == 0:
                    output += "\n\n"
                else:
                    output += " "
            output += '{}'.format(verse_num.translate(trans))
            output += verse
    return output


def formatQuery(query):
    if re.search(queries_regex['book'], query) is not None:
        query_content = re.findall(queries_regex['book'], query)[0]
        return apiBible(
            "https://www.biblestudytools.com/{}/{}.html".format(query_content[0], query_content[1]))
    elif re.search(queries_regex['verse'], query) is not None:
        query_content = re.findall(queries_regex['verse'], query)[0]
        return apiBible(
            "https://www.biblestudytools.com/{}/{}-{}.html".format(query_content[0], query_content[1],
                                                                   query_content[2]))
    elif re.search(queries_regex['passage'], query) is not None:
        query_content = re.findall(queries_regex['passage'], query)[0]
        return apiBible(
            "https://www.biblestudytools.com/{}/passage/?q={}+{}:{}-{}".format(query_content[0], query_content[0],
                                                                               query_content[1], query_content[2],
                                                                               query_content[3]))
    else:
        return -1


def checkMaximumLength(content_output):
    content_output_overflow = ""
    if len(content_output) > 4096:
        content_output_1, content_output_overflow = content_output[:4096], content_output[4096:]
        return content_output_1, content_output_overflow
    else:
        return content_output, content_output_overflow


@send_typing_action
def get4ws(update, context):
    page = requests.get(CELL_WORD_URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    pdfs = soup.find(class_="views-field views-field-field-pdfs")
    href = pdfs.find('a', href=True)['href']
    caption = "<b>4Ws For Cell Groups</b>\n\n" + pdfs.find('a', href=True).get_text()
    # document = open(href, 'rb')
    bot.sendDocument(chat_id=update.message.chat_id, document=href, caption=caption, parse_mode=telegram.ParseMode.HTML)


@send_typing_action
def addBirthdayReminder(update, context):
    user = update.message.from_user
    message = update.message.text
    chatId = update.message.chat_id
    birthday = " ".join(message.split()[1:]).upper()
    # check for birthday format
    searchResult = re.search("^(\d{2})-(\d{2})-(\d{4})$", birthday)
    if searchResult is None:
        update.message.reply_text(
            "Sorry {}, I have detected an incorrect date format, please enter like this: dd-mm-yyyy".format(
                user.first_name))
    else:
        # add to chat node
        chat_details = {'name': user.first_name, 'birthday': birthday, 'userId': user.id, 'chatId': chatId}
        db.child("chat").child(chatId).child(user.id).set(chat_details)
        # add to reminder node
        birthday_details = {'name': user.first_name, 'birthday': birthday, 'userId': user.id, 'chatIds': [chatId]}
        dbPath = db.child("reminder").child(user.id).get().val()
        if dbPath is None:
            db.child("reminder").child(user.id).set(birthday_details)
            update.message.reply_text("Thank you {}, your record has been saved".format(user.first_name))
        elif birthday != dbPath['birthday']:
            db.child("reminder").child(user.id).set(birthday_details)
            update.message.reply_text("Hi {}, your birthday record is sucessfully changed".format(user.first_name))
        else:
            userDetails = db.child("reminder").child(user.id).get().val()
            if chatId not in userDetails['chatIds']:
                updatedIds = userDetails['chatIds']
                updatedIds.append(chatId)
                birthday_details['chatIds'] = updatedIds
                db.child("reminder").child(user.id).update(birthday_details)
                update.message.reply_text("Thank you {}, your record has been saved".format(user.first_name))
            else:
                update.message.reply_text("Hi {}, your record is already saved".format(user.first_name))

@send_typing_action
def getSermons(update, context):
    page = requests.get("https://fcbc.org.sg/celebration/media-downloads")
    soup = BeautifulSoup(page.content, 'html.parser')
    link = soup.find(class_="views-row views-row-1 views-row-odd views-row-first views-row-last")
    title = link.findAll('td', {'valign': 'top'}, limit=15)  # change link to soup to get all
    composite_list = [title[x:x + 5] for x in range(0, len(title), 5)]
    output = ""
    for item in composite_list:
        for i, o in enumerate(item):
            if i == 0:
                output += "\n📅" + o.text
            elif i == 1:
                output += "\n📖" + o.text
            elif i == 2:
                output += "\n👔" + o.text
            elif i == 4:
                link = re.findall("<a href=\"(.+)\">", str(o))
                output += "\n📹" + pyshort.tinyurl.short(str(link[0])) + "\n\n"
    f_output = "<b>English Sermons</b> ✝️" + "\n" + output
    bot.send_message(chat_id=update.message.chat_id, text=f_output, parse_mode=telegram.ParseMode.HTML)


@send_typing_action
def listOfCommands(update, context):
    bot.send_message(chat_id=update.message.chat_id, text="in progress")


@send_typing_action
def unknownCommand(update, context):
    user = update.message.from_user
    bot.send_message(chat_id=update.message.chat_id,
                     text="Sorry {}, this is an invalid command, click /list to see all available commands".format(
                         user.first_name))


@send_typing_action
def specialMessage(update, context):
    message = update.message.text
    user = update.message.from_user
    name = " ".join(message.split()[1:]).lower()
    if name == "":
        bot.send_message(chat_id=update.message.chat_id,
                         text="Sorry {}, please input a name".format(user.first_name))
    else:
        message = db.child('reminder').child(user.id).child('message').get().val()
        if message == None:
            message = "Have a good day {}!".format(user.first_name)
        bot.send_message(chat_id=update.message.chat_id,
                         text=message)

@send_typing_action
def about(update, context):
    bot.send_photo(chat_id=update.message.chat_id, photo=open('aboutus.jpg', 'rb'),
                   caption="FCBC Telebot was created to provide quick access to cell group essentials such as looking "
                           "up bible verses, search for worship song lyrics, reminder for birthdays and more!\n\n"
                           "Meet the creators of FCBC Telebot: "
                           "👨 <b>Jiawen</b> (@jiawenlor)\n💼 Biz Whiz at SMU\n\n"
                           "👩 <b>Zhi Xin</b> (@zx0123)\n💻 Programmer at NYP\n\n"
                           "👨 Joshua (@happpyfuntimess)\n💡 Electronics guy at ITE East\n\n"
                           "👨 Amadaeus (@tehontherocks)\n🛠️ Engineer at SP\n\n"
                           "👨  Gerald (@Geraldlim95)\n🤓 Hardcore nerd at SUTD\n\n"
                           "If you have any feedback or suggestion, please feel free to pm any of us!",
                            parse_mode=telegram.ParseMode.HTML)

@send_typing_action
def listOfCommands(update, context):
    bot.send_message(chat_id=update.message.chat_id,
                     text="1️⃣ /pinfo <Last 4 digits of NRIC>\nRetrieves your personal information\n\n"
                          "2️⃣ /estatus <Last 4 digits of NRIC>\nRetrieves your equipping status\n\n"
                          "3️⃣ /totw\nRetireves the thought of the week by FCBC\n\n"
                          "4️⃣ /votd\nRetrieves the verse of the day by YouVersion\n\n"
                          "5️⃣ /lyrics <Song title/artist>\nRetrieves the lyrics the top search result for the song title or artist input\n\n"
                          "6️⃣ /songs <Song title/artist>\nRetrieves the top 5 search results for the song title or artist input\n\n"
                          "7️⃣ /get <Bible verse/passage>\nRetrieves bible verse or passage in NIV\n\n"
                          "8️⃣ /4ws\nRetrieves the latest 4Ws for cell leaders\n\n"
                          "9️⃣ /birthdays\nRetrieves all users' birthday in the group chat\n\n"
                          "1️⃣0️⃣ /remind <dd-mm-yyyy>\nAdd user's birthday to the group chat\n\n"
                          "1️⃣1️⃣ /sermons\nRetrieves latest sermon video links\n\n"
                          "1️⃣2️⃣ /list\nRetrieves a list of all acceptable commands\n\n"
                          "ℹ️ /about Information about FCBC Telebot"
                          "😉 /fcbc <name>\nEnter your name for a special message from the administrators")


def main():
    updater = Updater(BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('pinfo', getpinfo))
    dp.add_handler(CommandHandler('estatus', estatus))
    dp.add_handler((CommandHandler('totw', thoughtOfTheWeek)))
    dp.add_handler((CommandHandler('votd', verseOfTheDay)))
    dp.add_handler((CommandHandler('songs', getTopSongs)))
    dp.add_handler((CommandHandler('lyrics', getSongLyrics)))
    dp.add_handler((MessageHandler(Filters.regex('lyric3.+'), scrapeLyrics)))
    dp.add_handler((CommandHandler('get', getBibleVerses)))
    dp.add_handler((CommandHandler('4ws', get4ws)))
    dp.add_handler((CommandHandler('birthdays', getBirthdays)))
    dp.add_handler((CommandHandler('list', listOfCommands)))
    dp.add_handler((CommandHandler('remind', addBirthdayReminder)))
    dp.add_handler((CommandHandler('fcbc', specialMessage)))
    dp.add_handler((CommandHandler('list', listOfCommands)))
    dp.add_handler((CommandHandler('sermons', getSermons)))
    dp.add_handler((CommandHandler('about', about)))
    dp.add_handler((MessageHandler(Filters.command, unknownCommand)))
    # Start the Bot
    updater.start_polling()

    # updater.start_webhook(listen="0.0.0.0",
    #                       port=PORT,
    #                       url_path=BOT_TOKEN)
    # updater.bot.set_webhook("https://fcbctelebot.herokuapp.com/" + BOT_TOKEN)
    # Run the bot until you press Ctrl-C or the process rec eives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
#     message = db.child('reminder').child("260677589").child('message').get().val()
#     print(message)
