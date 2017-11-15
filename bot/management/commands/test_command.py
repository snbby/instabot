import logging

import os
from django.core.management import BaseCommand
from django.conf import settings

from bot import Bot

logger = logging.getLogger('bot.command.test_command')


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-a', '--account', dest='account', type=str, choices=['test', 'radio'])
        parser.add_argument('-t', '--tags', dest='tags', nargs='*')

    def handle(self, *args, **options):
        bot = Bot(settings.INSTA_USERNAME_TEST, settings.INSTA_PASSWORD_TEST)
        bot._logout()
