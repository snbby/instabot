from django.core.management import BaseCommand

from bot import Bot


class Command(BaseCommand):
    def handle(self, *args, **options):
        bot = Bot('i_see_smth')
        bot.run()
