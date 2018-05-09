from django.contrib import admin

from .models import Student, Professor, University

admin.site.register(Student)
admin.site.register(Professor)
admin.site.register(University)