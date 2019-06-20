import datetime
import time

from django.core.management import BaseCommand
from testapp.models import EmailQueue
from django.core.mail import send_mail
from django.core.mail import EmailMessage



class Command(BaseCommand):
    """
    Management command to process mail queue
    """
    help = "Management command to process mail queue"
    
    def handle(self, *args, **options):
        self.stdout.write("Start processing queue")
        start_time = datetime.datetime.now()
        now = datetime.datetime.now()
        while 1:
        # while(now - start_time).seconds < 45:
            time.sleep(0.01)
            now = datetime.datetime.now()
            email_qs = EmailQueue.objects.filter(status=0)
            if not email_qs.exists():
                time.sleep(5)
                now = datetime.datetime.now()
                continue
            for email_obj in email_qs:
                email_obj.status = 2
                email_obj.from_address = "*****"
                email_obj.to_address = "*****"
                email_obj.save()
                try:
                    cc_address = email_obj.cc_address
                    if cc_address:
                        cc_address = [cc_address]
                    email_message = EmailMessage(email_obj.subject, email_obj.content, 
                        email_obj.from_address, [email_obj.to_address], cc=cc_address)
                    email_message.content_subtype = "html"
                    if email_obj.attachment_file_path:
                        email_message.attach_file(email_obj.attachment_file_path)
                    email_message.send()
                    email_obj.status = 1
                    email_obj.save()
                except Exception as e:
                    email_obj.status = 3
                    email_obj.save()
                    self.stdout.write(e)
                    self.stdout.write("Exception...................")
            now = datetime.datetime.now()
        self.stdout.write("End processing queue")
