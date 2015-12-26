from lxml.html import document_fromstring
from urllib.parse import urlparse, urljoin
from celerycrawler import settings
from celery.decorators import task
from celerycrawler.models import Page, RobotsTxt
from celerycrawler.utils import unescape


@task
def retrieve_page(url, rank=None):
    print("retrieve_page {}".format(url))
    page = Page.get_by_url(url, update=True)
    if page is None:
        print("Page is None")
        return

    if rank is not None:
        page.rank = rank
        page.store(settings.db)

    if page.id is None:
        page.update()

    find_links.delay(page.id)

@task
def find_links(doc_id):
    print("in find_links")
    if doc_id is None:
        print("doc_id = None")
        return False

    doc = Page.load(settings.db, doc_id)

    if not hasattr(doc, 'content'):
        print("Got None for the content of %s -> %s." % (doc_id, doc.url))
        return False
    elif not doc['content']:
        print("tasks.py:elif not doc.content")
        return False

    raw_links = []
    tree = document_fromstring(doc.content)
    for a in tree.xpath('//a'):
        link = urljoin(doc['url'], a.get('href'))
        doc.links.append(link)
    
    doc.store(settings.db)

    calculate_rank.delay(doc.id)

    for link in doc.links:
        p = Page.get_id_by_url(link, update=False)
        if p is not None:
            calculate_rank.delay(p)
        else:
            retrieve_page.delay(link)

    print("find_links {} -> {}".format(doc.url, len(doc.links)))

@task
def calculate_rank(doc_id):
    print("in calculate_rank")
    page = Page.load(settings.db, doc_id)

    links = Page.get_links_to_url(page.url)

    rank = 0
    for link in links:
        rank += link[0] / link[1]

    old_rank = page.rank
    page.rank = rank * 0.85

    if page.rank == 0:
        n_links = settings.db.view("page/by_url", limit=0).total_rows
        page.rank = 1.0 / n_links

    if abs(old_rank - page.rank) > 0.0001:
        print("%s: %s -> %s" % (page.url, old_rank, page.rank))
        page.store(settings.db)
        
        for link in page.links:
            p = Page.get_id_by_url(link, update=False)
            if p is not None:
                calculate_rank.delay(p)
