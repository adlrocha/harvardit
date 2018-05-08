from django.urls import reverse
from django.http import HttpResponseRedirect

def registrador_only(function):
    def wrap(request, *args, **kwargs):

        if hasattr(request.user, 'registrador'):
            return function(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('root'))
    wrap.__doc__=function.__doc__
    wrap.__name__=function.__name__
    return wrap