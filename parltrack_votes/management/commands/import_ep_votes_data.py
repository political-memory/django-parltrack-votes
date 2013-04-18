# -*- coding:Utf-8 -*-

# This file is part of django-parltrack-votes-data.
#
# django-parltrack-votes-data is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or any later version.
#
# django-parltrack-votes-data is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU General Affero Public
# License along with Foobar.
# If not, see <http://www.gnu.org/licenses/>.
#
# Copyright (C) 2013  Laurent Peuch <cortex@worlddomination.be>

import os
import sys
import pytz
from os.path import join
from json import loads, dumps
from dateutil.parser import parse
import urllib

from django.db import transaction, connection, reset_queries
from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand

from parltrack_votes.models import VotesData


class Command(BaseCommand):
    help = 'Import vote data of the European Parliament, this is needed to be able to create voting recommendations'

    def handle(self, *args, **options):
        if os.system("which unxz > /dev/null") != 0:
            raise Exception("XZ binary missing, please install xz")
        print "Clean old downloaded files"
        json_file = join("/tmp", "ep_votes.json")
        xz_file = join("/tmp", "ep_votes.json.xz")
        if os.path.exists(json_file):
            os.remove(json_file)
        if os.path.exists(xz_file):
            os.remove(xz_file)
        print "Download vote data from parltrack"
        urllib.urlretrieve('http://parltrack.euwiki.org/dumps/ep_votes.json.xz', xz_file)
        print "unxz it"
        os.system("unxz %s" % xz_file)
        print "cleaning old votes data..."
        connection.cursor().execute("DELETE FROM %s" % VotesData._meta.db_table)
        transaction.commit_unless_managed()
        print VotesData.objects.count()
        print "read file"
        current_json = ""
        a = 1
        with transaction.commit_on_success():
        # I need to parse the json file by hand, otherwise this eat way to much memory
            for i in open(json_file, "r"):
                if i in ("[{\n", "{\n"):
                    # print "begin doc"
                    current_json += "{\n"
                elif "}\n" == i:
                    # print "end"
                    current_json += "\n}"
                    vote = loads(current_json)
                    VotesData.objects.create(proposal_name=vote.get("report", vote["title"]),
                                            title=vote["title"],
                                            data=dumps(vote, indent=4),
                                            date=make_aware(parse(vote["ts"]), pytz.timezone("Europe/Brussels"))),
                    reset_queries() # to avoid memleaks in debug mode
                    current_json = ""
                    sys.stdout.write("%s\r" % a)
                    sys.stdout.flush()
                    a += 1
                elif i == ",\n":
                    pass
                else:
                    current_json += i
            sys.stdout.write("\n")

# vim:set shiftwidth=4 tabstop=4 expandtab:
