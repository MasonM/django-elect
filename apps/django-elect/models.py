from datetime import date

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User


class Election(models.Model):
    """
    Represents elections. which can be composed of one or more ballots.
    Voting only allowed between vote_start and vote_end dates.
    """
    name = models.CharField(max_length=255, blank=False, unique=True)
    introduction = models.TextField(blank=True,
        help_text="This is printed at the top of the voting page below "+\
        "the header. Enter the text as HTML.")
    vote_start = models.DateField(help_text="Start date for voting, inclusive")
    vote_end = models.DateField(help_text="End date for voting, inclusive")
    biographies_url = models.URLField(max_length=255, blank=True,
        help_text="This is used to linkify candidate names on the voting "+\
        "page. It must have named anchors for every candidate in the form "+\
        "'FirstnameLastname' (no spaces).")

    def __unicode__(self):
        return unicode(self.name)

    def voting_allowed(self):
        """
        Returns True if if today is between vote_start and vote_end, inclusive.
        """
        return self.vote_start <= date.today() <= self.vote_end

    def has_voted(self, account):
        """ Returns True if given account has voted for this election """
        return self.votes.filter(account=account).count() != 0

    def disassociate_accounts(self):
        """
        Sets account = NULL for all Vote objects associated with this election.
        Returns number of rows affected.
        """
        from django.db import connection
        cursor = connection.cursor()
        query = """
            UPDATE election_vote
            SET account_id = NULL
            WHERE election_id = %i
        """
        cursor.execute(query % self.pk)
        return cursor.rowcount

    class Meta:
        ordering = ['vote_start']
        get_latest_by = "vote_start"


class Ballot(models.Model):
    """
    Represents a ballot of a certain type (plurality, etc.) for an election.
    Each ballot has one or more candidates associated with it.
    """
    TYPES = (
        ("Pl", "Plurality"),
        ("Pr", "Preferential"),
    )
    election = models.ForeignKey(Election, related_name="ballots")
    position_number = models.PositiveSmallIntegerField(default=1,
        help_text="Change this if you want to customize the order in which "+\
        "ballots are shown for an election.")    
    description = models.CharField(max_length=255, blank=True)
    introduction_override = models.TextField(blank=True,
        help_text="If this field is non-empty, it will replace the default "+\
        "text shown below the ballot header on the voting page. Enter the "+\
        "text as HTML.")
    type = models.CharField(max_length=2, blank=False, choices=TYPES)
    seats_available = models.PositiveSmallIntegerField()
    write_in_available = models.BooleanField(default=True)

    def __unicode__(self):
        return "%s %s: %s" % (self.get_type_display(),
                              unicode(self.election), self.description)

    def get_candidate_stats(self):
        """
        Returns list of form [(candidate1, x1), (candidate2, x2), ...]
        where x1, x2, ... are the total number of votes if self.type == "Pl"
        or the sum of the point values if self.type == "Pr"
        """
        stats = []
        if self.type == "Pl":
            stats = [(c, VotePlurality.objects.filter(candidate=c).count())
                     for c in self.candidates.all()]
            # sort according to # of votes, in reverse order
            stats.sort(key=lambda x: x[1], reverse=True)
        elif self.type == "Pr":
            #fall back to SQL since Django DB API doesn't support sum()
            from django.db import connection
            cursor = connection.cursor()
            query = """
                SELECT c.id, IF(v.point IS NULL, 0, SUM(v.point)) AS points
                FROM election_ballot b
                JOIN election_candidate c ON (c.ballot_id=b.id)
                LEFT JOIN election_votepreferential v ON (v.candidate_id=c.id)
                WHERE b.id = '%i'
                GROUP BY c.id
                ORDER BY points DESC
            """
            cursor.execute(query % self.id)
            stats = [(Candidate.objects.get(id=c[0]), c[1])
                     for c in cursor.fetchall()]
        return stats

    def has_incumbents(self):
        """
        Returns True if ballot has any candidates associated with it that
        are incumbents
        """
        return self.candidates.filter(incumbent=True).count() > 0

    class Meta:
        ordering = ['election', 'position_number', 'type', 'description']


class Candidate(models.Model):
    """
    Model for election candidates (e.g. governing board, nominating committee).
    Each candidate must be associated with a single ballot.
    """
    ballot = models.ForeignKey(Ballot, related_name="candidates")
    first_name = models.CharField(max_length=255, blank=False)
    last_name = models.CharField(max_length=255, blank=False)
    institution = models.CharField(max_length=255, blank=True)
    incumbent = models.BooleanField()
    image_url = models.URLField(max_length=255, blank=True)
    write_in = models.BooleanField(default=False)

    def __unicode__(self):
        parenthesis = self.institution or (self.write_in and "write-in")
        return "%s%s %s (%s)" % (self.incumbent and "*" or "",
                                 self.first_name, self.last_name,
                                 parenthesis)

    def get_name(self):
        """Returns full name of candidate."""
        return self.first_name+" "+self.last_name

    class Meta:
        ordering = ['last_name', 'first_name']


class Vote(models.Model):
    """
    Vote associates individual candidate selections with an account and
    an election.
    """
    account = models.ForeignKey(User, null=True)
    election = models.ForeignKey(Election, related_name="votes",
        limit_choices_to=Q(vote_start__lte=date.today()) &\
                         Q(vote_end__gte=date.today()))

    def __unicode__(self):
        return unicode(self.account) + " - " + unicode(self.election)

    def get_details(self):
        """
        Returns list in form
        [ (ballot1, [vote1, vote2, ...]), (ballot2, [vote3, vote4, ...]), ...]
        """
        details = []
        for ballot in self.election.ballots.all():
            votes = []
            if ballot.type == "Pl":
                votes = (self.pluralities
                             .filter(candidate__ballot=ballot)
                             .order_by('candidate'))
            elif ballot.type == "Pr":
                votes = (self.preferentials
                             .filter(candidate__ballot=ballot)
                             .order_by('candidate'))
            details.append((ballot, votes))
        return details

    def get_points_for_candidates(self, candidates):
        """
        Given a list of candidates, constructs a list of the same length
        wherein the candidate is replaced by 0 if vote doesn't contain the
        candidate and the point value (or 1 in case of plurality) if so.
        """
        point_list = []
        for candidate in candidates:
            if candidate.ballot.type == "Pr":
                vote = self.preferentials.filter(candidate=candidate)
                point_list.append(vote[0].point if vote else 0)
            elif candidate.ballot.type == "Pl":
                has_voted = self.pluralities.filter(candidate=candidate)
                point_list.append(1 if has_voted else 0)
        return point_list


def _get_choices(type):
    """
    Returns Q object that matches a ballot of the specified type that's
    currently active, i.e. today is between the vote_start and vote_end dates
    """
    return Q(ballot__type=type) &\
           Q(ballot__election__vote_start__lte=date.today()) &\
           Q(ballot__election__vote_end__gte=date.today())


class VotePreferential(models.Model):
    """
    Vote for a candidate on a preferential ballot (i.e. Ballot.type="Pr")
    """
    vote = models.ForeignKey(Vote, related_name="preferentials")
    candidate = models.ForeignKey(Candidate,
        limit_choices_to=_get_choices("Pr"))
    point = models.PositiveSmallIntegerField()

    def __unicode__(self):
        return "%s vote, %i points for %s" % (self.vote, self.point,
                                              self.candidate.get_name())


class VotePlurality(models.Model):
    """
    Vote for a candidate on a plurality ballot (i.e. Ballot.type="Pl")
    """
    vote = models.ForeignKey(Vote, related_name="pluralities")
    candidate = models.ForeignKey(Candidate,
        limit_choices_to=_get_choices("Pl"))

    def __unicode__(self):
        return "%s vote for %s" % (self.vote, self.candidate.get_name())
