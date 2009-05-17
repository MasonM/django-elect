from django.contrib import admin

from models import Election, Ballot, Vote, Candidate, \
    VotePreferential, VotePlurality


class BallotInline(admin.StackedInline):
    model = Ballot
    extra = 2

class ElectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'vote_start', 'vote_end')
    inlines = [BallotInline]
admin.site.register(Election, ElectionAdmin)


class CandidateInline(admin.StackedInline):
    model = Candidate
    extra = 5

class BallotAdmin(admin.ModelAdmin):
    list_display = ("election", "description", "type")
    inlines= [CandidateInline]
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
