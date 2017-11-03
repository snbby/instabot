from django.core.management import BaseCommand
from django.conf import settings

from bot import Bot


class Command(BaseCommand):
    def handle(self, *args, **options):
        bot = Bot(settings.INSTA_USERNAME_TEST, settings.INSTA_PASSWORD_TEST)
        bot.run()
