import socket
import time
from typing import Dict
import re
import os
import pathlib
import json
import datetime as dt
import atexit

from users import TwitchChatter
from loyalty import *

import settings


twitch_host = 'irc.chat.twitch.tv'
twitch_port = 6667
chat_msg_re = re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")
max_message_size = 250


def chat(sock: socket.socket, channel: str, msg: str):
    print("Sending message: {}".format(msg))
    sock.send('PRIVMSG {} :{}\r\n'.format(channel, msg).encode('utf-8'))
    time.sleep(2)


def setup_socket(token: str, username: str, channel: str) -> socket.socket:
    s = socket.socket()
    s.connect((twitch_host, 6667))
    s.send("PASS {}\r\n".format(token).encode("utf-8"))
    s.send("NICK {}\r\n".format(username).encode("utf-8"))
    s.send("JOIN {}\r\n".format(channel).encode("utf-8"))
    chat(s, channel, '/me has landed!')
    return s


def parse_twitch_message(s: str) -> Dict[str, str]:
    result = {}
    username = re.search(r"\w+", s).group(0)  # return the entire match
    message = chat_msg_re.sub("", s)
    result['username'] = username
    result['message'] = message
    return result


class TwitchRPBot:
    def __init__(self, token: str, username: str, channel: str):
        self.s = setup_socket(token, username, channel)
        self.token = token
        self.username = username
        self.channel = channel
        self.commands = set()
        self.setup_commands()
        atexit.register(self.cleanup)

    def cleanup(self):
        self.s.close()

    def setup_commands(self):
        pass

    def get_msg(self) -> str:
        while True:
            response = self.s.recv(1024).decode("utf-8")
            if response == "PING :tmi.twitch.tv\r\n":
                self.s.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
            else:
                return response
            time.sleep(2)

    def chat(self, msg: str):
        if len(msg) > max_message_size:
            msg_count = len(msg) // max_message_size + 1
            iter = 1
            while iter <= msg_count:
                prepart = "Part {}/{} ".format(iter, msg_count)
                print("Sending message: {}{}".format(prepart, msg[:(max_message_size - len(prepart) - 1)]
                if len(msg) > (max_message_size - len(prepart) - 1)
                else msg))

                chat(self.s, self.channel, '{}{}'.format(prepart,
                                                         msg[:(max_message_size - len(prepart) - 1)]
                                                         if len(msg) > (max_message_size - len(prepart) - 1)
                                                         else msg))
                iter += 1
                if len(msg) > (max_message_size - len(prepart) - 1):
                    msg = msg[(max_message_size - len(prepart) - 1):]
            return
        chat(self.s, self.channel, msg)

    def run(self):
        while True:
            msg = self.get_msg().strip()
            print(msg)
            d = parse_twitch_message(msg)
            if d['username'] != self.username:
                words = d['message'].split(' ')
                print('{}: {}'.format(d['username'], d['message']))
                if len(words) > 0 and words[0].startswith(settings.bot_prefix):
                    # print("Found a command {}".format(words[0]))
                    cmd = words[0][1:].lower().strip()
                    if cmd in self.commands:
                        # print("Command {} was in the commands list".format(cmd))
                        exec('self.{}("{}", {})'.format(cmd,
                                                        d['username'],
                                                        words[1:] if len(words) > 1 else []))
                    else:
                        print("{} is not in list of {}".format(cmd, self.commands))


class TwitchLoyaltyPointRPBot(TwitchRPBot):
    def __init__(self, token: str, username: str, channel: str, user_db: str = ''):
        super().__init__(token, username, channel)
        self.users = {}
        self.db = user_db
        self.redeem_list = {}
        self.setup_redeems()
        if len(user_db) == 0:
            self.initialize_db_path()
        elif os.path.isfile(self.db):
            print('Restore point found, restoring...')
            self.restore_from_file()
        else:
            print('No restore point found, starting new database...')
            pathlib.Path(self.db).touch()

    def cleanup(self):
        super().cleanup()
        print('Saving database')
        self.update_streak_info()
        self.save_to_file()

    def setup_redeems(self):
        pass

    def initialize_db_path(self):
        home_dir = os.path.expanduser('~')
        db_filename = os.path.join(home_dir, 'twitch_user_db.json')
        self.db = db_filename
        if os.path.isfile(db_filename):
            print('Restore point found, restoring...')
            self.restore_from_file()
        else:
            print('No restore point found, starting new database...')
            pathlib.Path(db_filename).touch()

    def restore_from_file(self):
        with open(self.db, mode='r') as fp:
            data = fp.read()
            for u in json.loads(data):
                user = TwitchChatter.from_dict(u)
                self.users[user.username] = user

    def save_to_file(self):
        users = [u.to_dict() for _, u in self.users.items()]
        with open(self.db, mode='w+') as fp:
            fp.write(json.dumps(users))

    def update_user_score(self, user: str, msg: str):
        if user not in self.users:
            self.users[user] = TwitchChatter(user)
            print('Giving {} a sign on bonus of {} points'.format(user, sign_on_bonus))
            self.users[user].points += sign_on_bonus

        print('Giving {} {} points'.format(user, assign_message_score(msg)))
        self.users[user].points += assign_message_score(msg)

        if not self.users[user].present:
            print('Giving {} a consecutive visit bonus for a streak of {}, for {} points'.format(
                user, self.users[user].visit_streak, determine_visit_bonus(self.users[user].visit_streak)))
            self.users[user].present = True
            self.users[user].points += determine_visit_bonus(self.users[user].visit_streak)
            self.users[user].visit_streak += 1

        self.users[user].last_chat = dt.datetime.now()

    def update_streak_info(self):
        for u in self.users.keys():
            if not self.users[u].present:
                self.users[u].visit_streak = 0

    def run(self):
        while True:
            msg = self.get_msg().strip()
            print(msg)
            d = parse_twitch_message(msg)
            # if d['username'] != self.username:

            self.update_user_score(d['username'], d['message'])

            words = d['message'].split(' ')
            print('{}: {}'.format(d['username'], d['message']))
            if len(words) > 0 and words[0].startswith(settings.bot_prefix):
                # print("Found a command {}".format(words[0]))
                cmd = words[0][1:].lower().strip()
                if cmd in self.commands:
                    # print("Command {} was in the commands list".format(cmd))
                    exec('self.{}("{}", {})'.format(cmd,
                                                    d['username'],
                                                    words[1:] if len(words) > 1 else []))
                else:
                    print("{} is not in list of {}".format(cmd, self.commands))


if __name__ == '__main__':
    cb = TwitchRPBot(settings.tmi_token, settings.bot_nick, settings.channel)
    print(cb.get_msg())
    while True:
        cb.chat('Hello')
