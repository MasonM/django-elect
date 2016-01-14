from freezegun import freeze_time
from datetime import datetime

from django.test import TestCase
from django.apps import apps

from django_elect import settings
from django_elect.models import Ballot, Candidate, Election, Vote, \
    VotePlurality, VotePreferential, VotingNotAllowedException


@freeze_time("2010-10-10 00:00:00")
class BaseTestCase(TestCase):
    def setUp(self):
        user_model = apps.get_model(settings.DJANGO_ELECT_USER_MODEL)
        self.user1 = user_model.objects.create(username="user1")
        self.user2 = user_model.objects.create(username="user2")
        self.election_current = Election.objects.create(
            name="current",
            introduction="Intro1",
            vote_start=datetime(2010, 10, 1),
            vote_end=datetime(2010, 10, 11))

    def create_candidate(self, ballot, incumbent=True, last_name='bar'):
        return Candidate.objects.create(
            ballot=ballot,
            first_name="foo",
            last_name=last_name,
            incumbent=incumbent)

    def create_current_pl_ballot(self, seats_available=2):
        return Ballot.objects.create(
            election=self.election_current,
            type="Pl",
            seats_available=seats_available)

    def create_current_pr_ballot(self, seats_available=2):
        return Ballot.objects.create(
            election=self.election_current,
            type="Pr",
            seats_available=seats_available)


class ElectionTestCase(BaseTestCase):
    "Tests for the Election model"
    def test_unicode(self):
        self.assertEqual(unicode(self.election_current), u"current")

    def test_voting_allowed_with_current_election(self):
        self.assertTrue(self.election_current.voting_allowed())

    def test_voting_allowed_with_finished_election(self):
        election_finished = Election(
            vote_start=datetime(2010, 10, 1),
            vote_end=datetime(2010, 10, 9))
        self.assertFalse(election_finished.voting_allowed())

    def test_voting_allowed_with_future_election(self):
        election_future = Election(
            vote_start=datetime(2010, 10, 11),
            vote_end=datetime(2010, 10, 17))
        self.assertFalse(election_future.voting_allowed())

    def test_has_voted_with_user_not_allowed_to_vote(self):
        self.assertFalse(self.election_current.has_voted(self.user1))

    def test_has_voted_with_user_who_already_voted(self):
        self.election_current.allowed_voters.add(self.user1)
        Vote.objects.create(account=self.user1, election=self.election_current)
        self.assertTrue(self.election_current.has_voted(self.user1))
        self.assertFalse(self.election_current.has_voted(self.user2))

    def test_voting_allowed_for_user_with_empty_allowed_voters_list(self):
        self.assertTrue(self.election_current.voting_allowed_for_user(self.user1))
        self.assertTrue(self.election_current.voting_allowed_for_user(self.user2))

    def test_voting_allowed_for_user_with_nonempty_allowed_voters_list(self):
        self.election_current.allowed_voters.add(self.user1)
        self.assertTrue(self.election_current.voting_allowed_for_user(self.user1))
        self.assertFalse(self.election_current.voting_allowed_for_user(self.user2))

    def test_voting_allowed_for_user_who_voted_with_empty_allowed_voters_list(self):
        self.assertTrue(self.election_current.voting_allowed_for_user(self.user1))
        Vote.objects.create(account=self.user1, election=self.election_current)
        self.assertFalse(self.election_current.voting_allowed_for_user(self.user1))

    def test_voting_allowed_for_user_who_voted_with_nonempty_allowed_voters_list(self):
        self.election_current.allowed_voters.add(self.user1)
        self.assertTrue(self.election_current.voting_allowed_for_user(self.user1))
        Vote.objects.create(account=self.user1, election=self.election_current)
        self.assertFalse(self.election_current.voting_allowed_for_user(self.user1))

    def test_voting_allowed_for_user_with_finished_election(self):
        election_finished = Election.objects.create(
            name="finished",
            vote_start=datetime(2010, 10, 1),
            vote_end=datetime(2010, 10, 9))
        election_finished.allowed_voters.add(self.user1)
        self.assertFalse(election_finished.voting_allowed_for_user(self.user1))

    def test_disassociate_accounts(self):
        Vote.objects.create(account=self.user1, election=self.election_current)
        Vote.objects.create(account=self.user2, election=self.election_current)
        self.assertEqual(self.election_current.votes.count(), 2)

        self.election_current.disassociate_accounts()
        self.assertEqual(self.election_current.votes.count(), 2)
        self.assertFalse(self.election_current.has_voted(self.user1))
        self.assertFalse(self.election_current.has_voted(self.user2))

    def test_get_votes_with_points(self):
        self.election_current.allowed_voters.add(self.user1)
        ballot_plurality = self.create_current_pl_ballot(seats_available=6)
        pl_candidate1 = self.create_candidate(ballot_plurality)

        ballot_preferential = self.create_current_pr_ballot(seats_available=2)
        pr_candidate1 = self.create_candidate(ballot_preferential,
            last_name='AAA')
        pr_candidate2 = self.create_candidate(ballot_preferential,
            last_name='ZZZ')

        temp_vote1 = Vote.objects.create(
            account=self.user1,
            election=self.election_current)
        temp_votepl1 = VotePlurality.objects.create(
            vote=temp_vote1,
            candidate=pl_candidate1)
        temp_votepr1 = VotePreferential.objects.create(vote=temp_vote1,
            candidate=pr_candidate1, point=2)
        temp_votepr2 = VotePreferential.objects.create(vote=temp_vote1,
            candidate=pr_candidate2, point=3)

        votes_points = self.election_current.get_votes_with_points()
        self.assertEqual(len(votes_points), 1);
        self.assertEqual(votes_points[0][0], temp_vote1)
        self.assertEqual(votes_points[0][1], ['1', '2', '3']);


class BallotTestCase(BaseTestCase):
    "Tests for logic in the Ballot model that's common to both types"
    def test_has_incumbents_with_empty_ballot(self):
        ballot = self.create_current_pl_ballot()
        self.assertFalse(ballot.has_incumbents())

    def test_has_incumbents_with_ballot_not_having_incumbent_candidates(self):
        ballot = self.create_current_pl_ballot()
        candidate = self.create_candidate(ballot, incumbent=False)
        self.assertFalse(ballot.has_incumbents())

    def test_has_incumbents_with_ballot_having_incumbent_candidates(self):
        ballot = self.create_current_pl_ballot()
        candidate = self.create_candidate(ballot, incumbent=True)
        self.assertTrue(ballot.has_incumbents())


class PluralityBallotTestCase(BaseTestCase):
    "Tests for the Ballot model with type='Pl'"
    def test_unicode(self):
        ballot = Ballot(
            description="lorem ipsum",
            type="Pl",
            election=self.election_current,
        )
        self.assertEqual(unicode(ballot), "Plurality current: lorem ipsum")

    def test_get_candidate_stats(self):
        self.election_current.allowed_voters.add(self.user1, self.user2)

        ballot = self.create_current_pl_ballot(seats_available=6)
        pl_candidate1 = self.create_candidate(ballot)
        self.assertEqual(ballot.get_candidate_stats(), [(pl_candidate1, 0)])

        temp_vote1 = Vote.objects.create(
            account=self.user1,
            election=self.election_current)
        VotePlurality.objects.create(vote=temp_vote1, candidate=pl_candidate1)
        self.assertEqual(ballot.get_candidate_stats(), [(pl_candidate1, 1)])

        pl_candidate2 = self.create_candidate(ballot)
        self.assertEqual(ballot.get_candidate_stats(),
            [(pl_candidate1, 1), (pl_candidate2, 0)])

        temp_vote2 = Vote.objects.create(account=self.user2,
            election=self.election_current)
        VotePlurality.objects.create(vote=temp_vote2, candidate=pl_candidate1)
        self.assertEqual(ballot.get_candidate_stats(),
            [(pl_candidate1, 2), (pl_candidate2, 0)])


class PreferentialBallotTestCase(BaseTestCase):
    "Tests for the Ballot model with type='Pr'"
    def test_unicode(self):
        ballot = Ballot(
            description="dolor sit",
            type="Pr",
            election=self.election_current,
        )
        self.assertEqual(unicode(ballot), "Preferential current: dolor sit")

    def test_get_candidate_stats(self):
        ballot_preferential = self.create_current_pr_ballot(seats_available=2)
        pr_candidate1 = self.create_candidate(ballot_preferential)

        self.election_current.allowed_voters.add(self.user1, self.user2)
        self.assertEqual(ballot_preferential.get_candidate_stats(),
            [(pr_candidate1, 0)])

        temp_vote1 = Vote.objects.create(account=self.user1,
            election=self.election_current)
        VotePreferential.objects.create(vote=temp_vote1, point=2,
            candidate=pr_candidate1)
        self.assertEqual(ballot_preferential.get_candidate_stats(),
            [(pr_candidate1, 2)])

        pr_candidate2 = self.create_candidate(ballot_preferential)
        self.assertEqual(ballot_preferential.get_candidate_stats(),
            [(pr_candidate1, 2), (pr_candidate2, 0)])

        temp_vote2 = Vote.objects.create(account=self.user2,
            election=self.election_current)
        VotePreferential.objects.create(vote=temp_vote2, point=1,
            candidate=pr_candidate1)
        VotePreferential.objects.create(vote=temp_vote2, point=2,
            candidate=pr_candidate2)
        self.assertEqual(ballot_preferential.get_candidate_stats(),
            [(pr_candidate1, 3), (pr_candidate2, 2)])


class CandidateTestCase(BaseTestCase):
    "Tests for the Candidate model"
    def test_unicode_with_normal_candidate(self):
        candidate = Candidate(
            first_name="FOO",
            last_name="BAR",
            institution="FBAR",
            incumbent=True)
        self.assertEqual(unicode(candidate), "*FOO BAR (FBAR)")

    def test_unicode_with_writein(self):
        candidate = Candidate(
            first_name="LOREM",
            last_name="IPSUM",
            write_in=True,
            incumbent=False)
        self.assertEqual(unicode(candidate), "LOREM IPSUM (write-in)")

    def test_get_name(self):
        candidate = Candidate(
            first_name="FOO",
            last_name="BAR",
            institution="FBAR",
            incumbent=True)
        self.assertEqual(candidate.get_name(), "FOO BAR")


class VoteTestCase(BaseTestCase):
    "Tests for the Vote model"
    def test_user_not_allowed_error_handling(self):
        self.election_current.allowed_voters.add(self.user2)
        temp_vote1 = lambda: Vote.objects.create(account=self.user1,
            election=self.election_current)
        # shouldn't be allowed to save a vote for someone not in allowed_voters
        self.assertRaises(VotingNotAllowedException, temp_vote1)

    def test_get_details(self):
        ballot_plurality = self.create_current_pl_ballot(seats_available=6)
        pl_candidate1 = self.create_candidate(ballot_plurality)

        self.election_current.allowed_voters.add(self.user1)
        temp_vote1 = Vote.objects.create(account=self.user1,
            election=self.election_current)
        self.assertEqual(repr(temp_vote1.get_details()), repr(
            [(ballot_plurality, [])]))

        ballot_preferential = self.create_current_pr_ballot(seats_available=2)
        pr_candidate1 = self.create_candidate(ballot_preferential)
        pr_candidate2 = self.create_candidate(ballot_preferential)

        temp_votepl1 = VotePlurality.objects.create(vote=temp_vote1,
            candidate=pl_candidate1)
        self.assertEqual(repr(temp_vote1.get_details()), repr(
            [(ballot_plurality, [temp_votepl1]),
             (ballot_preferential, [])]))

        temp_votepr1 = VotePreferential.objects.create(vote=temp_vote1,
            candidate=pr_candidate1, point=2)
        temp_votepr2 = VotePreferential.objects.create(vote=temp_vote1,
            candidate=pr_candidate2, point=3)
        self.assertEqual(repr(temp_vote1.get_details()), repr(
            [(ballot_plurality, [temp_votepl1]),
             (ballot_preferential, [temp_votepr1, temp_votepr2])]))
