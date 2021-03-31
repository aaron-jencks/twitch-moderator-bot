from typing import List

from twitch_api import TwitchLoyaltyPointRPBot
from loyalty import LoyaltyRedeem
import settings


class RedeemBot(TwitchLoyaltyPointRPBot):
    def setup_commands(self):
        self.commands.add('redeems')
        self.commands.add('redeem')
        self.commands.add('redeem_info')
        self.commands.add('points')
        self.commands.add('give')
        self.commands.add('streak')
        self.commands.add('stats')

    def setup_redeems(self):
        self.redeem_list['commit'] = LoyaltyRedeem('commit', 'Force me to commit my code.', 100)
        self.redeem_list['hydrate'] = LoyaltyRedeem('hydrate', 'Take a sip of water, or whatever it is I\'m drinking atm.', 100)
        self.redeem_list['question'] = LoyaltyRedeem('question', 'Ask me a question, anything, and I\'ll do my best to answer it', 200)
        self.redeem_list['squats'] = LoyaltyRedeem('squats', 'Give me buns of steel! I\'ll do 10 squats', 1000)
        self.redeem_list['comment'] = LoyaltyRedeem('comment', 'I\'ll put your comment in my code whatever it is, must be in Twitch\'s ToS', 1000)
        self.redeem_list['raid'] = LoyaltyRedeem('raid', 'You get to choose the destination for the raid at the end of the stream', 5000)
        self.redeem_list['project'] = LoyaltyRedeem('project', 'I\'ll do a coding project of your choice, must be within Twitch\'s ToS', 999999)

    def redeems(self, user: str, args: List[str]):
        self.chat('The list of valid redeems is {}, use !redeem_info rname to see what they do!'.format(
            str(list(self.redeem_list.keys()))[1:-1])
        )

    def redeem(self, user: str, args: List[str]):
        pnts = self.users[user].points
        if len(args) > 0 and args[0] in self.redeem_list:
            if pnts >= self.redeem_list[args[0]].cost:
                self.chat('@iggy12345101: @{} has redeemed {}'.format(user, args[0]))
                self.users[user].points -= self.redeem_list[args[0]].cost
            else:
                self.chat('@{} Insufficient points.'.format(user))
        else:
            self.chat('@{} That redeem doesn\'t exist, please use !redeems to see a list of valid redeems'.format(user))

    def redeem_info(self, user: str, args: List[str]):
        if len(args) > 0 and args[0] in self.redeem_list:
            r = self.redeem_list[args[0]]
            self.chat('@{} {} x{}: {}'.format(user, r.title, r.cost, r.description))
        else:
            self.chat('@{} That redeem doesn\'t exist, please use !redeems to see a list of valid redeems'.format(user))

    def points(self, user: str, args: List[str]):
        self.chat('@{} you have {} points!'.format(user, self.users[user].points))

    def give(self, user: str, args: List[str]):
        if len(args) > 1:
            try:
                target = args[0]
                if target.startswith('@'):
                    target = target[1:]

                pnts = int(args[1])

                if target in self.users:
                    self.users[target].points += pnts
                    self.chat('Gave {} points from @{} to @{}'.format(pnts, user, target))
                else:
                    self.chat('@{} the user @{} doesn\'t exist, please ensure they have chatted at least once.'.format(
                        user, target))
            except ValueError:
                self.chat('@{} that value {} is invalid, please enter a number (0, infinity]'.format(user, args[1]))
        else:
            self.chat('@{} too few arguments supplied, the syntax is !give @target points .'.format(user))

    def streak(self, user: str, args: List[str]):
        self.chat('@{} You\'ve come to {} streams in a row!'.format(user, self.users[user].visit_streak))

    def stats(self, user: str, args: List[str]):
        u = self.users[user]
        self.chat('@{} Points: {}, Chats: {}, Streak: {}'.format(user, u.points, u.num_chats, u.visit_streak))


if __name__ == '__main__':
    print('Starting automod twitch bot')
    b = RedeemBot(settings.tmi_token, settings.bot_nick, settings.channel)
    b.run()

