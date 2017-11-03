import logging
from django.core.management import BaseCommand

logger = logging.getLogger('bot.command.test_command')


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-a', '--account', dest='account', type=str, choices=['test', 'radio'], required=True)
        parser.add_argument('-t', '--tags', dest='tags', nargs='*', required=True)

    def handle(self, *args, **options):
        print(args)
        print(options)
