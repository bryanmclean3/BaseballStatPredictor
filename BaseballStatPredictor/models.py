from django.db import models


# database model for users
class User(models.Model):
    sub = models.CharField(unique=True)
    name = models.CharField()
    email = models.CharField(unique=True)


# database model for predicting head-to-head winners
class HeadToHead(models.Model):
    date = models.DateField()
    game_id = models.IntegerField()
    team = models.CharField()


# database model for predicting player Stats
class PlayerStats(models.Model):
    date = models.DateField()
    name = models.CharField()
    opponent = models.CharField()
    runs = models.IntegerField(blank=True, null=True)
    hits = models.IntegerField(blank=True, null=True)
    doubles = models.IntegerField(blank=True, null=True)
    triples = models.IntegerField(blank=True, null=True)
    home_runs = models.IntegerField(blank=True, null=True)
    rbis = models.IntegerField(blank=True, null=True)
    walks = models.IntegerField(blank=True, null=True)
    strike_outs = models.IntegerField(blank=True, null=True)
    innings_pitched = models.IntegerField(blank=True, null=True)
    hits_allowed = models.IntegerField(blank=True, null=True)
    runs_allowed = models.IntegerField(blank=True, null=True)
    earned_runs = models.IntegerField(blank=True, null=True)
    home_runs_allowed = models.IntegerField(blank=True, null=True)
    pitches_thrown = models.IntegerField(blank=True, null=True)
