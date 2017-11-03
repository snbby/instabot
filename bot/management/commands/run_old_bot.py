from django.core.management import BaseCommand
from django.conf import settings

from old_bot.instabot import InstaBot


class Command(BaseCommand):
    def handle(self, *args, **options):
        bot = InstaBot(settings.INSTA_USERNAME, settings.INSTA_PASSWORD,
                       tag_list=['future', 'kino', 'cinema'])
        bot.auto_mod()
