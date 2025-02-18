from django import template
from django.template.defaultfilters import stringfilter
from web.markdown_utils import process_markdown

register = template.Library()

@register.filter()
@stringfilter
def quizz_markdown(value, quizz_src):
    if value:
        return process_markdown(quizz_src, value, 'quizz')
    return ""
