Introduction
============

European part vote related code and models extracted from [memopol](https://memopol.lqdn.fr) [code base](https://gitorious.org/memopol2-0).

This contains the models needed to work with Votes and also the script to match between MEPs and votes data.

Dependancies
============

You'll need [django-parltrack-votes-data](https://github.com/Psycojoker/django-parltrack-votes-data) and [django-parltrack-meps](https://github.com/Psycojoker/django-parltrack-meps)

Installation for dev
====================

For dev, this will look something like this:

    virtualenv ve
    source ve/bin/activate

    git clone git@github.com:Psycojoker/django-parltrack-votes-data.git
    git clone git@github.com:Psycojoker/django-parltrack-votes.git
    git clone git@github.com:Psycojoker/django-parltrack-meps.git

    pip install django
    pip install -r django-parltrack-votes-data/requirements.txt

    django-admin.py startproject testing
    cd testing

    ln -s ../django-parltrack-meps/django\_parltrack\_meps .
    ln -s ../django-parltrack-votes/django\_parltrack\_votes.
    ln -s ../django-parltrack-votes-data/django\_parltrack\_votes\_data .

    vi testing/settings.py # here, set the database
    # and add 'django_parltrack_votes_data' 'django_parltrack_votes' 'django_parltrack_meps'
    # to the list of installed apps

    python manage.py syncdb

    python manage.py update_meps
    python manage.py import_ep_votes_data

Usage
=====

Run:

    python manage.py link_a_proposal_part_votes_to_meps <votes_data id>

To try to link the votes of a proposal part to their respectives meps. WARNING: high chance of failing if the vote is old.

Licence
=======

Like memopol: aGPLv3+
