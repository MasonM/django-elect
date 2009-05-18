from string import Template

from django import forms
from django.utils.http import urlquote
from django.utils.safestring import mark_safe

from models import Candidate, VotePlurality, VotePreferential
import settings


class CandidateRowWidget(forms.Select):
    """
    Form widget for showing a table row with information on a single candidate.
    """
    template = Template(u"""
      <tr class="candidate-row">
        <td>$select</td>
        <td>$incum$name</td>
        <td>$inst</td>
        <td><img src="$image" alt="Photograph"/></td>
      </tr>
    """)

    def __init__(self, candidate, form_widget, *args, **kwargs):
        """
        "candidate" is the Candidate to show, and "form_widget" is the form
        input to show next to the candidate's name
        """
        super(CandidateRowWidget, self).__init__(*args, **kwargs)
        self.candidate = candidate
        self.form_widget = form_widget

    def render(self, name, value, attrs=None, choices=()):
        candidate_name = self.candidate.get_name()
        if self.candidate.biography:
            # make candidate's name a link to the appropriate anchor
            # on the auto-generated biographies page
            link = "/election/biographies/#" + urlquote(candidate_name)
            candidate_name = '<a href="%s">%s</a>' % (link, candidate_name)
        select = self.form_widget.render(name, value)
        photo_unavailable = settings.DJANGO_ELECT_MEDIA_ROOT + \
                            "/img/photo_unavailable.gif"
        return mark_safe(self.template.substitute({
            'select': select,
            'incum': self.candidate.incumbent and "*" or "",
            'name': candidate_name,
            'inst': self.candidate.institution or "N/A",
            'image': self.candidate.image_url or photo_unavailable,
        }))


class BaseVoteForm(forms.Form):
    """
    Base class for representing the form for a single ballot
    """
    ballot = None
    candidate_list = None

    def __init__(self, ballot, *args, **kwargs):
        super(BaseVoteForm, self).__init__(*args, **kwargs)
        self.ballot = ballot

    def has_candidates(self):
        """
        Returns True if this form is valid and contains at least one candidate
        """
        return self.is_valid() and len(self.candidate_list) >= 1

    def save(self, vote):
        """
        Creates appropriate objects for each candidate choice, then
        associates them with the given vote object.
        """
        raise NotImplementedError

    def get_write_in_candidate(self, write_in):
        """
        Returns write-in candidate corresponding to given dictionary if this
        ballot has been marked to accept write-in candidates, else returns None
        """
        if not self.ballot.write_in_available or not write_in:
            return None
        return Candidate.objects.get_or_create(ballot=self.ballot,
            write_in=True, first_name=write_in['first_name'],
            last_name=write_in['last_name'], incumbent=False)[0]


class WriteInField(forms.MultiValueField):
    """
    Represents the write-in candidate field for a general ballot.
    Must be passed the appropriate widget.
    """
    def __init__(self, widget, fields=(), *args, **kwargs):
        fields += (
            forms.CharField(label="First Name", min_length=1, max_length=45),
            forms.CharField(label="Last Name", min_length=1, max_length=45),
        )
        self.widget = widget(widgets=[f.widget for f in fields])
        super(WriteInField, self).__init__(fields, *args, **kwargs)
        self.required = False

    def compress(self, data_list):
        if data_list:
            return {'first_name': data_list[0], 'last_name': data_list[1]}
        return None

    def clean(self, value):
        name = super(WriteInField, self).clean(value)
        if name and ((name['first_name'] and not name['last_name']) or
           (not name['first_name'] and name['last_name'])):
            message = "Please enter in both the first and last name for "+\
                      "write-in candidates."
            raise forms.ValidationError(message)
        return name


class PluralityVoteForm(BaseVoteForm):
    """
    Extends BaseVoteForm to implement the vote form for plurality ballots.
    """
    def __init__(self, *args, **kwargs):
        super(PluralityVoteForm, self).__init__(*args, **kwargs)
        candidates = self.ballot.candidates.filter(write_in=False)
        select = forms.CheckboxInput()
        for candidate in candidates:
            self.fields[candidate.pk] = forms.BooleanField(label="",
                widget=CandidateRowWidget(candidate, select),
                required=False)
        if self.ballot.write_in_available:
            self.fields['write_in'] = WriteInField(widget=self.WriteInWidget)

    class WriteInWidget(forms.MultiWidget):
        """
        Widget representing the "write-in" choice on a plurality ballot.
        """
        def decompress(self, value):
            if value:
                return (value['first_name'], value['last_name'])
            else:
                return (None, None, None)

        def format_output(self, rendered_widgets):
            return mark_safe(u"""
                <tr>
                    <th colspan="2">&nbsp;</th>
                    <th>First Name</th>
                    <th>Last Name</th>
                </tr>
                <tr>
                    <td colspan="2">Write in:</td>
                    <td>%s</td>
                    <td>%s</td>
                </tr>""" % tuple(rendered_widgets))

    def clean(self):
        clean = super(PluralityVoteForm, self).clean()
        candidates = [cand for cand, selected in clean.items()
                      if selected and isinstance(cand, long)]
        self.candidate_list = Candidate.objects.in_bulk(candidates).values()
        seats = self.ballot.seats_available
        write_in = clean.get('write_in')
        if (len(self.candidate_list) + (1 if write_in else 0)) > seats:
            message = 'Please select %i or fewer candidates.' % (seats)
            raise forms.ValidationError(message)

        if write_in:
            self.candidate_list.append(self.get_write_in_candidate(write_in))
        return clean

    def save(self, vote):
        for candidate in self.candidate_list:
            if candidate.write_in:
                candidate.save()
            VotePlurality(vote=vote, candidate=candidate).save()


class PreferentialVoteForm(BaseVoteForm):
    """
    Extends BaseVoteForm to implement the vote form for preferential ballots.
    """
    def __init__(self, *args, **kwargs):
        super(PreferentialVoteForm, self).__init__(*args, **kwargs)
        candidates = self.ballot.candidates.filter(write_in=False)
        #we use the Borda count method for preferential ballots, so each
        #candidate select box should have options in the format
        #[(0, 0), (1, 3), (2, 2), (3, 1)]
        point_options = [(0, 0)]
        points = range(1, candidates.count() + 1)
        point_options += zip(points[::-1], points)
        widget = forms.Select(choices=point_options,
                              attrs={'style': 'width: 40px'})
        for candidate in candidates:
            self.fields[candidate.pk] = forms.ChoiceField(label="",
                choices=point_options,
                widget=CandidateRowWidget(candidate, widget))
        if self.ballot.write_in_available:
            self.fields['write_in'] = PreferentialWriteInField(
                choices=point_options)

    def clean(self):
        clean = super(PreferentialVoteForm, self).clean()
        write_in = clean.pop('write_in', False)
        point_list = [int(i) for i in clean.values() if int(i) > 0]
        if write_in and write_in['points'] > 0:
            point_list.append(write_in['points'])
        message = ""
        # check that no point value exceeds the number of candidates
        candidates = self.ballot.candidates.filter(write_in=False)
        num = candidates.count()
        if point_list and filter(lambda x: x > num, point_list):
            message = "Please rank your preferences from 1 to %i." % num
        # check that there are no duplicate points
        elif len(set(point_list)) != len(point_list) and sum(point_list) > 0:
            message = "Please do not give the same point value to "+\
                      "more than one candidate."
        if message:
            raise forms.ValidationError(message)
        self.candidate_list = [(candidates.get(id=c), int(p))
                               for c, p in clean.items() if int(p) > 0]
        if write_in:
            candidate = self.get_write_in_candidate(write_in)
            self.candidate_list.append((candidate, write_in['points']))
        return clean

    def save(self, vote):
        for candidate, points in self.candidate_list:
            VotePreferential(vote=vote, candidate=candidate,
                             point=points).save()


class PreferentialWriteInField(WriteInField):
    """
    WriteInField with an additional ChoiceField.
    """
    def __init__(self, choices, *args, **kwargs):
        fields = (
            forms.ChoiceField(choices=choices),
        )
        super(PreferentialWriteInField, self).__init__(
            fields=fields, widget=self.WriteInWidget, *args, **kwargs
        )

    def compress(self, data_list):
        # make sure something was filled in for name
        if data_list and (data_list[1] or data_list[2]):
            return {'points': int(data_list[0]),
                    'first_name': data_list[1],
                    'last_name': data_list[2]}
        return None

    def clean(self, value):
        write_in = super(PreferentialWriteInField, self).clean(value)
        if write_in and write_in['first_name'] and write_in['last_name'] and \
           (write_in['points'] == 0):
            message = "Please select a non-zero point value for the write-in"+\
                      " candidate you entered."
            raise forms.ValidationError(message)
        return write_in

    class WriteInWidget(forms.MultiWidget):
        """
        Widget representing the "write-in" choice on a preferential ballot.
        """
        def decompress(self, value):
            if value:
                return (value['points'], value['first_name'],
                        value['last_name'])
            else:
                return (None, None, None)

        def format_output(self, rendered_widgets):
            return mark_safe(u"""
                <tr>
                    <th colspan="2">&nbsp;</th>
                    <th>First Name</th>
                    <th>Last Name</th>
                </tr>
                <tr>
                    <td>%s</td>
                    <td>Write in:</td>
                    <td>%s</td>
                    <td>%s</td>
                </tr>""" % tuple(rendered_widgets))
