
from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.root_view, name='root'),
    path('home', views.home_view, name='home'),
    path('register_user', views.register_user_view, name='register_user'),
    path('logout', views.logout_view, name='logout'),
    path('get_professors/<str:student_name>', views.get_professors_view, name='get_professors'),
    path('add_professors', views.add_professors_view, name='add_professors'),
    path('get_student_info/<str:student_name>', views.get_student_info_view, name='get_student_info'),
    path('add_grade', views.add_grade_view, name='add_grade'),
    path('send_thesis', views.send_thesis_view, name='send_thesis'),
    path('check_thesis/<str:student_name>/<str:doc_hash>', views.check_thesis_view, name='check_thesis'),
]
