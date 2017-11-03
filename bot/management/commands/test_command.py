
import requests
import logging
from django.core.management import BaseCommand

logger = logging.getLogger('bot.command.test_command')

class Command(BaseCommand):
    def handle(self, *args, **options):
        requests.get('http://yandex.ru')
        logger.debug('hohoh')
        print(args)
        print(options)
