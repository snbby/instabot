import logging

import os
from django.core.management import BaseCommand
from django.conf import settings

logger = logging.getLogger('bot.command.test_command')


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-a', '--account', dest='account', type=str, choices=['test', 'radio'])
        parser.add_argument('-t', '--tags', dest='tags', nargs='*')

    def handle(self, *args, **options):
        print(args)
        print(options)
        filename = 'pampam.html'
        file_path = os.path.join(settings.HTML_SAMPLES_DIR_PATH, filename)

        print(file_path)
