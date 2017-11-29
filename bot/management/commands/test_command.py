import logging

from django.core.management import BaseCommand

from bot import Bot

logger = logging.getLogger('bot.command.test_command')


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-a', '--account', dest='account', type=str, choices=['test', 'radio'])
        parser.add_argument('-t', '--tags', dest='tags', nargs='*')

    def handle(self, *args, **options):
        bot = Bot('i_see_smth')
        bot._login()
        bot._unfollow_loop(max_follow_num=0)
        bot._logout()
