import base64
from datetime import datetime
import pickle
from robotparser import RobotFileParser
import time
from urlparse import urlparse
from urllib2 import urlopen, Request, HTTPError, install_opener, build_opener, HTTPRedirectHandler

from django.core.cache import cache

from couchdb.mapping import Document, TextField, DateTimeField, ListField, FloatField

import settings

install_opener(build_opener(HTTPRedirectHandler()))

class Page(Document):
    type = TextField(default="page")

    url = TextField()

    content = TextField()

    links = ListField(TextField())

    rank = FloatField(default=0)

    last_checked = DateTimeField(default=datetime.now)

    def is_valid(self):
        return (datetime.now() - self.last_checked).days < 7

    def update(self):
        parse = urlparse(self.url)

        robotstxt = RobotsTxt.get_by_domain(parse.scheme, parse.netloc)
        if not robotstxt.is_allowed(parse.netloc):
            return False

        while cache.get(parse.netloc) is not None:
            time.sleep(1)
        cache.set(parse.netloc, True, 10)

        print "getting", self.url
        req = Request(self.url, None, { "User-Agent": settings.USER_AGENT })

        resp = urlopen(req)
        if not resp.info()["Content-Type"].startswith("text/html"):
            return
        self.content = resp.read().decode("utf8")
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
        if self.robot_parser_pickle is not None:
            return pickle.loads(base64.b64decode(self.robot_parser_pickle))
        else:
            parser = RobotFileParser()
            parser.set_url(self.protocol + "://" + self.domain + "/robots.txt")
            self.robot_parser = parser

            return parser
    def _set_robot_parser(self, parser):
        self.robot_parser_pickle = base64.b64encode(pickle.dumps(parser))
    robot_parser = property(_get_robot_parser, _set_robot_parser)

    def is_valid(self):
        return (time.time() - self.robot_parser.mtime()) < 7*24*60*60

    def is_allowed(self, url):
        return self.robot_parser.can_fetch(settings.USER_AGENT, url)

    def update(self):
        while cache.get(self.domain) is not None:
            time.sleep(1)
        cache.set(self.domain, True, 10)

        print "getting %s://%s/robots.txt" % (self.protocol, self.domain)
        parser = self.robot_parser
        parser.read()
        parser.modified()
        self.robot_parser = parser

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
