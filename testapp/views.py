from django.shortcuts import render

# Create your views here.
from django.views import View
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect



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
        posted_data = request.POST
        return render(request, self.template_name, {"countries":  self.countries,
            "user_types": self.user_types, "errors": errors, "posted_data": posted_data})


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

from django.contrib.auth.mixins import LoginRequiredMixin

class LoginRequiredView(View):
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            return HttpResponseRedirect('/login/')
        return super().dispatch(request, *args, **kwargs)



class DashboardView(LoginRequiredView):

    template_name = "dashboard.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


class LoginView(View):
    template_name = "index.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_anonymous:
            return HttpResponseRedirect('/home/')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.render_login_view(request)


    def render_login_view(self, request, errors=None):
        posted_data = request.POST
        return render(request, self.template_name, {
            "errors": errors, "posted_data": posted_data})


    def post(self, request, *args, **kwargs):
        data = request.POST
        email = data.get("username")
        password = data.get("password")
        user = authenticate(username=email, password=password)
        if not user:
            errors = {"email": [{"message": "Invalid credentials", "code": 1007}], 
                "password": [{"message": "Invalid credentials", "code": 1007}]}
            return self.render_login_view(request, errors)
        login(request, user)
        return HttpResponseRedirect('/home/')


class LogoutView(LoginRequiredView):
    

    def get(self, request, *args, **kwargs):
        logout(request)
        return HttpResponseRedirect('/login/')



