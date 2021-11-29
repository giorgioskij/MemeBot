from os import pread
from credentials import TOKEN, USERS_PATH
import schedule
import telebot
from telebot import types
import feedparser
from threading import Thread
from time import sleep
import pickle
import requests

MEME_TIME = "10:30"

def main(): 
    # load users from file or generate new users file
    try:
        with open(USERS_PATH, 'r+b') as f:
            users = pickle.load(f)
    except:
        with open(USERS_PATH, 'w+b') as f1:
            users = {}
            pickle.dump(users, f1)

    # create bot
    memebot = telebot.TeleBot(TOKEN)

    # handle /start command
    @memebot.message_handler(commands=['start', 'help'])
    def start(message):
        chat_id = message.chat.id
        add_user(chat_id)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, row_width=2)
        markup.row(types.KeyboardButton('/help'))
        markup.row(types.KeyboardButton('/subscribe'), types.KeyboardButton('/unsubscribe'))
        markup.row(types.KeyboardButton('/meme'))
        memebot.send_message(
            chat_id,
            "Welcome to Daily Memini's!\n\nUse \subscribe to subscribe to the daily meme service,\nor use \meme to receive a single meme",
            reply_markup = markup)

    # handle /meme command
    @memebot.message_handler(commands=['meme'])
    def meme(message):
        send_meme(memebot, message.chat.id)

    # handle /subscribe command
    @memebot.message_handler(commands=['subscribe'])
    def subscribe(message):
        chat_id = message.chat.id
        memebot.reply_to(message, "Glad to have you on our daily subscription - it's free of charge!\nYou will receive a meme every morning to cheer you up!")
        add_subscription(chat_id)
    
    # handle /unsubscribe command
    @memebot.message_handler(commands=['subscribe'])
    def subscribe(message):
        chat_id = message.chat.id
        memebot.reply_to(message, "Sorry to see you go! :(")
        remove_subscription(chat_id)


    schedule.every().day.at(MEME_TIME).do(send_broadcast, memebot=memebot)
    schedule.every().day.at('00:01').do(clear_all_counters)

    Thread(target=schedule_checker).start()
    memebot.polling()


def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(1)

# sends a meme to every subscribed user
def send_broadcast(memebot: telebot.TeleBot):
    print('sending everyone a meme')
    users = read_users()
    for user in users:
        if users[user]['subscribed']: 
            memebot.send_message(user, 'Good morning! Here\'s your daily meme!')
            send_meme(memebot, user)

# sets to 0 the meme counters for every user (to do at least everyday)
def clear_all_counters():
    users = read_users()
    for user in users:
        users[user]['counter'] = 0
    save_users(users)

# reads from file the users database
def read_users():
    with open(USERS_PATH, 'rb') as f:
        users = pickle.load(f)
    return users

# saves the user database to file
def save_users(users):
    with open(USERS_PATH, 'wb') as f:
        pickle.dump(users, f)

# makes sure that a user is added to the database.
def add_user(chat_id: int):
    users = read_users()
    if chat_id in users: return
    users[chat_id] = {'subscribed': False, 'counter': 0}
    save_users(users)

# enables the subscription for a user
def add_subscription(chat_id: int):
    add_user(chat_id)
    users = read_users()
    users[chat_id]['subscribed'] = True
    save_users(users)

# cancels the subscription for a user
def remove_subscription(chat_id: int):
    add_user(chat_id)
    users = read_users()
    users[chat_id]['subscribed'] = False
    save_users(users)

# increments by 1 the meme counter of a user: it prevents the bot
# from sending the same meme to a user multiple times
def increment_user_counter(chat_id: int):
    add_user(chat_id)
    users = read_users()
    users[chat_id]['counter'] += 1
    save_users(users)

# finds the index-th hot meme of the day on reddit
def find_meme(index: int = 0) -> tuple:
    url = "https://www.reddit.com/r/memes/top.rss?t=day"
    f = feedparser.parse(url)
    key = index 
    success = False
    while not success:
        title = f.entries[key].title
        content: str = f.entries[key].content[0].value
        index_start = content.find('https://i.redd')
        key += 1
        success = index_start != -1

        if key >= len(f.entries):
            break

    if not success:
        raise IndexError('Out of fresh memes to show')

    index_end = index_start + content[index_start:].find('"')
    link = content[index_start : index_end]
    return title, link 

# gets the meme counter for a user
def get_user_counter(chat_id: int) -> int:
    users = read_users()
    return users[chat_id]['counter']

# finds a meme and sends it to a user
def send_meme(memebot, chat_id):
    add_user(chat_id)
    success = False

    while not success:
        counter = get_user_counter(chat_id)
        try:
            title, link = response = find_meme(index = counter)
        except:
            memebot.send_message(chat_id, 'Reddit is out of fresh memes for today!\nGo do something productive for a while...')
            break
        extension = link[-link[::-1].find('.'):]
        if extension == 'gif':
            resp = requests.get(f'https://api.telegram.org/bot{TOKEN}/sendAnimation?chat_id={chat_id}&animation={link}')
        else:
            resp = requests.get(f'https://api.telegram.org/bot{TOKEN}/sendPhoto?chat_id={chat_id}&photo={link}')
        if resp.ok:
            memebot.send_message(chat_id, title)
            success = True
        increment_user_counter(chat_id)


if __name__ == "__main__":
    main()









