from django.contrib import admin
from django.http import HttpResponseRedirect

from models import Election, Ballot, Vote, Candidate, \
    VotePreferential, VotePlurality


class BallotInline(admin.StackedInline):
    model = Ballot
    extra = 3

class ElectionAdmin(admin.ModelAdmin):
    change_form_template = "admin/election_change_form.html"
    list_display = ('name', 'vote_start', 'vote_end')
    inlines = [BallotInline]

    def response_add(self, request, obj):
        # Overrides ModeAdmin.response_add() and redirects user to the ballot
        # page, filtered for the new Election
        msg = "The election '%s' was added successfully. " % unicode(obj)
        msg += """Please fill in the details for all the ballots listed
           below. Use the "Add Ballot" button to add additional ballots."""
        self.message_user(request, msg)
        url = "../../ballot/?election__id__exact=%i" % obj.pk
        return HttpResponseRedirect(url)

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
