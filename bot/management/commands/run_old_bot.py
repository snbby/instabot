from django.core.management import BaseCommand
from django.conf import settings

from old_bot import InstaBot


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-a', '--account', dest='account', type=str, choices=['test', 'radio'], required=True)
        parser.add_argument('-t', '--tags', dest='tags', nargs='*', required=True)
        parser.add_argument('-f', '--follow_per_day', dest='follow_per_day', type=int)
        parser.add_argument('-l', '--like_per_day', dest='like_per_day', type=int)
        parser.add_argument('--unfollow_per_day', dest='unfollow_per_day', type=int)
        parser.add_argument('--media_max_like', dest='media_max_like', type=int)
        parser.add_argument('--log_mode', dest='log_mod', choices=[0, 1, 2], type=int)

    def handle(self, *args, **options):
        username = None
        password = None

        if options['account'] == 'test':
            username = settings.INSTA_USERNAME_TEST
            password = settings.INSTA_PASSWORD_TEST
        elif options['account'] == 'radio':
            username = settings.INSTA_USERNAME
            password = settings.INSTA_PASSWORD

        bot = InstaBot(
            username,
            password,
            tag_list=options['tags'],
            follow_per_day=options.get('follow_per_day', 0),
            like_per_day=options.get('like_per_day', 1000),
            unfollow_per_day=options.get('unfollow_per_day', 0),
            media_max_like=options.get('media_max_like', 0),
            log_mod=options.get('log_mod', 0)
        )
        bot.auto_mod()
