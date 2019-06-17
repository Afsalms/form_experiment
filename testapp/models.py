from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.

class Country(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=255, unique=True)
    country = models.ForeignKey('Country', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class BusinessType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=50, unique=True)
    business_type = models.ForeignKey('BusinessType', on_delete=models.CASCADE)
