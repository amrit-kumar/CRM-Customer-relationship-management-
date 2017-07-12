from django.db import models

# Create your models here.
STSTUS_CHOICES = (('1', '1'),
                        ('2', '2'),
                        ('16', '16')
                        )

class MsgReports(models.Model):
    request_id = models.CharField(max_length=250, null=True, blank=True)
    user_id = models.CharField(max_length=250, null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)
    discription = models.CharField(max_length=250, null=True, blank=True)
    number = models.BigIntegerField(null=True, blank=True)
    sender_id = models.CharField(max_length=250, null=True, blank=True)
    campaign_name = models.CharField(max_length=250, null=True, blank=True)
    status = models.CharField(max_length=250, choices=STSTUS_CHOICES, null=True, blank=True)

    def __str__(self):
        return self.request_id
