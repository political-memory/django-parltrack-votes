# -*- coding:Utf-8 -*-
from django.db import models
from parltrack_meps.models import MEP

class Proposal(models.Model):
    title = models.CharField(max_length=255, unique=True)
    ponderation = models.IntegerField(default=1)
    _date = models.DateField(default=None, null=True, blank=True)

    @property
    def date(self):
        if self._date is None:
            self._date = self.proposalpart_set.all()[0].datetime.date()
            self.save()
        return self._date

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('-_date', )


class ProposalPart(models.Model):
    datetime = models.DateTimeField()
    subject = models.CharField(max_length=255)
    part = models.CharField(max_length=255)
    description = models.CharField(max_length=511)
    proposal = models.ForeignKey(Proposal)

    def __unicode__(self):
        return self.subject

    class MetaClass:
        ordering = ['datetime']


class Vote(models.Model):
    choice = models.CharField(max_length=15, choices=((u'for', u'for'), (u'against', u'against'), (u'abstention', u'abstention'), (u'absent', u'absent')))
    name = models.CharField(max_length=127)
    proposal_part = models.ForeignKey(ProposalPart)
    mep = models.ForeignKey(MEP, null=True)
    raw_mep = models.CharField(max_length=255)
    raw_group = models.CharField(max_length=255)

    class Meta:
        ordering = ["choice"]

    def __unicode__(self):
        return '%s (%s)' % (self.name, self.choice)
