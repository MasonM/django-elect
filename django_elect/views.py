from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

from django_elect.models import Election, Vote
from django_elect.forms import PluralityVoteForm, PreferentialVoteForm
from django_elect import settings


def biographies(request):
    election = Election.get_latest_or_404()
    ballot_candidates = dict((b, b.candidates_with_biographies())
        for b in election.ballots.all() if b.candidates_with_biographies())
    return render_to_response('django_elect/biographies.html', {
        'election': election,
        'ballot_candidates': ballot_candidates.items(),
    })


@staff_member_required
@never_cache
def statistics(request, id):
    """
    Displays a table for each ballot with statistics for the candidates.
    """
    election = get_object_or_404(Election, pk=id)
    return render_to_response('django_elect/statistics.html', {
        'title': "Election Statistics",
        'election': election,
    })


@staff_member_required
def generate_spreadsheet(request, id):
    """
    Generates an Excel spreadsheet for review by a staff member.
    """
    election = get_object_or_404(Election, pk=id)
    response = render_to_response("django_elect/spreadsheet.html", {
        'full_stats': election.get_full_statistics(),
    })
    filename = "election%s.xls" % (election.pk)
    response['Content-Disposition'] = 'attachment; filename='+filename
    response['Content-Type'] = 'application/vnd.ms-excel; charset=utf-8'
    return response


@staff_member_required
def disassociate_accounts(request, id):
    """
    Disassociates accounts (i.e. sets account_ids to NULL) for all Vote
    objects. 'id' corresponds to the primary key of the Election objects.
    """
    election = get_object_or_404(Election, pk=id)
    success = False
    if request.POST and "confirm" in request.POST:
        election.disassociate_accounts()
        success = True
    return render_to_response("django_elect/disassociate.html", {
        "title": "Disassociate Accounts for Election %s" % election,
        "election": election,
        "success": success,
    }, context_instance=RequestContext(request))


@login_required
def vote(request):
    election = Election.get_latest_or_404()
    if not election.voting_allowed_for_user(request.user):
        # they aren't supposed to be on this page
        return HttpResponseRedirect(settings.LOGIN_URL)

    forms = []
    none_selected = False
    data = request.POST or None
    # fill forms list with Form objects, one for each ballot
    for b in election.ballots.all():
        prefix = "ballot%i" % (b.id)
        if b.type == "Pl":
            form = PluralityVoteForm(b, data=data, prefix=prefix)
        elif b.type == "Pr":
            form = PreferentialVoteForm(b, data=data, prefix=prefix)
        forms.append(form)

    if request.POST and all(x.is_valid() for x in forms):
        #all forms valid, so save unless no candidates were selected
        if any(f.has_candidates() for f in forms):
            vote = election.create_vote(request.user)
            for f in forms:
                f.save(vote)
            return HttpResponseRedirect(reverse("django_elect_success"))
        else:
            # they must not have selected any candidates, so show an error
            none_selected = True

    return render_to_response('django_elect/vote.html', {
        'current_tab': 'election',
        'account': request.user,
        'election': election,
        'forms': forms,
        'none_selected': none_selected,
    }, context_instance=RequestContext(request))


def success(request):
    return render_to_response('django_elect/success.html')
