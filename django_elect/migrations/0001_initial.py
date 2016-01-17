# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from django_elect import settings


class Migration(migrations.Migration):

    dependencies = settings.DJANGO_ELECT_MIGRATION_DEPENDENCIES

    operations = [
        migrations.CreateModel(
            name='Ballot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('position_number', models.PositiveSmallIntegerField(default=1, help_text=b'Change this if you want to customize the order in which ballots are shown for an election.')),
                ('description', models.CharField(max_length=255, blank=True)),
                ('introduction', models.TextField(help_text=b'If this field is non-empty, it will be shown below the ballot header on the voting page. Enter the text as HTML.', blank=True)),
                ('type', models.CharField(default=b'Pl', max_length=2, choices=[(b'Pl', b'Plurality'), (b'Pr', b'Preferential')])),
                ('seats_available', models.PositiveSmallIntegerField()),
                ('is_secret', models.BooleanField(default=False, help_text=b'Check this for a secret ballot. This means that only the fact that a voter voted will be recorded, not his or her choices.')),
                ('write_in_available', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['election', 'position_number', 'type', 'description'],
            },
        ),
        migrations.CreateModel(
            name='Candidate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('institution', models.CharField(max_length=255, blank=True)),
                ('incumbent', models.BooleanField(default=False)),
                ('image_url', models.URLField(max_length=255, blank=True)),
                ('write_in', models.BooleanField(default=False)),
                ('biography', models.TextField(help_text=b"Enter the candidate's biography here as HTML. It will be shown when the user clicks the candidate's name. If you leave this field blank, the candidate's name will not be a link.", blank=True)),
                ('ballot', models.ForeignKey(related_name='candidates', to='django_elect.Ballot')),
            ],
            options={
                'ordering': ['last_name', 'first_name'],
            },
        ),
        migrations.CreateModel(
            name='Election',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b"Used to uniquely identify elections. Will be shown with ' Election' appended to it on all publicly-visible pages.", unique=True, max_length=255)),
                ('introduction', models.TextField(help_text=b'This is printed at the top of the voting page below the header. Enter the text as HTML.', blank=True)),
                ('vote_start', models.DateTimeField(help_text=b'Start of voting')),
                ('vote_end', models.DateTimeField(help_text=b'End of voting')),
                ('allowed_voters', models.ManyToManyField(help_text=b'If empty, all registered users will be allowed to vote.', to=settings.DJANGO_ELECT_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ['vote_start'],
                'get_latest_by': 'vote_start',
            },
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('account', models.ForeignKey(to=settings.DJANGO_ELECT_USER_MODEL, null=True)),
                ('election', models.ForeignKey(related_name='votes', to='django_elect.Election')),
            ],
        ),
        migrations.CreateModel(
            name='VotePlurality',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('candidate', models.ForeignKey(to='django_elect.Candidate')),
                ('vote', models.ForeignKey(related_name='pluralities', to='django_elect.Vote', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='VotePreferential',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('point', models.PositiveSmallIntegerField()),
                ('candidate', models.ForeignKey(to='django_elect.Candidate')),
                ('vote', models.ForeignKey(related_name='preferentials', to='django_elect.Vote', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='ballot',
            name='election',
            field=models.ForeignKey(related_name='ballots', to='django_elect.Election'),
        ),
    ]
