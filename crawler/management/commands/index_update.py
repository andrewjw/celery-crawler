import re

from BeautifulSoup import BeautifulSoup
import couchdb
from django.core.management.base import BaseCommand, CommandError

from crawler.indexer import get_writer, get_last_change, set_last_change

import settings

desc_re = re.compile("^description$", re.I)

class Command(BaseCommand):
    def handle(self, **options):
        since = get_last_change()
        writer = get_writer()
        try:
            while True:
                changes = settings.db.changes(since=since)
                since = changes["last_seq"]
                for changeset in changes["results"]:
                    try:
                        doc = settings.db[changeset["id"]]
                    except couchdb.http.ResourceNotFound:
                        continue
                    if "type" in doc and doc["type"] == "page":
                        print "indexing", doc["url"]
                        soup = BeautifulSoup(doc["content"])
                        if soup.body is None:
                            continue

                        desc = soup.findAll('meta', attrs={ "name": desc_re })

                        writer.update_document(
                                title=unicode(soup.title(text=True)[0]) if soup.title is not None and len(soup.title(text=True)) > 0 else doc["url"],
                                url=unicode(doc["url"]),
                                desc=unicode(desc[0]["content"]) if len(desc) > 0 and desc[0]["content"] is not None else u"",
                                rank=doc["rank"],
                                content=unicode(soup.title(text=True)[0] + "\n" + doc["url"] + "\n" + "".join(soup.body(text=True)))
                            )

                    writer.commit()
                    writer = get_writer()

                set_last_change(since)
        finally:
            set_last_change(since)
