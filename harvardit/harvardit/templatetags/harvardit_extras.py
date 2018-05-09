
from django import template

register = template.Library()

@register.filter
def is_student(user):
    return hasattr(user, 'student')

@register.filter
def is_professor(user):
    return hasattr(user, 'professor')

@register.filter
def is_university(user):
    return hasattr(user, 'university')