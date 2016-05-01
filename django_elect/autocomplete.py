from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.functions import Concat
from django.db.models import Value as V
from django.utils.decorators import method_decorator

from dal import autocomplete

from django_elect.models import Candidate


class CandidateAutocomplete(autocomplete.Select2QuerySetView):
    ballot_type = None

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(CandidateAutocomplete, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        if not self.ballot_type:
            raise "Ballot type not specified"

        qs = Candidate.objects.annotate(
            full_name=Concat('first_name', V(' '), 'last_name'),
        ).filter(ballot__type=self.ballot_type)

        election = self.forwarded.get('election', None)
        if election:
            qs = qs.filter(ballot__election=election)

        if self.q:
            qs = qs.filter(full_name__icontains=self.q)

        return qs
