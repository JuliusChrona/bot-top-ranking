import math
import os
import telebot
import re
import json

from datetime import datetime
from work_music import get_links, download_music_link, get_music_csv, create_csv
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from telebot.apihelper import ApiTelegramException

bot = telebot.TeleBot("1389559561:AAGbQ0mIBnptbQ4-XCvqKLlNMN-szSIhyxI")


class Setup:
    def __init__(self):
        self.FILENAME = "music.csv"
        self.config = {}
        self.loads_config()
        create_csv(self.FILENAME,self.count_music)
        self.get_songs()

    def loads_config(self):
        if os.path.exists('saved_config.json'):
            with open("saved_config.json") as r_file:
                print("Load from exists")
                self.config = json.load(r_file)
        else:
            with open("config.json") as r_file:
                print("Load from default settings")
                self.config = json.load(r_file)
        self.users_for_promoting = self.config['usersForPromoting']
        self.count_music = self.config['countMusic']
        self.songs = self.config['songs']
        self.poll_started = self.config['pollStarted']
        self.message_id = self.config['messageId']
        self.poll_id = self.config['pollId']
        self.chat_id = self.config['chatId']
        self.upload_flag = self.config['uploadFlag']

    def get_songs(self,):
        self.songs = get_music_csv(self.FILENAME)

    def save_config(self):
        with open(f'saved_config.json',"w") as w_file:
            print("hello")
            data = {
                "chatId" : self.chat_id,
                "messageId": self.message_id,
                "pollId" : self.poll_id,
                "countMusic": self.count_music,
                "usersForPromoting": self.users_for_promoting,
                "uploadFlag": self.upload_flag,
                "songs" : self.songs,
                "pollStarted": self.poll_started,
            }
            json.dump(data, w_file)


setup = Setup()


def check_admin_permissions(message):
    admins_id = [admin.user.id for admin in bot.get_chat_administrators(message.chat.id)]
    return message.from_user.id in admins_id


def update_poll_message():
    music_poll = ''
    for idx, song in enumerate(setup.songs):
        music_poll += f'{idx}. {song["title"]}\n'
    bot.edit_message_text(music_poll, setup.chat_id, setup.poll_id)


def upload_song(link):
    if setup.upload_flag:
        download_music_link(link)
        audio = open('song.mp3', 'rb')
        bot.send_audio(setup.chat_id, audio)
        os.remove('song.mp3')


def gen_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Help", callback_data="help"),)
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "help":
        get_help(call.message)

@bot.message_handler(commands=['vote'])
def vote_for_song(message):
    try:
        if setup.poll_started:
            try:
                idx = int(re.search(r'^/vote ([\d]*)$', message.text).group(1)) - 1
            except AttributeError:
                bot.send_message(setup.chat_id, '/help')
            else:
                if idx > setup.count_music:
                    bot.send_message(setup.chat_id, f'Type {setup.count_music} > number > 0')
                elif message.from_user.id not in setup.songs[idx]["votedUsers"]:
                    song_item = setup.songs[idx]
                    song_item["mark"] += 1
                    song_item["votedUsers"].append(message.from_user.id)
                    setup.songs[idx] = song_item
                else:
                    song_item = setup.songs[idx]
                    song_item["mark"] -= 1
                    song_item["votedUsers"].pop(song_item["votedUsers"].index(message.from_user.id))
                    setup.songs[idx] = song_item
        else:
            bot.send_message(message.chat.id, "poll hasn't started yet. Type /disco to start")
    except ApiTelegramException:
        setup.save_config()
        print("Error in ApiTelegramException")


@bot.message_handler(commands=['help'])
def get_help(message):

    try:
        help_message = (
                "/disco to start poll (Admin only)\n"
                "/finish to end poll (Admin only)\n"
                "/top [num] output top songs(e.g. /top or top 5) \n"
                "/vote [num] vote for song from poll (e.g. /vote or /vote 5) \n"
                "/setDJ [mentioned user] set mentioned people a DJ (e.g. /setDJ @Admin) (Admin only)\n"
                "/settings mp3 on|off\n"
                "/poll_status to print status of poll in this chat"
        )
        bot.send_message(message.chat.id, help_message)
    except ApiTelegramException:
        setup.save_config()
        print("Error in ApiTelegramException")


@bot.message_handler(commands=['settings'])
def change_upload_flag(message):
    try:
        if message.text == '/settings mp3':
            setup.upload_flag = False if setup.upload_flag else True
        else:
            switch = message.text.replace('/settings mp3', '').split()[0]
            if switch == 'on':
                setup.upload_flag = True
            elif switch == 'off':
                setup.upload_flag = False
        bot_message = f"uploading songs is {'Enabled' if setup.upload_flag else 'Disabled'}"
        bot.send_message(setup.chat_id, bot_message)
    except ApiTelegramException:
        setup.save_config()
        print("Error in ApiTelegramException")

@bot.message_handler(commands=['poll_status'])
def get_poll_status(message):
    if check_admin_permissions(message):
        status = f'''Poll status\n———————————\nPoll_started: {setup.poll_started}\nUpload mp3:{"on" if setup.upload_flag else "off"} '''
        bot.send_message(setup.chat_id,status)
    else:
        bot.send_message(message.chat.id, r"You don't have permission")


@bot.message_handler(commands=['disco'])
def create_poll(message):
    try:
        if check_admin_permissions(message):
            if setup.poll_started:
                bot.send_message(message.chat.id, "Previous poll hasn't finished yet. Type /finish or use pined Message")
                # bot.send_message(1, "Previous poll hasn't finished yet. Type /finish or use pined Message")
            else:
                setup.poll_started = True
                music_poll = ''
                for idx, song in enumerate(setup.songs):
                    music_poll += f'{idx + 1}. {song["title"]} | {song["author"]}\n'
                poll = bot.send_message(message.chat.id, music_poll, reply_markup=gen_markup())
                setup.message_id = poll.message_id
                setup.chat_id = poll.chat.id
                bot.pin_chat_message(setup.chat_id, setup.message_id, disable_notification=True)
        else:
            bot.send_message(message.chat.id, r"You don't have permission")
    except ApiTelegramException:
        setup.save_config()
        print("Error in ApiTelegramException")


@bot.message_handler(commands=['finish'])  # Unnecessary command
def finish_poll(message):
    try:
        if setup.poll_started:
            bot.unpin_chat_message(setup.chat_id)
        else:
            bot.send_message(setup.chat_id, "poll hasn't started yet. Type /poll to start")
    except ApiTelegramException:
        setup.save_config()
        print("Error in ApiTelegramException")


@bot.message_handler(commands=['top'])
def get_songs_top_list(message):
    try:
        top_list = setup.songs.copy()
        top_list.sort(key=lambda song: song["mark"], reverse=True)
        music_poll = ''
        try:
            top_number = int(re.search(r'^/top ([\d]*)$', message.text).group(1))
        except AttributeError:
            bot.send_message(message.chat.id, 'Incorrect input')
        else:
            if top_number > 10 or not top_number:
                bot.send_message(message.chat.id, 'Number should be greater than 0 and less or equal to 10')
            else:
                for idx, song in enumerate(top_list[:top_number]):  # 5 - regexp
                    music_poll += f'{idx + 1}. {song["title"]} Votes - {song["mark"]}\n'
                bot.send_message(message.chat.id, music_poll)
    except ApiTelegramException:
        setup.save_config()
        print("Error in ApiTelegramException")


@bot.message_handler(commands=['poptop'])
def pop_element_from_top(message):
    try:
        if check_admin_permissions(message):
            if setup.poll_started:
                try:
                    if message.text == '/poptop':
                        idx = 0
                    else:
                        idx = int(re.search(r'^/poptop ([\d]*)$', message.text).group(1)) - 1
                except AttributeError:
                    bot.send_message(setup.chat_id, 'Incorrect input')
                    return None
                else:
                    if idx > setup.count_music:
                        bot.send_message(setup.chat_id, f'Type {setup.count_music} > number')
                        return None
                top_list = setup.songs.copy()
                top_list.sort(key=lambda song: song["mark"], reverse=True)
                upload_song(top_list[idx]["link"])
                song_index = top_list[idx]["pos"] - 1  # positions of songs starts by 1
                song_item = setup.songs[song_index]
                song_item["votedUsers"] = []
                song_item["mark"] = 0
                print(song_item)
                setup.songs[song_index] = song_item
            else:
                bot.send_message(message.chat.id, "poll hasn't started yet. Type /poll to start")
        else:
            bot.send_message(message.chat.id, r"You don't have permission")
    except ApiTelegramException:
        setup.save_config()
        print("Error in ApiTelegramException")


@bot.message_handler(commands=['setDJ'])
def set_dj_by_user_id(message):
    try:
        if check_admin_permissions(message):
            try:
                mentioned_user = re.search(r'^/setDJ @([\w]*)', message.text).group(1)
            except AttributeError:
                bot.send_message(message.chat.id, '/help')
            else:
                setup.users_for_promoting.append(mentioned_user)
                bot.send_message(message.chat.id, f'@{mentioned_user} type /becomeDJ. It\'s privileges only for you ^_^')
    except ApiTelegramException:
        setup.save_config()
        print("Error in ApiTelegramException")


@bot.message_handler(commands=['becomeDJ'])
def become_dj(message):
    try:
        if message.from_user.username in setup.users_for_promoting:
            bot.promote_chat_member(message.chat.id, message.from_user.id, can_delete_messages=True)
            bot.set_chat_administrator_custom_title(message.chat.id, message.from_user.id, 'DJ')
            bot.send_message(
                message.chat.id,
                f'@{message.from_user.username} You have been promoted to DJ. Congratulate 🏆🏆🏆'
            )
        elif check_admin_permissions(message):
            bot.send_message(message.chat.id, 'You are admin. Why do you try to do it??? (╮°-°)╮┳━━┳ ( ╯°□°)╯ ┻━━┻')
    except ApiTelegramException:
        setup.save_config()
        print("Error in ApiTelegramException")


if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except Exception:
        print('I\'m here')
