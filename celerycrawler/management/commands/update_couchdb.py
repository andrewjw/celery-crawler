import couchdb
import glob
import os

from celerycrawler import settings
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    help = "Update couchdb views"

    can_import_settings = True

    def handle_noargs(self, **options):
        couchdir = os.path.realpath(os.path.split(__file__)[0] + "../../../couchviews")

        databases = glob.glob(couchdir+"/*")
        for d in databases:
            if not os.path.isdir(d):
                continue

            db = getattr(settings, d.split("/")[-1])

            for design in glob.glob(d + "/*"):
                design = design.split("/")[-1]
                try:
                    doc = db["_design/" + design]
                except couchdb.http.ResourceNotFound:
                    doc = {"_id": "_design/" + design}

                doc["views"] = {}
                for mapreduce in glob.glob(d+"/"+design+"/*"):
                     mapreduce = mapreduce.split("/")[-1]
                     mr = {}
                     mr["map"] = open(d+"/"+design+"/"+mapreduce+"/map.js").read()
                     try:
                         mr["reduce"] = reduce = open(d+"/"+design+"/"+mapreduce+"/reduce.js").read()
                     except IOError:
                         pass

                     doc["views"][mapreduce] = mr

                db["_design/" + design] = doc
