from datetime import datetime

from django.http import Http404
from django.db import models, connection
from django.db.models import Q
from django_elect import settings


class VotingNotAllowedException(Exception):
    pass


class Election(models.Model):
    """
    Represents elections. which can be composed of one or more ballots.
    Voting only allowed between vote_start and vote_end dates.
    """
    name = models.CharField(max_length=255, blank=False, unique=True,
        help_text="Used to uniquely identify elections. Will be shown "+\
        "with ' Election' appended to it on all publicly-visible pages.")
    introduction = models.TextField(blank=True,
        help_text="This is printed at the top of the voting page below "+\
        "the header. Enter the text as HTML.")
    vote_start = models.DateTimeField(help_text="Start of voting")
    vote_end = models.DateTimeField(help_text="End of voting")
    allowed_voters = models.ManyToManyField(settings.DJANGO_ELECT_USER_MODEL,
        blank=True,
        help_text="If empty, all registered users will be allowed to vote.")

    def __unicode__(self):
        return unicode(self.name)

    def voting_allowed_for_user(self, user):
        """
        Returns True if not is between vote_start and vote_end, inclusive,
        and given user is in allowed_voters and user hasn't already voted.
        """
        return (self.voting_allowed() and not self.has_voted(user) and
            (self.allowed_voters.count() == 0 or
            self.allowed_voters.filter(id=user.id)))

    def voting_allowed(self):
        """
        Returns True if now is between vote_start and vote_end, inclusive.
        """
        return self.vote_start <= datetime.now() <= self.vote_end

    def create_vote(self, user):
        """
        Checks that the given account can vote in this election, and if so,
        creates and returns a Vote object.
        """
        if not self.voting_allowed_for_user(user):
            msg = 'The account %s is not allowed to vote in this election.'
            raise VotingNotAllowedException(msg % unicode(user))
        return self.votes.create(account=user, election=self)

    def has_voted(self, account):
        """ Returns True if given account has voted for this election """
        return self.votes.filter(account=account).count() != 0

    def get_full_statistics(self):
        """
        Returns dictionary of the following form:
        {
            "candidates": [ Candidate#1, Candidate#2, ... ],
            "ballots": [ Ballot#1, Ballot#2, ... ],
            "votes": {
                Vote#1: [ points_for_candidate1, points_for_candidate2, ... ],
                Vote#2: [...],
            },
        }
        Where "points_for_candidate#" is 0 if the vote doesn't contain the
        corresponding candidate and either the point value (for preferential
        ballots) or 1 (for plurality) if so. Candidates are ordered by ballot
        ID and then by candidate id.
        """
        query = """
            SELECT
                v.id AS vote_id,
                c.id AS candidate_id,
                IF(
                    b.type = "Pl",
                    IF(vpl.id IS NULL, 0, 1),
                    IFNULL(SUM(vpr.point), 0)
                ) AS point
            FROM %(vote)s v
            JOIN %(ballot)s b ON (b.election_id = v.election_id)
            JOIN %(candidate)s c ON (c.ballot_id = b.id)
            LEFT JOIN %(vote_plurality)s vpl ON (vpl.vote_id = v.id
                AND vpl.candidate_id = c.id)
            LEFT JOIN %(vote_preferential)s vpr ON (vpr.vote_id = v.id
                AND vpr.candidate_id = c.id)
            WHERE v.election_id = '%(id)i'
            GROUP BY v.id, c.id
            ORDER BY v.id, b.id, c.id
        """
        query %= {
            'vote': Vote._meta.db_table,
            'ballot': Ballot._meta.db_table,
            'candidate': Candidate._meta.db_table,
            'vote_plurality': VotePlurality._meta.db_table,
            'vote_preferential': VotePreferential._meta.db_table,
            'id': self.pk,
        }

        cursor = connection.cursor()
        cursor.execute(query)

        stats = {
            'candidates': [],
            'ballots': [],
            'votes': {},
        }

        vote_points = {}
        for row in cursor.fetchall():
            vote_id, candidate_id, point = row[0], row[1], row[2]
            vote_points.setdefault(vote_id, []).append(point)
            # Every vote in the result set has the same list of candidates, so
            # we only need to populate the candidates and ballots lists on
            # the first one.
            if len(vote_points) == 1:
                candidate = Candidate.objects.get(id=candidate_id)
                stats['candidates'].append(candidate)
                if candidate.ballot not in stats['ballots']:
                    stats['ballots'].append(candidate.ballot)

        # convert vote_ids into Vote objects
        for vote_id, points in vote_points.iteritems():
            vote = Vote.objects.get(id=vote_id)
            stats['votes'][vote] = points

        return stats

    def disassociate_accounts(self):
        """
        Sets account = NULL for all Vote objects associated with this election.
        Returns number of rows affected.
        """
        from django.db import connection
        cursor = connection.cursor()
        query = """
            UPDATE %(vote)s
            SET account_id = NULL
            WHERE election_id = %(id)i
        """
        cursor.execute(query % {
            'vote': Vote._meta.db_table,
            'id': self.pk,
        })
        return cursor.rowcount

    @staticmethod
    def get_latest_or_404():
        """
        Similar to the get_object_or_404() function, except returns the
        latest Election instead.
        """
        try:
            return Election.objects.latest()
        except Election.DoesNotExist:
            raise Http404("No elections have been entered yet.")

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
    introduction = models.TextField(blank=True,
        help_text="If this field is non-empty, it will be shown below the "+\
        "ballot header on the voting page. Enter the text as HTML.")
    type = models.CharField(max_length=2, blank=False, choices=TYPES,
        default="Pl")
    seats_available = models.PositiveSmallIntegerField()
    is_secret = models.BooleanField(default=False,
        help_text="Check this for a secret ballot. This means that only the "+\
        "fact that a voter voted will be recorded, not his or her choices.")
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
                FROM %(ballot)s b
                JOIN %(candidate)s c ON (c.ballot_id=b.id)
                LEFT JOIN %(vote_preferential)s v ON (v.candidate_id=c.id)
                WHERE b.id = '%(id)i'
                GROUP BY c.id
                ORDER BY points DESC
            """
            cursor.execute(query % {
                'ballot': Ballot._meta.db_table,
                'candidate': Candidate._meta.db_table,
                'vote_preferential': VotePreferential._meta.db_table,
                'id': self.pk,
            })
            stats = [(Candidate.objects.get(id=c[0]), c[1])
                     for c in cursor.fetchall()]
        return stats

    def candidates_with_biographies(self):
        return self.candidates.exclude(biography="")

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
    incumbent = models.BooleanField(default=False)
    image_url = models.URLField(max_length=255, blank=True)
    write_in = models.BooleanField(default=False)
    biography = models.TextField(blank=True,
        help_text="Enter the candidate's biography here as HTML. It will "+\
        "be shown when the user clicks the candidate's name. If you leave "+\
        "this field blank, the candidate's name will not be a link.")

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
    account = models.ForeignKey(settings.DJANGO_ELECT_USER_MODEL, null=True)
    election = models.ForeignKey(Election, related_name="votes")

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


def _get_choices(ballot_type):
    """
    Returns Q object that matches a ballot of the specified type that's
    currently active, i.e. now() is between the vote_start and vote_end dates
    """
    return Q(ballot__type=ballot_type) &\
           Q(ballot__election__vote_start__lte=datetime.now()) &\
           Q(ballot__election__vote_end__gte=datetime.now())


class VotePreferential(models.Model):
    """
    Vote for a candidate on a preferential ballot (i.e. Ballot.type="Pr")
    """
    vote = models.ForeignKey(Vote, related_name="preferentials", null=True)
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
    vote = models.ForeignKey(Vote, related_name="pluralities", null=True)
    candidate = models.ForeignKey(Candidate,
        limit_choices_to=_get_choices("Pl"))

    def __unicode__(self):
        return "%s vote for %s" % (self.vote, self.candidate.get_name())
