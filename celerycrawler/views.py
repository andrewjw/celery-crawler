from django.shortcuts import render_to_response
from whoosh.qparser import QueryParser

from celerycrawler.indexer import get_searcher, schema
from celerycrawler.models import Page

def index(req):
    return render_to_response("index.html", { "doc_count": Page.count(), "top_docs": Page.get_top_by_rank(limit=20) })

def search(req):
    searcher = get_searcher()

    q = QueryParser("content", schema=schema).parse(req.GET["q"])

    results = searcher.search(q, limit=100)

    if len(results) > 0:
        max_score = max([r.score for r in results])
        max_rank = max([r.fields()["rank"] for r in results])

        combined = []
        for r in results:
            fields = r.fields()
            r.score = r.score/max_score
            r.rank = fields["rank"]/max_rank
            r.combined = r.score + r.rank
            combined.append(r)

        combined.sort(key=lambda x: x.combined, reverse=True)
    else:
        combined = []

    return render_to_response("results.html", { "q": req.GET["q"], "results": combined })
