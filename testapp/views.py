from django.shortcuts import render

# Create your views here.
from django.views import View
from django.db import transaction

from .models import *


from django import forms

import json


class SignUpForm(forms.Form):
    first_name = forms.CharField(max_length=255, min_length=1)
    first_name = forms.CharField(max_length=255, min_length=1)
    user_type = forms.IntegerField()
    country = forms.IntegerField()
    phonenumber = forms.CharField()

    def clean_country(self):
        country = self.cleaned_data['country']
        if not Country.objects.filter(id=country).exists():
            raise forms.ValidationError('Invalid country', code=1000)
        return country

    def clean_user_type(self):
        user_type = self.cleaned_data['user_type']
        if not BusinessType.objects.filter(id=user_type).exists():
            raise forms.ValidationError('Invalid business type', code=1001)
        return user_type

    def clean_phonenumber(self):
        phonenumber = self.cleaned_data["phonenumber"]
        if User.objects.filter(phone_number=phonenumber).exists():
            raise forms.ValidationError('Phonenumber already used', code=1002)
        return phonenumber


    def save(self):
        import uuid
        company_data = {"name": str(uuid.uuid4()),
            "country_id": self.cleaned_data["country"], "phone_number": self.cleaned_data["phonenumber"]} 
        company_obj = Company.objects.create(**company_data)
        user_data = {"business_type_id": self.cleaned_data["user_type"], 
            "phone_number": self.cleaned_data["phonenumber"], "company": company_obj,
            "email": str(uuid.uuid4())+ "@gmail.com", "username": str(uuid.uuid4())}
        user_obj = User.objects.create(**user_data)
        return user_obj


class HomeView(View):

    template_name = "index.html"
    countries = Country.objects.all()
    user_types = BusinessType.objects.all()

    def get(self, request, *args, **kwargs):
        return self.render_home_view(request)

    
    def post(self, request, *args, **kwargs):
        data = {"first_name": "first" , "last_name": "Last", "user_type": 1, "country": 1, 
            "phonenumber": "998877665555"}
        form = SignUpForm(data=data)
        if form.is_valid():
            created, user_obj = self.create_user(request, form)
            if created:
                return self.render_home_view(request)
            else:
                return self.render_home_view(request, "something happened")
        errors_json = json.loads(form.errors.as_json())
        return self.render_home_view(request, errors_json)

    def render_home_view(self, request, errors=None):
        return render(request, self.template_name, {"countries":  self.countries,
            "user_types": self.user_types, "errors": errors})


    @transaction.atomic
    def create_user(self, request, form):
        roll_back_point = transaction.savepoint()
        try:
            user_obj = form.save()
            transaction.savepoint_commit(roll_back_point)
            return True, user_obj 
        except Exception as e:
            transaction.savepoint_rollback(roll_back_point) 
            return False , {}

