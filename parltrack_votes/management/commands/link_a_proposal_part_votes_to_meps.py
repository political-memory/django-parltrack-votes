# -*- coding:Utf-8 -*-

import re
import sys
import json

from urllib import urlopen
from datetime import datetime, time

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction

from parltrack_meps.models import MEP
from parltrack_votes.models import VotesData
from parltrack_votes.models import Proposal, ProposalPart, Vote


class Command(BaseCommand):
    help = 'Create a voting recommandation, WARNING: due to the nature of the data, there is sadly non-negligible chances that this command will fail'

    def handle(self, *args, **options):
        if not args:
            print >>sys.stderr, "Usage: %s <votes_data id>" % __file__
            sys.exit(1)

        votes_data_id = args[0]

        with transaction.commit_on_success():
            create_recommendation(votes_data_id)



def create_recommendation(votes_data_id):
    votes_data = VotesData.objects.get(id=votes_data_id)
    data = json.loads(votes_data.data)

    # XXX dunno if we still want that
    # ProposalPart.objects.filter(datetime=datetime.combine(votes_data.date, time()),
                                  # subject="".join(votes_data.title.split("-")[:-1]),
                                  # part=data["issue_type"]).delete()

    proposal = get_proposal(votes_data.proposal_name)
    print "Creating recommendation"
    r = ProposalPart.objects.create(datetime=datetime.combine(votes_data.date, time()),
                                  subject="".join(votes_data.title.split("-")[:-1]),
                                  part=data["issue_type"],
                                  proposal=proposal)

    # clean old votes
    # XXX dunno if we still want this
    #Vote.objects.filter(recommendation=r).delete()

    choices = (('Against', 'against'), ('For', 'for'), ('Abstain', 'abstention'))
    for key, choice in choices:
        for group in data[key]["groups"]:
            for mep in group["votes"]:
                in_db_mep = find_matching_mep_in_db(mep)
                print "Create vote for", in_db_mep.first_name, in_db_mep.last_name
                Vote.objects.create(choice=choice, proposal_part=r, mep=in_db_mep, name=votes_data.proposal_name)

    sys.stdout.write("\n")
    votes_data.imported = True
    votes_data.save()


def find_matching_mep_in_db(mep):
    mep = mep["orig"]
    mep = mep.replace(u"ß", "SS")
    mep = mep.replace("(The Earl of) ", "")
    try:
        representative = MEP.objects.filter(active=True, last_name=mep)
        if not representative:
            representative = MEP.objects.filter(active=True, last_name__iexact=mep)
        if not representative:
            representative = MEP.objects.filter(active=True, last_name__iexact=re.sub("^DE ", "", mep.upper()))
        if not representative:
            representative = MEP.objects.filter(active=True, last_name__contains=mep.upper())
        if not representative:
            representative = MEP.objects.filter(active=True, full_name__contains=re.sub("^MC", "Mc", mep.upper()))
        if not representative:
            representative = MEP.objects.filter(active=True, full_name__icontains=mep)
        if not representative:
            representative = [dict([("%s %s" % (x.last_name.lower(), x.first_name.lower()), x) for x in MEP.objects.filter(active=True)])[mep.lower()]]
        representative = representative[0]
    except Exception as e:
        print "WARNING: failed to get mep using internal db, fall back on parltrack (exception: %s)" % e
        print "http://parltrack.euwiki.org/mep/%s?format=json" % (mep.encode("Utf-8"))
        mep_ep_id = json.loads(urlopen("http://parltrack.euwiki.org/mep/%s?format=json" % (mep.encode("Utf-8"))).read())["UserID"]
        print mep_ep_id, mep, json.loads(urlopen("http://parltrack.euwiki.org/mep/%s?format=json" % (mep.encode("Utf-8"))).read())["Name"]["full"]
        representative = MEP.objects.get(ep_id=mep_ep_id).representative_ptr
    return representative


# vim:set shiftwidth=4 tabstop=4 expandtab:
