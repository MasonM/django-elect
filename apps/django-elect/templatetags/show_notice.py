from django import template

register = template.Library()

@register.inclusion_tag('django-elect/notice.html')
def show_notice(notice):
    """Shows a notice given by the string 'notice'"""
    return {'notice': notice}
