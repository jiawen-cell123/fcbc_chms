import telegram
from telegram.ext import Updater, CommandHandler, Filters, MessageHandler
import pyrebase
from telegram import ChatAction
from functools import wraps
from bs4 import BeautifulSoup
import requests
from uuid import uuid4
import re
import abbreviation
import json


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
    context.chat_data["teamId"] = ""
    bot.send_photo(chat_id=update.message.chat_id, photo="https://fcbc.org.sg/sites/default/files/fcbc_logo.jpg",caption="Welcome to FCBC CHMS Bot"+"\n"+"How can I help you ?" )

@send_typing_action
def loginChms(update, context):
    # /loginChms 812E06111995
    db = firebase.database()
    message = update.message.text
    key = " ".join(message.split()[1:])
    print(key)
    result = db.child("chms").get()
    found_id = False
    for i in result.each():
        if key == i.key():
            # {key: value}
            context.chat_data["teamId"] = key
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
    db = firebase.database()
    teamId = context.chat_data['teamId']
    if teamId == "":
            update.message.reply_text("Login unsuccessful." + "\n" + "Kindly Login to proceed" + "😔")
    else:
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
    page = requests.get("https://www.bible.com/verse-of-the-day")
    soup = BeautifulSoup(page.content, 'html.parser')
    verse = soup.find_all(class_="verse-wrapper ml1 mr1 mt4 mb4")
    verse_output = ""
    for i in verse:
        header = soup.find("p", class_="usfm fw7 mt0 mb0 gray f7 ttu").get_text()
        text = soup.find("p", class_="near-black mt0 mb2").get_text()
    verse_output = "Verse of the Day" + "\n\n" + header + "\n\n" + text
    print(verse_output)
    update.message.reply_text(verse_output)

def apiBible(query):
    response = requests.get(
        'https://api.scripture.api.bible/v1/bibles/78a9f6124f344018-01/passages/{'
        '}?content-type=json&include-notes=false&include-titles=true&include-chapter-numbers=false&include-verse'
        '-numbers=true&include-verse-spans=false&use-org-id=false'.format(
            query),
        headers={'api-key': '643c03c56dfaef821ef0247f1aa2dde0'})
    json_response = response.json()
    contents = json_response['data']['content']
    content_output = ""
    for content in contents:
        if content['attrs']['style'] == 's1' or content['attrs']['style'] == 'ms' or content['attrs'][
            'style'] == 'mr' or content['attrs']['style'] == 'cl' or content['attrs']['style'] == 'd' or \
                content['attrs']['style'] == 'sp':
            if len(content['items']) != 0:
                content_output += "\n" + content['items'][0]['text'] + "\n\n"
        elif content['attrs']['style'] == 'b':
            pass
        elif content['attrs']['style'] == 'p' or content['attrs']['style'] == 'q1' or content['attrs']['style'] == 'q2':
            for item in content['items']:
                if 'style' in item['attrs']:
                    if item['attrs']['style'] == 'v':
                        content_output += item['attrs']['number']
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
    query = message.split()[1]
    # clear chat lyrics data
    context.chat_data['lyrics_data'] = {}
    # query = 'marry'
    search_page = requests.get("https://www.musixmatch.com/search/{}/tracks".format(query), headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(search_page.content, 'html.parser')
    top_tracks = soup.find_all(class_="showArtist showCoverart", limit = 5)
    output_top_tracks = ""
    for track in top_tracks:
        title = track.find("a", class_="title").get_text()
        artist = track.find("a", class_="artist").get_text()
        href = track.find("a", href=True)['href']
        # print(href)
        uuid = str(uuid4()).upper()[:4]
        output_top_tracks = output_top_tracks + title + "\n" + artist + "\n" + "/lyric3" + uuid  + "\n\n"
        # store in temp db
        context.chat_data['lyrics_data']["lyric3" + uuid] = {'title': title, 'artist': artist, 'href': href}
    # print(output_top_tracks)
    update.message.reply_text(output_top_tracks)

@send_typing_action
def getSongLyrics(update, context):
    message = update.message.text
    query = message.split()[1]
    print(query)
    # query = 'ride'
    search_page = requests.get("https://www.musixmatch.com/search/{}/tracks".format(query),
                               headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(search_page.content, 'html.parser')
    best_result = soup.find(class_="showArtist showCoverart")
    song_title = best_result.find("a", class_="title").get_text()
    song_artist = best_result.find("a", class_="artist").get_text()
    song_href = best_result.find("a", href=True)['href']
    # print(href)
    lyrics_page = requests.get("https://www.musixmatch.com{}".format(song_href), headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(lyrics_page.content, 'html.parser')
    lyrics_content = soup.find_all(class_="mxm-lyrics__content")
    lyrics_output = "{} by {}\n\n".format(song_title, song_artist)
    for lyrics in lyrics_content:
        lyrics_output = lyrics_output + lyrics.get_text() + "\n"
    update.message.reply_text(lyrics_output)
    # print(lyrics_output)

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
    lyrics_output = "{} by {}\n\n".format(song_info['title'], song_info['artist'])
    for lyrics in lyrics_content:
        lyrics_output = lyrics_output + lyrics.get_text() + "\n"
    update.message.reply_text(lyrics_output)

@send_typing_action
def getBibleVerses(update, context):
    message = update.message.text
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
    update.message.reply_text(content_output)


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
    print(href)
    # document = open(href, 'rb')
    bot.sendDocument(chat_id=update.message.chat_id, document=href)


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
    dp.add_handler((CommandHandler('charts', getTopSongs)))
    dp.add_handler((CommandHandler('lyrics', getSongLyrics)))
    dp.add_handler((MessageHandler(Filters.regex('lyric3.+'), scrapeLyrics)))
    dp.add_handler((CommandHandler('get', getBibleVerses)))
    dp.add_handler((CommandHandler('4ws', get4ws)))
    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()

    # query = 'oceans'
    # search_page = requests.get("https://www.musixmatch.com/search/{}/tracks".format(query),
    #                            headers={"User-Agent": "Mozilla/5.0"})
    # soup = BeautifulSoup(search_page.content, 'html.parser')
    # best_result = soup.find(class_="showArtist showCoverart")
    # song_title = best_result.find("a", class_="title").get_text()
    # song_artist = best_result.find("a", class_="artist").get_text()
    # song_href = best_result.find("a", href=True)['href']
    # # print(href)
    # lyrics_page = requests.get("https://www.musixmatch.com{}".format(song_href), headers={"User-Agent": "Mozilla/5.0"})
    # soup = BeautifulSoup(lyrics_page.content, 'html.parser')
    # lyrics_content = soup.find_all(class_="mxm-lyrics__content")
    # lyrics_output = "{} by {}\n\n".format(song_title, song_artist)
    # for lyrics in lyrics_content:
    #     lyrics_output = lyrics_output + lyrics.get_text() + "\n"
    # print(lyrics_output)
