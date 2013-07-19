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
import urllib
from os.path import join
from json import loads
from dateutil.parser import parse
from datetime import datetime

from django.db import transaction, connection, reset_queries
from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand

from parltrack_votes.models import Proposal, ProposalPart


def get_proposal(proposal_name):
    proposal = Proposal.objects.filter(title=proposal_name)
    if proposal:
        return proposal[0]
    return Proposal.objects.create(title=proposal_name)


class Command(BaseCommand):
    help = 'Import vote data of the European Parliament, this is needed to be able to create voting recommendations. If given a file in arg use it instead download it from parltrack'

    def handle(self, *args, **options):
        if args:
            json_file = args[0]
        else:
            json_file = retrieve_json()

        print "read file", json_file
        start = datetime.now()
        with transaction.commit_on_success():
            for a, vote in enumerate(json_parser_generator(json_file)):
                create_in_db(vote)
                reset_queries()  # to avoid memleaks in debug mode
                sys.stdout.write("%s\r" % a)
                sys.stdout.flush()
        print datetime.now() - start
        sys.stdout.write("\n")


def json_parser_generator(json_file):
    """Parse the json and yield one parltrack vote at the time
     I need to parse the json file by hand, otherwise this eat way too much memory
    """
    current_json = ""
    for i in open(json_file, "r"):
        if i in ("[{\n", "{\n"):
            # print "begin doc"
            current_json += "{\n"
        elif "}\n" == i:
            # print "end"
            current_json += "\n}"
            yield loads(current_json)
            current_json = ""
        elif i == ",\n":
            pass
        else:
            current_json += i


def retrieve_json():
    "Download and extract json file from parltrack"
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
    return json_file


def create_in_db(vote):
    cur = connection.cursor()
    proposal_name = vote.get("report", vote["title"])
    vote_datetime = make_aware(parse(vote["ts"]), pytz.timezone("Europe/Brussels"))
    subject = "".join(vote["title"].split("-")[:-1])
    proposal = get_proposal(proposal_name)
    part = vote.get("issue_type", proposal_name)

    r = ProposalPart.objects.create(
        datetime=vote_datetime,
        subject=subject,
        part=part,
        proposal=proposal
    )

    # print vote
    args = []
    choices = (('Against', 'against'), ('For', 'for'), ('Abstain', 'abstention'))
    for key, choice in choices:
        if key in vote:
            for group in vote[key]["groups"]:
                for mep in group["votes"]:
                    # in_db_mep = find_matching_mep_in_db(mep)
                    if isinstance(mep, dict):
                        mep_name = mep['orig']
                    else:
                        mep_name = mep
                    group_name = group['group']
                    # print "Create vote for", mep_name

                    args.append((choice, proposal_name, r.id, mep_name, group_name))
    cur.executemany("INSERT INTO parltrack_votes_vote (choice, name, proposal_part_id, raw_mep, raw_group) values (%s, %s, %s, %s, %s)", args)

# vim:set shiftwidth=4 tabstop=4 expandtab:
