import telegram
from telegram.ext import Updater, CommandHandler, Filters, MessageHandler
import pyrebase
from telegram import ChatAction, ParseMode
from functools import wraps
from bs4 import BeautifulSoup
import requests
from uuid import uuid4
import re
import abbreviation
import json
import logging
import datetime


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

superscript_map = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶",
    "7": "⁷", "8": "⁸", "9": "⁹"}

trans = str.maketrans(
        ''.join(superscript_map.keys()),
        ''.join(superscript_map.values()))

firebase = pyrebase.initialize_app(config)

API_KEY = "1232203331:AAGRJxNgfTclfie4UQlglsofl2uzBR00-TY"
bot = telegram.Bot(token = '1232203331:AAGRJxNgfTclfie4UQlglsofl2uzBR00-TY')

db = firebase.database()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context, *args, **kwargs)

    return command_func

@send_typing_action
def start(update, context):
    context.chat_data["teamId"] = ""
    bot.send_photo(chat_id=update.message.chat_id, photo=open('unnamed.jpg', 'rb'), caption =  " Hello " + update.message.from_user.first_name + ", "+ "\n\n" + "Welcome !")
                   # + "\n\n" + "This bot is able to do a few things:" + "\n\n" + "1. Fetch your current equipping status and personal information"
                   # + "\n\n" + "2. Get Bible Verses or Verse of the Day in NIV version  " + "\n\n" +
                   # "3. Get you the top 5 songs on the artist you search" + "\n\n" +
                   # "4. Get you the lyrics of the songs you search" + "\n\n" + "5. Get FCBC's Thought of the Week and 4Ws"
                   # "\n\n\n" + "To gain access to your equipping status, Kindly login with your cell leader's ID" +
                   # "\n\n" + "Start by /login <cell leader's unique ID>" + "\n" + "Followed by /estatus <last 3 digits and last letter of your NRIC> to access your equipping status" +
                   # "\n" + "or /pinfo <last 3 digits and last letter of your NRIC> to gain access to your personal information" + "\n\n" +
                   # "To access the top 5 songs simply /songs <song artist>" + "\n" + "To gain access to the song lyrics simply /lyrics <song title>" + "\n" +
                   #  "To gain access to Bible Verses simply /get <your bible verse/passage> " +  "\n" + "To gain access to FCBC's Thought of the Week simply /TOTW " + "\n"
                   # "To gain access to FCBC's 4Ws simply /get4Ws" + "\n" + "To gain access to Verse of the Day simply /votd" + "\n\n" + "Have fun and enjoy using this bot !")
# need to have the exact functions detailed down


@send_typing_action
def loginChms(update, context):
    db = firebase.database()
    message = update.message.text
    key = " ".join(message.split()[1:])
    storeChatId(update, key)
    if key == "":
        update.message.reply_text("Please try again like this /login <password>.")
    result = db.child("chms").get()
    found_id = False
    for i in result.each():
        if key == i.key():
            # {key: value}
            context.chat_data["teamId"] = key
            found_id = True
            break
    if found_id:
        update.message.reply_text("You have login successfully!")
    else:
        update.message.reply_text("Invalid credentials, please try again.")

def storeChatId(update, teamId):
    chatId = update.message.chat_id
    data = {"chatid": chatId}
    db.child("chatdetails").child(teamId).set(data)


@send_typing_action
def getpinfo(update, context):
    # /pinfo 808E
    db = firebase.database()
    teamId = context.chat_data['teamId']
    message = update.message.text
    nric = " ".join(message.split()[1:]).upper()
    p_info = db.child("chms").child(teamId).child(nric).child("pinfo").get()
    list_of_nric = db.child("chms").child(teamId).get()
    found_nric = False
    if teamId == "":
        update.message.reply_text("Login unsuccessful." + "\n" + "Kindly Login to proceed" + "😔")
    elif nric == "":
        update.message.reply_text("Enter a valid 4 Digit NRIC")
    else:
        for keys in list_of_nric.each():
            if nric == keys.key():
                address = p_info.val()["address"]
                dob = p_info.val()["dob"]
                name = p_info.val()["name"]
                final_output = "<b>{}</b>\n\u2022{}\n\u2022{}".format(name, dob, address)
                found_nric = True
                break
        if found_nric:
            bot.send_message(chat_id=update.message.chat_id, text=final_output, parse_mode=telegram.ParseMode.HTML)
        else:
            update.message.reply_text("User does not exist." + "\n" + "Kindly check the last 4 digits of your NRIC")


@send_typing_action
def estatus(update, context):
    # estatus 0812E
    db = firebase.database()
    teamId = context.chat_data['teamId']
    list_of_nric = db.child("chms").child(teamId).get()
    message = update.message.text
    nric = " ".join(message.split()[1:]).upper()
    found_nric = False
    if teamId == "":
            update.message.reply_text("Login unsuccessful." + "\n" + "Kindly Login to proceed" + "😔")
    elif nric == "":
            update.message.reply_text("Enter a valid 4 Digit NRIC")
    else:
        for keys in list_of_nric.each():
                if nric == keys.key():
                    final_output = ""
                    name = db.child("chms").child(teamId).child(nric).child("pinfo").child("name").get()
                    equipping = db.child("chms").child(teamId).child(nric).child("estatus").get()
                    final_output += "<b>{}</b>\n\n".format(name.val())
                    for items in equipping.each():
                        title = items.val()["title"]
                        date = items.val()["date"]
                        if "attendance" not in items.val():
                            attendance = "NA"
                        else:
                            attendance = items.val()["attendance"]
                        final_output += "<b>{}</b>\n\u2022{}\n\u2022{}\n\n".format(title, date, attendance)
                    found_nric = True
                    break
        if found_nric:
            # update.message.reply_text(final_output, parse_mode=telegram.ParseMode.MARKDOWN_V2)
            print(final_output)
            bot.send_message(chat_id=update.message.chat_id, text = final_output, parse_mode=telegram.ParseMode.HTML)
        else:
            update.message.reply_text("User does not exist." + "\n" + "Kindly check the last 4 digits of your NRIC")

@send_typing_action
def getBirthdays(update, context):
    # /birthdays
    db = firebase.database()
    teamId = context.chat_data['teamId']
    get_IC = db.child("chms").child(teamId).get()
    monthConversions = {
        "01": "January",
        "02": "February",
        "03": "March",
        "04": "April",
        "05": "May",
        "06": "June",
        "07": "July",
        "08": "August",
        "09": "September",
        "10": "October",
        "11": "November",
        "12": "December",
    }
    birthdays = {}
    if teamId == "":
        update.message.reply_text("Login unsuccessful." + "\n" + "Kindly Login to proceed" + "😔")
    else:
        for i in get_IC.each():
            p_info = db.child("chms").child(teamId).child(i.key()).child("pinfo").get()
            name = p_info.val()['name']
            birthday = p_info.val()["dob"].replace("-", "")[4:]
            birthdays[name] = birthday  # {gerald: 654837563, josh: 5454353}
        birthday_sorted = {name: birthday for name, birthday in sorted(birthdays.items(), key=lambda item: item[1])}
        output_2 = ""
        for j in birthday_sorted:
            month = birthday_sorted[j][0:2]
            day = birthday_sorted[j][2:4]
            name = j
            if month[0] == "0":
                month_nozero = month[1]
            else:
                month_nozero = month
            now = datetime.datetime.now()
            bday = datetime.date(now.year, int(month_nozero), int(day))
            current_day = datetime.date.today()
            current_month = datetime.datetime.now().month
            till_bday = bday - current_day
            if till_bday.days < 0:
                output_1 = name
            elif till_bday.days == 0:
                output_1 = "Happy Birthday " + name + "!🥳🎂"
            elif int(month_nozero) == current_month:
                output_1 = name + " (" + str(till_bday.days) + " days left!)"
            else:
                output_1 = name
            birthday_expression = day + " " + monthConversions[month]
            output_2 += "<b>{}</b>\n{}\n\n".format(output_1, birthday_expression)
        final_output = "List of Birthdays!🥳🎂" + "\n\n" + output_2
        bot.send_message(chat_id=update.message.chat_id, text=final_output, parse_mode=telegram.ParseMode.HTML)

@send_typing_action
def thoughtOfTheWeek(update, context):
    page = requests.get("https://fcbc.org.sg/celebration/our-thoughts-this-week")
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
    #combining fcbc.org.sg to source of the image
    content = '<b>Thought of the week</b>\n\n<a href="{}">{}</a>{}'.format(url, header, content)
    bot.send_message(chat_id=update.message.chat_id,
                     text=content,
                     parse_mode=telegram.ParseMode.HTML)    #must use update.message.chat_id to send picture using telegram bot

@send_typing_action
def verseOfTheDay(update, context):
    page = requests.get("https://www.bible.com/verse-of-the-day")
    soup = BeautifulSoup(page.content, 'html.parser')
    verse = soup.find(class_="usfm fw7 mt0 mb0 gray f7 ttu").get_text()
    verse_query = re.findall('(.+) ', verse)[0]
    scriptures = list(re.findall('([\w\s]+[a-z])\W?(\d+)\W?(\d*)\W?(\d*)', verse_query)[0])
    scriptures = list(filter(lambda a: a != '', scriptures))
    book_id = [key for key, value in abbreviation.book_ids.items() if scriptures[0].lower() in value][0]
    bible_query = ""
    # passage
    if len(scriptures) == 4:
        bible_query = "{}.{}.{}-{}.{}.{}".format(book_id, scriptures[1], scriptures[2], book_id, scriptures[1],
                                                 scriptures[3])
    # verse
    elif len(scriptures) == 3:
        bible_query = "{}.{}.{}".format(book_id, scriptures[1], scriptures[2])
    elif len(scriptures) == 2:
        bible_query = "{}.{}".format(book_id, scriptures[1])
    content_output = apiBible(bible_query)
    verse_output = "<b>Verse of the Day</b>" + "\n\n" + content_output
    bot.send_message(chat_id=update.message.chat_id,
                     text=verse_output,
                     parse_mode=telegram.ParseMode.HTML)


def apiBible(query):
    response = requests.get(
        'https://api.scripture.api.bible/v1/bibles/78a9f6124f344018-01/passages/{'
        '}?content-type=json&include-notes=false&include-titles=true&include-chapter-numbers=false&include-verse'
        '-numbers=true&include-verse-spans=false&use-org-id=false'.format(
            query),
        headers={'api-key': '643c03c56dfaef821ef0247f1aa2dde0'})
    json_response = response.json()
    if 'statusCode' in json_response and json_response['statusCode'] == 404:
        return False
    contents = json_response['data']['content']
    reference = json_response['data']['reference']
    content_output = "<b>{} (NIV)</b>\n\n".format(reference)
    for content in contents:
        if content['attrs']['style'] == 's1' or content['attrs']['style'] == 'ms' or content['attrs'][
            'style'] == 'mr' or content['attrs']['style'] == 'cl' or content['attrs']['style'] == 'd' or \
                content['attrs']['style'] == 'sp':
            if len(content['items']) != 0:
                content_output += "\n<b>{}</b>\n\n".format(content['items'][0]['text'])
        elif content['attrs']['style'] == 'b':
            pass
        elif content['attrs']['style'] == 'p' or content['attrs']['style'] == 'q1' or content['attrs']['style'] == 'q2':
            for item in content['items']:
                if 'style' in item['attrs']:
                    if item['attrs']['style'] == 'v':
                        content_output += item['attrs']['number'].translate(trans)
                    elif item['attrs']['style'] == 'wj' or item['attrs']['style'] == 'nd':
                        content_output += item['items'][0]['text']
                elif 'text' in item:
                    content_output += item['text']
            content_output += additional_output(content['attrs']['style'])
    temp_content_output = content_output.split('\n')
    cleaned_content_output = "\n".join(
        [v for i, v in enumerate(temp_content_output) if i == 0 or v != temp_content_output[i - 1]])
    return cleaned_content_output

@send_typing_action
def getTopSongs(update, context):
    message = update.message.text
    query = " ".join(message.split()[1:])
    # clear chat lyrics data
    context.chat_data['lyrics_data'] = {}
    # query = 'marry'
    search_page = requests.get("https://www.musixmatch.com/search/{}/tracks".format(query), headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(search_page.content, 'html.parser')
    if soup.find(class_="empty"):
        bot.send_message(chat_id=update.message.chat_id,
                         text="Sorry {}, we couldn't find what you were looking for.".format(user.first_name))
        return
    top_tracks = soup.find_all(class_="showArtist showCoverart", limit = 5)
    output_top_tracks = "<b>Top search results on {}:</b>\n\n".format(query)
    for track in top_tracks:
        title = track.find("a", class_="title").get_text()
        artist = track.find("a", class_="artist").get_text()
        href = track.find("a", href=True)['href']
        # print(href)
        uuid = str(uuid4()).upper()[:4]
        output_top_tracks = output_top_tracks + "💿 " + title + "\n" + "🎤 " + artist + "\n" + "/lyric3" + uuid  + "\n\n"
        # store in temp db
        context.chat_data['lyrics_data']["lyric3" + uuid] = {'title': title, 'artist': artist, 'href': href}
    # print(output_top_tracks)
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
        bot.send_message(chat_id=update.message.chat_id, text="Sorry {}, we couldn't find what you were looking for.".format(user.first_name))
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
    print(query)
    song_info = context.chat_data['lyrics_data'].get(query, False)
    print(song_info)
    lyrics_page = requests.get("https://www.musixmatch.com{}".format(song_info['href']), headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(lyrics_page.content, 'html.parser')
    lyrics_content = soup.find_all(class_="mxm-lyrics__content")
    lyrics_output = "{} by {} 🎵\n\n".format(song_info['title'], song_info['artist'])
    for lyrics in lyrics_content:
        lyrics_output = lyrics_output + lyrics.get_text() + "\n"
    update.message.reply_text(lyrics_output)

@send_typing_action
def getBibleVerses(update, context):
    message = update.message.text
    user = update.message.from_user
    query = message.split(" ", 1)[1]
    scriptures = list(re.findall('([\w\s]+[a-z])\W?(\d+)\W?(\d*)\W?(\d*)', query)[0])
    scriptures = list(filter(lambda a: a != '', scriptures))
    book_id = [key for key, value in abbreviation.book_ids.items() if scriptures[0].lower() in value][0]
    bible_query = ""
    # passage
    if len(scriptures) == 4:
        bible_query = "{}.{}.{}-{}.{}.{}".format(book_id, scriptures[1], scriptures[2], book_id, scriptures[1],
                                                 scriptures[3])
    # verse
    elif len(scriptures) == 3:
        bible_query = "{}.{}.{}".format(book_id, scriptures[1], scriptures[2])
    elif len(scriptures) == 2:
        bible_query = "{}.{}".format(book_id, scriptures[1])
    content_output = apiBible(bible_query)
    if content_output is False:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Sorry {}, we cannot find what you're looking for.".format(user.first_name))
    else:
        bot.send_message(chat_id=update.message.chat_id,
                        text=content_output,
                        parse_mode=telegram.ParseMode.HTML)


def additional_output(style):
    if style == 'p':
        return  '\n\n'
    if style == 'q1':
        return '\n '
    if style == 'q2':
        return '\n'


@send_typing_action
def get4ws(update, context):
    page = requests.get("https://www.fcbc.org.sg/pastoral-care/4ws-for-cell-groups")
    soup = BeautifulSoup(page.content, 'html.parser')
    pdfs = soup.find(class_="views-field views-field-field-pdfs")
    href = pdfs.find('a', href=True)['href']
    caption = "<b>4Ws For Cell Groups</b>\n\n" + pdfs.find('a', href=True).get_text()
    # document = open(href, 'rb')
    bot.sendDocument(chat_id=update.message.chat_id, document=href, caption=caption, parse_mode=telegram.ParseMode.HTML)

@send_typing_action
def getSermons(update, context):
    page = requests.get("https://fcbc.org.sg/celebration/media-downloads")
    soup = BeautifulSoup(page.content, 'html.parser')
    link = soup.find(class_="views-row views-row-1 views-row-odd views-row-first views-row-last")
    title = link.findAll('td', {'valign': 'top'})  # change link to soup to get all
    output = ""
    f_output = ""
    for i in title[0:15]:
        extract = i.findAll("a", href=True)
        text = i.text
        output += text + "\n"
        for z in extract:
            if "mp4" in z.get("href"):
                output += "Video:" + z.get("href") + "\n\n"
            else:
                output += "Audio:" + z.get("href") + "\n"
    f_output = "English Sermons ✝️" + "\n\n"+ output
    bot.send_message(chat_id=update.message.chat_id, text=f_output, parse_mode=telegram.ParseMode.HTML)


def main():
    updater = Updater(API_KEY, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('pinfo', getpinfo))
    dp.add_handler(CommandHandler('estatus', estatus))
    dp.add_handler((CommandHandler('login', loginChms)))
    dp.add_handler((CommandHandler('totw', thoughtOfTheWeek)))
    dp.add_handler((CommandHandler('votd', verseOfTheDay)))
    dp.add_handler((CommandHandler('songs', getTopSongs)))
    dp.add_handler((CommandHandler('lyrics', getSongLyrics)))
    dp.add_handler((MessageHandler(Filters.regex('lyric3.+'), scrapeLyrics)))
    dp.add_handler((CommandHandler('get', getBibleVerses)))
    dp.add_handler((CommandHandler('4ws', get4ws)))
    dp.add_handler((CommandHandler('birthdays', getBirthdays)))
    dp.add_handler((CommandHandler('sermons', getSermons)))
    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()


    #commands
    # pinfo - retreives your personal information
    # estatus - retreives your equipping status
    # totw - thought of the week
    # votd - verse of the day
    # lyrics - retrieves lyrics of a song
    # songs - retrieves top songs of an artist
    # get - retrieves bible verse or passage
    # 4ws - retrieves 4Ws for cell group







