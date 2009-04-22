from django import template
from django.template.loader import render_to_string

register = template.Library()

@register.tag(name="show_errors")
def show_errors(parser, token):
    """Shows error messages for all fields in the given forms"""
    try:
        forms = token.split_contents()[1:]
    except:
        raise template.TemplateSyntaxError, \
              "show_errors tag requires at least one argument"
    return ShowErrorsNode(forms)

class ShowErrorsNode(template.Node):
    def __init__(self, forms):
        self.forms = forms

    def render(self, context):
        # store # of errors in context variable so we can sequentially order
        if "errorNum" not in context:
            context['errorNum'] = 0
        error_id = context['errorNum']
        context['errorNum'] += 1
        forms = map(lambda f: template.resolve_variable(f, context), self.forms)
        try:
            error_dicts = map(lambda f: f.errors, forms)
        except:
            raise template.TemplateSyntaxError, \
                  "show_errors arguments must be forms"
        #merge list of dicts into a list of tuples 
        errors = reduce(lambda a,b: a+b, map(lambda a: a.items(), error_dicts))
        #convert keys to human-readable form, e.g. "first_name" => "First Name"
        errors = map(lambda x: (str(x[0]).replace("_", " ").title(), 
                     x[1]), errors)
        return render_to_string('errors.html', {
            'error_dict': errors,
            "id": error_id,
        })
