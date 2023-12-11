from django.db import models


class Customers(models.Model):
    username = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    address = models.TextField()
    birthdate = models.DateTimeField()
    email = models.EmailField()
    accounts = models.JSONField()
    tier_and_details = models.JSONField()

