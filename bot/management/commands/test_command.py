import logging
from time import sleep

from django.core.management import BaseCommand

logger = logging.getLogger('bot.command.test_command')


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-a', '--account', dest='account', type=str, choices=['test', 'radio'])
        parser.add_argument('-t', '--tags', dest='tags', nargs='*')

    def handle(self, *args, **options):
        try:
            while True:
                print('ho')
                sleep(5)
        finally:
            print('finally')

