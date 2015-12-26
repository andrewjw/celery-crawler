import pickle
import time
import requests

from celerycrawler import settings
from datetime import datetime
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from urllib.request import urlopen, Request, HTTPError
from urllib.request import install_opener, build_opener, HTTPRedirectHandler
from couchdb.mapping import Document, TextField, DateTimeField, ListField, FloatField
from django.core.cache import cache

install_opener(build_opener(HTTPRedirectHandler()))

class Page(Document):
    type = TextField(default="page")
    url = TextField()
    raw = TextField()
    content = TextField()
    links = ListField(TextField())
    rank = FloatField(default=0)
    last_checked = DateTimeField(default=datetime.now)

    def is_valid(self):
        return (datetime.now() - self.last_checked).days < 7

    def update(self):
        print("updating page")
        
        parse = urlparse(self.url)
        robotstxt = RobotsTxt.get_by_domain(parse.scheme, parse.netloc)
        #if not robotstxt.is_allowed(self.url):
        #    return False

        while cache.get(parse.netloc) is not None:
            time.sleep(1)

        cache.set(parse.netloc, True, 10)

        print("getting: {}".format(self.url))
        resp = requests.get(self.url, headers={'User-Agent':
                                               settings.USER_AGENT})

        ctype = resp.headers['content-type']
        if not ctype.startswith("text/html"):
            print("unsupported content-type: {}".format(ctype))
            return

        print("setting Page.content...")
        self.content = resp.text
        self.raw = resp.text

        self.last_checked = datetime.now()
        self.store(settings.db)

    @staticmethod
    def count():
        r = settings.db.view("page/by_url", limit=0)
        return r.total_rows

    @staticmethod
    def get_top_by_rank(limit=10):
        r = settings.db.view("page/by_rank", limit=limit)
        docs = []
        for row in r.rows:
            docs.append(Page.load(settings.db, row.value))
        return docs

    @staticmethod
    def get_by_url(url, update=True):
        r = settings.db.view("page/by_url", key=url)
        if len(r.rows) == 1:
            doc = Page.load(settings.db, r.rows[0].value)
            if doc.is_valid():
                return doc
        elif not update:
            return None
        else:
            doc = Page(url=url)
        print("Page.get_by_url: doc.update() ...")
        doc.update()

        return doc

    @staticmethod
    def get_id_by_url(url, update=True):
        r = settings.db.view("page/by_url", key=url)
        if len(r) == 1:
            return r.rows[0].value
        else:
            doc = Page.get_by_url(url, update=update)
            if doc is not None:
                return doc.id
            else:
                return None

    @staticmethod
    def get_links_to_url(url):
        return [row.value for row in settings.db.view("page/links_to_url", key=url).rows]

class RobotsTxt(Document):
    type = TextField(default="robotstxt")

    domain = TextField()
    protocol = TextField()

    robot_parser_pickle = TextField()

    def _get_robot_parser(self):
        parser = RobotFileParser()
        parser.set_url(self.protocol + "://" + self.domain + "/robots.txt")

        return parser

    def is_valid(self):
        parser = self._get_robot_parser()
        return (time.time() - parser.mtime()) < 7*24*60*60

    def is_allowed(self, url):
        parser = self._get_robot_parser()
        return parser.can_fetch(settings.USER_AGENT, url)

    def update(self):
        while cache.get(self.domain) is not None:
            time.sleep(1)
        cache.set(self.domain, True, 10)

        print("getting %s://%s/robots.txt" % (self.protocol, self.domain))
        parser = self._get_robot_parser()
        parser.read()
        parser.modified()

        self.store(settings.db)

    @staticmethod
    def get_by_domain(protocol, domain):
        r = settings.db.view("robotstxt/by_domain", key=[protocol, domain])
        if len(r) > 0:
            doc = RobotsTxt.load(settings.db, r.rows[0].value)
            if doc.is_valid():
                return doc
        else:
            doc = RobotsTxt(protocol=protocol, domain=domain)

        doc.update()
        doc.store(settings.db)

        return doc
