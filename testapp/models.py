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


from django.contrib.auth.tokens import default_token_generator
from django.dispatch import receiver
from django.db.models import signals
from django.conf import settings
from django.template.loader import render_to_string



def send_verified_account_notification(user):
    to_address = user.email
    link = user.generate_complete_registation_link()
    message = render_to_string('registration_complete_email_template.html', 
        {"full_name": user.full_name, "link": link})
    subject = "Registration Completed"
    email_from = settings.FROM_ADDRESS
    email_queue_data = {"from_address": email_from, "to_address": to_address,
                        "subject": subject, "content": message,
                        "email_type": 0}
    EmailQueue.objects.create(**email_queue_data)


class User(AbstractUser):
    company = models.ForeignKey('Company', on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=50, unique=True)
    business_type = models.ForeignKey('BusinessType', on_delete=models.CASCADE)
    secret_question = models.CharField(max_length=50, null=True, blank=True)
    secret_answer = models.CharField(max_length=50, null=True, blank=True)
    status = models.IntegerField(default=0)

    @property
    def full_name(self):
        full_name = ""
        if self.first_name:
            full_name += self.first_name
        if self.last_name:
            full_name += " " + self.last_name
        return full_name


    def generate_token(self):
        token = default_token_generator.make_token(self)
        return token

    def validate_token(self, token):
        is_valid = default_token_generator.check_token(self, token)
        return is_valid

    def generate_complete_registation_link(self):
        link = settings.BASE_URL + "/{}/{}/complete_registration/".format(
            self.id, self.generate_token())
        return link


@receiver(signals.pre_save, sender=User)
def user_presave_trigger(sender, instance, *args, **kwargs):
    if instance.id:
        user_obj = User.objects.get(id=instance.id)
        setattr(instance, "status_before_save", user_obj.status)
    else:
        setattr(instance, "status_before_save", None)


@receiver(signals.post_save, sender=User)
def user_postsave_trigger(sender, instance, created, **kwargs):
    status_before_save = getattr(instance, "status_before_save")
    current_status = instance.status
    if current_status != status_before_save and current_status == 1:
        send_verified_account_notification(instance)


class EmailQueue(models.Model):
    from_address = models.EmailField()
    to_address = models.EmailField()
    subject = models.CharField(max_length=255)
    content = models.TextField()
    EMAIL_TYPE_CHIOCE = ((0, 'Registration'), (1, 'Forgot password')
                         )
    email_type = models.IntegerField(choices=EMAIL_TYPE_CHIOCE, default=0)
    EMAIL_STATUS_CHIOCE = ((0, 'Queued'), (1, 'In progress'), (2, 'Sent'),
        (3, 'Failed'))
    status = models.IntegerField(choices=EMAIL_STATUS_CHIOCE, default=0)
    attachment_file_path = models.TextField(null=True, blank=True)
    cc_address = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return "Email to " + self.to_address


