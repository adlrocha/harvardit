from django.db import models

from django.contrib.auth.models import User

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    sc_tx = models.CharField(max_length=66)
    sc_address = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return '%s' % (self.user)

class Professor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    students = models.ManyToManyField(Student, blank=True)
    eth_address = models.CharField(max_length=50)

    def __str__(self):
        return '%s' % (self.user)

class University(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    eth_address = models.CharField(max_length=50)

    def __str__(self):
        return '%s' % (self.user)

