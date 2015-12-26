from django.core.management.base import BaseCommand, CommandError
from celerycrawler.tasks import retrieve_page

class Command(BaseCommand):
    
    def handle(self, url, **options):
        print("handling: {}".format(url))
        retrieve_page.delay(url, rank=1)
