import re
import couchdb
import requests
import lxml

from pprint import pprint
from lxml.html import document_fromstring
from lxml.html.clean import Cleaner
from celerycrawler import settings
from celerycrawler.indexer import get_writer, get_last_change, set_last_change
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def handle(self, **options):
        since = get_last_change()
        writer = get_writer()

        last_change = since
        while True:
            doc = {}
            
            changes = settings.db.changes(since=since)
            since = changes["last_seq"]

            if since != last_change:
                print("Detected new tasks ".format(len(changes)))
                print("=== changes ===")
                pprint(changes)
            for changeset in changes["results"]:
                try:
                    doc = settings.db[changeset["id"]]
                except couchdb.http.ResourceNotFound:
                    print("resource not found")
                    continue

            if not ("type" in doc and "page" in doc["type"]):
                if since != last_change:
                    print("not processing doc: {}".format(str(doc)))
                    last_change = since
                continue
                    
            print("indexing", doc["url"])

            #####
            # raw, html, text
            #####################
            raw = doc['content']
            print("type(RAW) = %s" % type(raw))
            tree = document_fromstring(str(raw))
            title = ' '.join([title for title in tree.xpath('//title/text()')])
            
            # enable filters to remove Javascript and CSS from HTML document
            cleaner = Cleaner()
            cleaner.javascript = True
            cleaner.style = True
            cleaner.html = True
            cleaner.page_structure = False
            cleaner.meta = False
            cleaner.safe_attrs_only = False
            cleaner.links = False

            html = cleaner.clean_html(tree)
            text_content = html.text_content()

            lxml.html.tostring(html)
            description = ' '.join(tree.xpath("//meta[@name='description']/@content"))

            writer.update_document(
                title=title,
                url=doc['url'],
                desc=description,
                rank=doc['rank'],
                content='\n'.join([title, doc['url'], text_content]),
                raw=raw,
            )

            writer.commit()
            writer = get_writer()
            set_last_change(since)
            last_change = since
