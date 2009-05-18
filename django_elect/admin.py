from string import Template

from django.contrib import admin
from django.http import HttpResponseRedirect

from models import Election, Ballot, Vote, Candidate, \
    VotePreferential, VotePlurality
import settings


class BallotInline(admin.StackedInline):
    model = Ballot
    extra = 3

class ElectionAdmin(admin.ModelAdmin):
    actions = Template(u"""
        <a href="/election/statistics/$pk/">View Statistics</a> |
        <a href="/election/spreadsheet/$pk/">Generate Excel Spreadsheet</a> |
        <a href="/election/disassociate/$pk/">Disassociate Accounts</a>
    """)
    change_form_template = "admin/election_change_form.html"
    list_display = ('name', 'vote_start', 'vote_end', 'admin_actions')
    inlines = [BallotInline]

    def admin_actions(self, obj):
        return self.actions.substitute(pk = obj.pk)
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
