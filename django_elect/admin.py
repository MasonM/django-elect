from django.core.urlresolvers import reverse
from django.contrib import admin
from django.http import HttpResponseRedirect

from django_elect.models import Election, Ballot, Vote, Candidate, \
    VotePreferential, VotePlurality
from django_elect import settings


class BallotInline(admin.StackedInline):
    model = Ballot
    extra = 3

class ElectionAdmin(admin.ModelAdmin):
    actions_html = """
        <a href="%s">View Statistics</a> |
        <a href="%s">Generate Excel Spreadsheet</a> |
        <a href="%s">Disassociate Accounts</a>
    """
    change_form_template = "admin/election_change_form.html"
    list_display = ('name', 'vote_start', 'vote_end', 'admin_actions')
    filter_horizontal = ("allowed_voters",)
    inlines = [BallotInline]

    def admin_actions(self, obj):
        kwargs = {'id': str(obj.pk)}
        return self.actions_html % (
            reverse('django_elect_stats', kwargs=kwargs),
            reverse('django_elect_spreadsheet', kwargs=kwargs),
            reverse('django_elect_disassociate', kwargs=kwargs),
        )
    admin_actions.short_description = "Administrative Actions"
    admin_actions.allow_tags = True

    def response_add(self, request, obj):
        # Overrides ModeAdmin.response_add() and redirects user to the ballot
        # page, filtered for the new Election
        msg = "The election '%s' was added successfully. " % unicode(obj)
        msg += """Please fill in the details for all the ballots listed
           below. Use the "Add Ballot" button to add additional ballots."""
        self.message_user(request, msg)
        url = "../../ballot/?election__id__exact=%i" % obj.pk
        return HttpResponseRedirect(url)

    class Media:
        js = [settings.DJANGO_ELECT_MEDIA_ROOT+"/js/jquery-1.3.2.min.js"]
admin.site.register(Election, ElectionAdmin)


class CandidateInline(admin.StackedInline):
    model = Candidate
    extra = 5

class BallotAdmin(admin.ModelAdmin):
    list_display = ("election", "description", "type")
    inlines = [CandidateInline]
admin.site.register(Ballot, BallotAdmin)


class VotePreferentialInline(admin.TabularInline):
    model = VotePreferential

class VotePluralityInline(admin.TabularInline):
    model = VotePlurality

class VoteAdmin(admin.ModelAdmin):
    list_display = ('election', 'account')
    search_fields = ['account__first_name', 'account__last_name']
    inlines = [VotePreferentialInline, VotePluralityInline]
admin.site.register(Vote, VoteAdmin)
