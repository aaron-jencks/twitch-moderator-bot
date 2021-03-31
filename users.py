import datetime as dt


class TwitchChatter:
    def __init__(self, username: str):
        self.username = username
        self.points = 0
        self.num_chats = 0
        self.last_chat = None
        self.visit_streak = 0
        self.present = False

    def to_dict(self) -> dict:
        d = {'user': self.username,
             'points': self.points,
             'chats': self.num_chats,
             'last': 'null' if self.last_chat is None else self.last_chat.strftime('%m-%d-%Y-%H-%M-%S'),
             'streak': self.visit_streak}
        return d

    @staticmethod
    def from_dict(d: dict):
        chatter = TwitchChatter(d['user'])
        chatter.points = d['points']
        chatter.num_chats = d['chats']
        chatter.visit_streak = d['streak']
        chatter.last_chat = None if d['last'] == 'null' else dt.datetime.strptime(d['last'], '%m-%d-%Y-%H-%M-%S')
        return chatter
