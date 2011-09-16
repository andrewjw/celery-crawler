from datetime import datetime
import re
import time
from urlparse import urlparse
from utils import unescape

from celery.decorators import task

from crawler.models import Page, RobotsTxt

import settings

@task
def retrieve_page(url, rank=None):
    print "retrieve_page %s" % (url, )
    if url.startswith("http://showmedo.com") or url.startswith("http://www.rentacarnow.com"):
        return
    page = Page.get_by_url(url)
    if page is None:
        return

    if rank is not None:
        page.rank = rank
        page.store(settings.db)

    assert page.id is not None
    find_links.delay(page.id)

link_single_re = re.compile(r"<a[^>]+href='([^']+)'")
link_double_re = re.compile(r'<a[^>]+href="([^"]+)"')

@task
def find_links(doc_id):
    if doc_id is None:
        return

    doc = Page.load(settings.db, doc_id)

    if doc.content is None:
        print "Got None for the content of %s -> %s." % (doc_id, doc.url)
        return

    raw_links = []
    for match in link_single_re.finditer(doc.content):
        raw_links.append(match.group(1))

    for match in link_double_re.finditer(doc.content):
        raw_links.append(match.group(1))

    doc.links = []
    for link in raw_links:
        if link.startswith("#"):
            continue
        elif link.startswith("http://") or link.startswith("https://"):
            pass
        elif link.startswith("/"):
            parse = urlparse(doc["url"])
            link = parse.scheme + "://" + parse.netloc + link
        else:
            link = "/".join(doc["url"].split("/")[:-1]) + "/" + link

        doc.links.append(unescape(link.split("#")[0]))

    print "find_links %s -> %i" % (doc.url, len(doc.links))
    doc.store(settings.db)

    calculate_rank.delay(doc.id)

    for link in doc.links:
        p = Page.get_id_by_url(link, update=False)
        if p is not None:
            calculate_rank.delay(p)
        else:
            retrieve_page.delay(link)

@task
def calculate_rank(doc_id):
    page = Page.load(settings.db, doc_id)

    links = Page.get_links_to_url(page.url)

    rank = 0
    for link in links:
        rank += link[0] / link[1]

    old_rank = page.rank
    page.rank = rank * 0.85

    if page.rank == 0:
        page.rank = 1.0/settings.db.view("page/by_url", limit=0).total_rows

    if abs(old_rank - page.rank) > 0.0001:
        print "%s: %s -> %s" % (page.url, old_rank, page.rank)
        page.store(settings.db)

        for link in page.links:
            p = Page.get_id_by_url(link, update=False)
            if p is not None:
                calculate_rank.delay(p)
