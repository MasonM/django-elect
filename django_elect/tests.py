import unittest
from datetime import date, timedelta

from django.contrib.auth.models import User

from models import Ballot, Candidate, Election, Vote, VotePlurality,\
    VotePreferential


class ModelTestCase(unittest.TestCase):
    "Tests for the election models"

    def setUp(self):
        self.suiseiseki = User.objects.create(email="desu@desu.de",
            username="desu", first_name="Jade", last_name="Stern",
            password="DESU")
        self.shinku = User.objects.create(email="shinku@inbox.com",
            username="shinku", first_name="Reiner", last_name="Rubin",
            password="DAWA")

        week_ago = date.today() - timedelta(7)
        next_week = date.today() + timedelta(7)
        tomorrow = date.today() + timedelta(1)
        yesterday = date.today() - timedelta(1)
        self.election_current = Election.objects.create(name="current",
            introduction="Intro1", vote_start=week_ago, vote_end=tomorrow)
        self.election_finished = Election.objects.create(name="finished",
            vote_start=week_ago, vote_end=yesterday)
        self.election_future = Election.objects.create(name="future",
            vote_start=tomorrow, vote_end=next_week)

    def tearDown(self):
        self.suiseiseki.delete()
        self.shinku.delete()
        self.election_current.delete()
        self.election_finished.delete()
        self.election_future.delete()

    def test_election_model(self):
        # test __unicode__ and voting_allowed() methods
        self.assertEqual(unicode(self.election_current), u"current")
        self.assertTrue(self.election_current.voting_allowed())

        self.assertEqual(unicode(self.election_finished), u"finished")
        self.assertFalse(self.election_finished.voting_allowed())

        self.assertEqual(unicode(self.election_future), u"future")
        self.assertFalse(self.election_future.voting_allowed())

        # test has_voted() method
        self.assertFalse(self.election_current.has_voted(self.suiseiseki))
        Vote.objects.create(account=self.suiseiseki,
            election=self.election_current)
        self.assertTrue(self.election_current.has_voted(self.suiseiseki))
        self.assertFalse(self.election_finished.has_voted(self.suiseiseki))
        self.assertFalse(self.election_current.has_voted(self.shinku))
        Vote.objects.create(account=self.shinku, election=self.election_future)
        self.assertTrue(self.election_future.has_voted(self.shinku))
        self.assertFalse(self.election_future.has_voted(self.suiseiseki))
        Vote.objects.create(account=self.suiseiseki,
            election=self.election_future)
        self.assertTrue(self.election_future.has_voted(self.suiseiseki))

        # test disassociate_accounts() method
        self.assertEqual(self.election_future.votes.count(), 2)
        self.election_future.disassociate_accounts()
        self.assertEqual(self.election_future.votes.count(), 2)
        self.assertFalse(self.election_future.has_voted(self.suiseiseki))
        self.assertFalse(self.election_future.has_voted(self.shinku))

    def test_ballot_model(self):
        # test __unicode__ and has_incumbents()
        ballot_plurality = Ballot.objects.create(description="Best Doll",
            election=self.election_current, type="Pl", seats_available=6)
        self.assertEqual(unicode(ballot_plurality),
            "Plurality current: Best Doll")
        ballot_preferential = Ballot.objects.create(description="DESU",
            election=self.election_current, type="Pr", seats_available=2)
        self.assertEqual(unicode(ballot_preferential),
            "Preferential current: DESU")

        pl_candidate1 = Candidate.objects.create(ballot=ballot_plurality,
            first_name="Jade", last_name="Stern", incumbent=True)
        self.assertTrue(ballot_plurality.has_incumbents())
        self.assertFalse(ballot_preferential.has_incumbents())
        pr_candidate1 = Candidate.objects.create(ballot=ballot_preferential,
            first_name="Mercury", last_name="Lampe", incumbent=False)
        self.assertFalse(ballot_preferential.has_incumbents())

        # test get_candidate_stats() with a plurality ballot
        self.assertEqual(ballot_plurality.get_candidate_stats(),
            [(pl_candidate1, 0)])
        temp_vote1 = Vote.objects.create(account=self.suiseiseki,
            election=self.election_current)
        VotePlurality.objects.create(vote=temp_vote1, candidate=pl_candidate1)
        self.assertEqual(ballot_plurality.get_candidate_stats(),
            [(pl_candidate1, 1)])
        pl_candidate2 = Candidate.objects.create(ballot=ballot_plurality,
            first_name="Reiner", last_name="Rubin", incumbent=False)
        self.assertEqual(ballot_plurality.get_candidate_stats(),
            [(pl_candidate1, 1), (pl_candidate2, 0)])
        temp_vote2 = Vote.objects.create(account=self.shinku,
            election=self.election_current)
        VotePlurality.objects.create(vote=temp_vote2, candidate=pl_candidate1)
        self.assertEqual(ballot_plurality.get_candidate_stats(),
            [(pl_candidate1, 2), (pl_candidate2, 0)])

        # test get_candidate_stats with a preferential ballot
        self.assertEqual(ballot_preferential.get_candidate_stats(),
            [(pr_candidate1, 0)])
        temp_vote1 = Vote.objects.create(account=self.suiseiseki,
            election=self.election_current)
        VotePreferential.objects.create(vote=temp_vote1, point=2,
            candidate=pr_candidate1)
        self.assertEqual(ballot_preferential.get_candidate_stats(),
            [(pr_candidate1, 2)])
        pr_candidate2 = Candidate.objects.create(ballot=ballot_preferential,
            first_name="Reiner", last_name="Rubin", incumbent=False)
        self.assertEqual(ballot_preferential.get_candidate_stats(),
            [(pr_candidate1, 2), (pr_candidate2, 0)])
        temp_vote2 = Vote.objects.create(account=self.shinku,
            election=self.election_current)
        VotePreferential.objects.create(vote=temp_vote2, point=1,
            candidate=pr_candidate1)
        VotePreferential.objects.create(vote=temp_vote2, point=2,
            candidate=pr_candidate2)
        self.assertEqual(ballot_preferential.get_candidate_stats(),
            [(pr_candidate1, 3), (pr_candidate2, 2)])

    def test_candidate_model(self):
        # test __unicode__ and get_name() methods
        ballot = Ballot.objects.create(description="DESU",
            election=self.election_current, type="Pl", seats_available=1)
        candidate1 = Candidate.objects.create(ballot=ballot, first_name="Jade",
            last_name="Stern", institution="N-Field", incumbent=True)
        self.assertEqual(unicode(candidate1), "*Jade Stern (N-Field)")
        self.assertEqual(candidate1.get_name(), "Jade Stern")
        candidate2 = Candidate.objects.create(ballot=ballot, first_name="Hina",
            last_name="Ichigo", write_in=True, incumbent=False)
        self.assertEqual(unicode(candidate2), "Hina Ichigo (write-in)")
        self.assertEqual(candidate2.get_name(), "Hina Ichigo")

    def test_vote_model(self):
        # test get_details() method
        ballot_plurality = Ballot.objects.create(description="Best Doll",
            election=self.election_current, type="Pl", seats_available=6)
        pl_candidate1 = Candidate.objects.create(ballot=ballot_plurality,
            first_name="Jade", last_name="Stern", incumbent=True)

        temp_vote1 = Vote.objects.create(election=self.election_current,
            account=self.suiseiseki)
        self.assertEqual(repr(temp_vote1.get_details()), repr(
            [(ballot_plurality, [])]))
        ballot_preferential = Ballot.objects.create(description="DESU",
            election=self.election_current, type="Pr", seats_available=2)
        temp_votepl1 = VotePlurality.objects.create(vote=temp_vote1,
            candidate=pl_candidate1)
        self.assertEqual(repr(temp_vote1.get_details()), repr(
            [(ballot_plurality, [temp_votepl1]),
             (ballot_preferential, [])]))

        pr_candidate1 = Candidate.objects.create(ballot=ballot_preferential,
            first_name="Mercury", last_name="Lampe", incumbent=False)
        pr_candidate2 = Candidate.objects.create(ballot=ballot_preferential,
            first_name="Reiner", last_name="Rubin", incumbent=False)
        temp_votepr1 = VotePreferential.objects.create(vote=temp_vote1,
            candidate=pr_candidate1, point=2)
        temp_votepr2 = VotePreferential.objects.create(vote=temp_vote1,
            candidate=pr_candidate2, point=3)
        self.assertEqual(repr(temp_vote1.get_details()), repr(
            [(ballot_plurality, [temp_votepl1]),
             (ballot_preferential, [temp_votepr1, temp_votepr2])]))

        # test get_points_for_candidates method
        cand_list = [pl_candidate1]
        self.assertEqual(temp_vote1.get_points_for_candidates(cand_list), [1])
        cand_list = [pl_candidate1, pr_candidate1, pr_candidate2]
        self.assertEqual(temp_vote1.get_points_for_candidates(cand_list),
            [1, 2, 3])
        cand_list = [pr_candidate2, pr_candidate1]
        self.assertEqual(temp_vote1.get_points_for_candidates(cand_list),
            [3, 2])
