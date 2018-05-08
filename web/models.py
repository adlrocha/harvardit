from django.db import models

from django.contrib.auth.models import User


class Registrador(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return '%s' % (self.user)

class ProductType(models.Model):
    name = models.CharField(max_length=60)
    description = models.CharField(max_length=255)
    img_url = models.CharField(max_length=255)
    registrador = models.ForeignKey(Registrador, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return '%s - %s' % (self.name, self.description)