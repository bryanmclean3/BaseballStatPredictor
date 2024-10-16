from django.db import models


class User(models.Model):
    sub = models.CharField(unique=True)
    name = models.CharField()
    email = models.CharField(unique=True)

