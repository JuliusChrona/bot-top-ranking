import collections
import math
import os
import telebot
import re
import json
from datetime import datetime
from work_music import get_links, download_music_link, get_music_csv, create_csv
from telebot.types import File
bot = telebot.TeleBot("1389559561:AAGbQ0mIBnptbQ4-XCvqKLlNMN-szSIhyxI")

Song = collections.namedtuple('Song', ['link', 'title', 'mark', 'pos'])

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
        self.count_rows = self.config['countRows']
        self.current_page = self.config['currentPage']
        self.songs = self.config['songs']
        self.voted_users = self.config['votedUsers']
        self.current_idx = self.config['currentIdx']
        self.max_page = math.ceil(self.count_music / self.count_rows)
        self.poll_started = self.config['pollStarted']
        self.message_id = self.config['messageId']
        self.poll_id = self.config['pollId']
        self.chat_id = self.config['chatId']

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
                "votedUsers": self.voted_users,
                "usersForPromoting": self.users_for_promoting,
                "countRows": self.count_rows,
                "currentPage" : self.current_page,
                "songs" : self.songs,
                "currentIdx": self.current_idx,
                "pollStarted": self.poll_started
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


@bot.message_handler(commands=['vote'])
def vote_for_song(message):
    if setup.poll_started:
        try:
            idx = int(re.search(r'^/vote ([\d]*)$', message.text).group(1)) - 1
        except AttributeError:
            bot.send_message(setup.chat_id, '/help@DrakeChronoSilviumBot')
        else:
            if idx > setup.count_music:
                bot.send_message(setup.chat_id, f'Type {setup.count_music} > number > 0')
            elif (message.from_user.id, str(idx)) not in setup.voted_users:
                song_item = setup.songs[idx]
                setup.songs[idx]["mark"] = song_item["mark"] + 1
                setup.voted_users.append((message.from_user.id, str(idx)))
            else:
                song_item = setup.songs[idx]
                setup.songs[idx]["mark"] = song_item.mark + 1
                setup.voted_users.pop(setup.voted_users.index((message.from_user.id, str(idx))))
    else:
        bot.send_message(message.chat.id, "poll hasn't started yet. Type /disco to start")


@bot.message_handler(commands=['help'])
def get_help(message):
    help_message = (
            "/disco to start poll (Admin only)\n"
            "/finish to end poll (Admin only)\n"
            "/top [num] output top songs(e.g. /top or top 5) \n"
            "/vote [num] vote for song from poll (e.g. /vote or /vote 5) \n"
            "/setDJ [mentioned user] (e.g. /setDJ @Admin) (Admin only)\n"
    )
    bot.send_message(message.chat.id, help_message)


@bot.message_handler(commands=['disco'])
def create_poll(message):
    if check_admin_permissions(message):
        if setup.poll_started:
            bot.send_message(message.chat.id, "Previous poll hasn't finished yet. Type /finish or use pined Message")
        else:
            setup.poll_started = True
            music_poll = ''
            for idx, song in enumerate(setup.songs):
                music_poll += f'{setup.current_idx + idx}. {song["title"]}\n'
            poll = bot.send_message(message.chat.id, music_poll)
            setup.message_id = poll.message_id
            setup.chat_id = poll.chat.id
            bot.pin_chat_message(setup.chat_id, setup.message_id, disable_notification=True)
    else:
        bot.send_message(message.chat.id, r"You don't have permission")


@bot.message_handler(commands=['finish'])  # Unnecessary command
def finish_poll(message):
    if setup.poll_started:
        bot.unpin_chat_message(setup.chat_id)
        setup.make_default_setup()
    else:
        bot.send_message(setup.chat_id, "poll hasn't started yet. Type /poll to start")


@bot.message_handler(commands=['top'])
def get_songs_top_list(message):
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


@bot.message_handler(commands=['poptop'])
def pop_element_from_top(message):
    if check_admin_permissions(message):
        if setup.poll_started:
            try:
                if message.text == '/poptop@DrakeChronoSilviumBot':  # оставить /poptop
                    idx = 0
                else:
                    idx = int(re.search(r'^/poptop ([\d]*)$', message.text).group(1)) - 1
            except AttributeError:
                bot.send_message(setup.chat_id, 'Incorrect input')
                return None
            else:
                if idx < 0 or idx > setup.count_music:
                    bot.send_message(setup.chat_id, f'Type {setup.count_music} > number > 0')
                    return None
            is_changed = False
            top_list = setup.songs.copy()
            top_list.sort(key=lambda song: song["mark"], reverse=True)
            download_music_link(top_list[idx].link)
            audio = open('song.mp3', 'rb')
            bot.send_audio(message.chat.id, audio)
            os.remove('song.mp3')
            vote_remove_index_list = []
            for index, vote in enumerate(setup.voted_users):
                if vote[1] == top_list[idx].pos:  # vote[1] = song position
                    vote_remove_index_list.append(index)
                    song_item = setup.songs[int(vote[1])]
                    setup.songs[int(vote[1])] = song_item._replace(mark=0)
                    is_changed = True
            if is_changed:
                for index in vote_remove_index_list:
                    setup.voted_users.pop(index)
                bot.edit_message_reply_markup(setup.chat_id, setup.poll_id, reply_markup=gen_markup())
        else:
            bot.send_message(message.chat.id, "poll hasn't started yet. Type /poll to start")
    else:
        bot.send_message(message.chat.id, r"You don't have permission")


@bot.message_handler(commands=['setDJ'])
def set_dj_by_user_id(message):
    if check_admin_permissions(message):
        try:
            mentioned_user = re.search(r'^/setDJ @([\w]*)', message.text).group(1)
        except AttributeError:
            bot.send_message(message.chat.id, '/help@DrakeChronoSilviumBot') # Оставить /help
        else:
            setup.users_for_promoting.append(mentioned_user)
            bot.send_message(message.chat.id, f'@{mentioned_user} type /becomeDJ. It\'s privileges only for you ^_^')


@bot.message_handler(commands=['becomeDJ'])
def become_dj(message):
    if message.from_user.username in setup.users_for_promoting:
        bot.promote_chat_member(message.chat.id, message.from_user.id, can_delete_messages=True)
        bot.set_chat_administrator_custom_title(message.chat.id, message.from_user.id, 'DJ')
        bot.send_message(
            message.chat.id,
            f'@{message.from_user.username} You have been promoted to DJ. Congratulate 🏆🏆🏆'
        )
    elif check_admin_permissions(message):
        bot.send_message(message.chat.id, 'You are admin. Why do you try to do it??? (╮°-°)╮┳━━┳ ( ╯°□°)╯ ┻━━┻')


if __name__ == "__main__":
    bot.polling(none_stop=True)
