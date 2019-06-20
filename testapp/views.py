from django.shortcuts import render

# Create your views here.
from django.views import View
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.http import HttpResponse




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

class AnonymousView(View):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_anonymous:
            return HttpResponseRedirect('/home/')
        return super().dispatch(request, *args, **kwargs)




class DashboardView(LoginRequiredView):

    template_name = "dashboard.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


class LoginView(AnonymousView):
    template_name = "index.html"

    

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


from django.contrib.auth.tokens import default_token_generator
from django.core.validators import RegexValidator



class SecretDetailsForm(forms.Form):
    

    secret_question = forms.CharField(max_length=255, min_length=1)
    secret_answer = forms.CharField(max_length=255, min_length=1)
    

class SecretDetailsWithPasswordForm(SecretDetailsForm):
    password = forms.CharField(max_length=255, min_length=1, 
        validators=[RegexValidator('^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W)', 
            message="Password should be a combination of Alphabets and Numbers")])


class SetPasswordForm(forms.Form):
    password = forms.CharField(max_length=255, min_length=1, 
        validators=[RegexValidator('^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*\W)', 
            message="Password should be a combination of Alphabets and Numbers")])




class UserTokenProtectedView(View):

    def dispatch(self, request, *args, **kwargs):
        is_token_valid = self.validate_token(request, kwargs.get("user_id"),
            kwargs.get("token"))
        if not is_token_valid:
            return HttpResponse("Invalid link")
        return super().dispatch(request, *args, **kwargs)

    def validate_token(self, request, user_id, token):
        try:
            user_obj = User.objects.get(id=user_id)
            is_token_valid = default_token_generator.check_token(user_obj, token)
            self.user = user_obj
            return is_token_valid
        except User.DoesNotExist:
            return False



class SetPasswordAndSecretDetails(UserTokenProtectedView):
    template_name = "secret.html"
    user = None
    form = SecretDetailsWithPasswordForm

    def get(self, request, *args, **kwargs):
        return self.render_secret_view(request)

    def post(self, request, *args, **kwargs):
        form = self.form(data=request.POST)
        if form.is_valid():
            user_obj = self.user
            user_obj.secret_question = form.cleaned_data["secret_question"]
            user_obj.secret_answer = form.cleaned_data["secret_answer"]
            user_obj.set_password(form.cleaned_data["password"])
            user_obj.save()
            return self.render_secret_view(request, None, "Updated user details")
        errors_json = json.loads(form.errors.as_json())
        return self.render_secret_view(request, errors_json)

    def render_secret_view(self, request, errors=None, success=None):
        posted_data = request.POST
        return render(request, self.template_name, {"errors": errors,
            "posted_data": posted_data, "path": request.path,
            "success": success})


def send_forgot_password_notification(user):
    to_address = user.email
    link = user.generate_reset_password_link()
    message = render_to_string('forgot_password_email_template.html', 
        {"full_name": user.full_name, "link": link})
    subject = "Restpassword"
    email_from = settings.FROM_ADDRESS
    email_queue_data = {"from_address": email_from, "to_address": to_address,
                        "subject": subject, "content": message,
                        "email_type": 1}
    EmailQueue.objects.create(**email_queue_data)


class ForgotPasswordView(AnonymousView):

    template_name = "forgot_password.html"

    def get(self, request, *args, **kwargs):
        return self.render_forgot_password_view(request)

    def post(self, request, *args, **kwargs):
        data = request.POST
        email = data.get("email")
        user_obj, errors = User.get_user_using_email(email)
        if errors:
            return self.render_forgot_password_view(request, errors)
        send_forgot_password_notification(user_obj)
        return HttpResponseRedirect('/login/')

    def render_forgot_password_view(self, request, errors=None):
        posted_data = request.POST
        return render(request, self.template_name, {"errors": errors,
            "posted_data": posted_data})


class ResetPasswordStep1View(UserTokenProtectedView):

    template_name = "reset_password_step_1.html"
    form = SecretDetailsForm

    def get(self, request, *args, **kwargs):
        return self.render_reset_password_view(request)


    def post(self, request, *args, **kwargs):
        form = self.form(data=request.POST)
        if not form.is_valid():
            errors_json = json.loads(form.errors.as_json())
            return self.render_reset_password_view(request, errors_json)
        if not (self.user.secret_question == form.cleaned_data["secret_question"] and 
            self.user.secret_answer == form.cleaned_data["secret_answer"]):
            errors = {"secret_question": [{"message": "Incorrect secret details", "code": 1007}], 
                "secret_answer": [{"message": "Incorrect secret details", "code": 1007}]}
            return self.render_reset_password_view(request, errors_json)
        current_path = request.path
        reset_password_step_2_link = current_path.replace('reset_password_step1', 'reset_password_step2')
        self.user.question_verified = True
        self.user.save()
        return HttpResponseRedirect(reset_password_step_2_link)

    def render_reset_password_view(self, request, errors=None):
        posted_data = request.POST
        return render(request, self.template_name, {"errors": errors,
            "posted_data": posted_data, "path": request.path})


class ResetPasswordStep2View(UserTokenProtectedView):

    template_name = "reset_password_step_2.html"
    form = SetPasswordForm

    def get(self, request, *args, **kwargs):
        if not self.user.question_verified:
            current_path = request.path
            reset_password_step_1_link = current_path.replace('reset_password_step2',
                'reset_password_step1')
            return HttpResponseRedirect(reset_password_step_1_link)
        return self.render_reset_password_view(request)


    def post(self, request, *args, **kwargs):
        form = self.form(data=request.POST)
        if not form.is_valid():
            errors_json = json.loads(form.errors.as_json())
            return self.render_reset_password_view(request, errors_json)
        self.user.question_verified = False
        self.user.set_password(form.cleaned_data["password"])
        self.user.save()
        return HttpResponseRedirect('/login/')

    def render_reset_password_view(self, request, errors=None):
        posted_data = request.POST
        return render(request, self.template_name, {"errors": errors,
            "posted_data": posted_data, "path": request.path})


