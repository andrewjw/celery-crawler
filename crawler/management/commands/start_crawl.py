from django.core.management.base import BaseCommand, CommandError

from crawler.tasks import retrieve_page

class Command(BaseCommand):
    def handle(self, url, **options):
         retrieve_page.delay(url, rank=1)
