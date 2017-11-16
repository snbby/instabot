from django.core.management import BaseCommand

from bot import Bot


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-a', '--account', dest='account', type=str, required=True)

    def handle(self, *args, **options):
        bot = Bot(options['account'])
        bot.run()
