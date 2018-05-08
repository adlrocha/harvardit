
from django import template

register = template.Library()

@register.filter
def is_registrador(user):
	return hasattr(user, 'registrador')