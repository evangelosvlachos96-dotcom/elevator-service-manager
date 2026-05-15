from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    profile_pic = models.ImageField(
        null=True, blank=True)
    phone_number = models.CharField(max_length=20)
    address = models.CharField(max_length=30)
    region = models.CharField(max_length=20)
    email = models.EmailField(('email address'), blank=False, unique=True)


class week(models.Model):
    mon = models.CharField(max_length=50, null=True, blank=True)
    tue = models.CharField(max_length=50, null=True, blank=True)
    wed = models.CharField(max_length=50, null=True, blank=True)
    thu = models.CharField(max_length=50, null=True, blank=True)
    fri = models.CharField(max_length=50, null=True, blank=True)
    sat = models.CharField(max_length=50, null=True, blank=True)
    sun = models.CharField(max_length=50, null=True, blank=True)
    todays_shift = models.CharField(max_length=50, null=True, blank=True)
    week_year = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return str(self.week_year)


class elevators(models.Model):
    id = models.CharField(max_length=200, primary_key=True,
                          unique=True,)
    client_id = models.ForeignKey(User, limit_choices_to={
        'groups__name': "Client"}, on_delete=models.CASCADE)

    STATUS = (
        ('Hydraulic', 'Hydraulic'),
        ('Mechanical', 'Mechanical'),
    )
    elevator_type = models.CharField(max_length=200, null=True, choices=STATUS)
    moter_cauldron = models.CharField(max_length=20, null=True)
    control_panel = models.CharField(max_length=20, null=True)
    book_code = models.CharField(max_length=20, null=True, unique=True)
    watt = models.CharField(max_length=20, null=True, blank=True)
    station = models.PositiveIntegerField(null=True)
    wire_ropes = models.PositiveIntegerField(null=True)
    chassi = models.CharField(max_length=20, null=True, blank=True)
    last_kteo = models.DateField(
        auto_now_add=False, auto_now=False,  null=True, blank=True)
    comment = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return str(self.id)


class service(models.Model):
    elevator_id = models.ForeignKey(
        elevators, to_field='id', on_delete=models.CASCADE)
    stuff_id = models.ForeignKey(User, related_name='test_name', limit_choices_to={
        'groups__name': "Company"}, null=True, on_delete=models.SET_NULL)
    cost = models.PositiveIntegerField()
    recipe_code = models.CharField(
        max_length=50, unique=True, null=True, blank=True)

    date_ekd = models.DateField(
        auto_now_add=False, auto_now=False,  null=True, blank=True)
    date_ejof = models.DateField(
        auto_now_add=False, auto_now=False,  null=True, blank=True)

    date = models.DateField(
        auto_now_add=False, default=now, null=True)
    comment = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return str(self.recipe_code)


class Message(models.Model):
    CHOICES = (
        ('Alert', 'Alert'),
        ('Simple', 'Simple'),
    )
    CHOICES2 = (
        ('Door Locked', 'Door Locked'),
        ('Black out', 'Black out'),
        ('Control Table', 'Control Table'),
        ('Station Level', 'Station Level'),
        ('Ropes Problem', 'Ropes Problem'),

    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE)
    receiver = models.CharField(
        max_length=200, null=True)
    elvtr = models.CharField(
        max_length=200, blank=True, null=True)
    message_type = models.CharField(
        max_length=200, null=True, choices=CHOICES, default='Simple')
    categorized_problems = models.CharField(
        max_length=200, null=True, blank=True, choices=CHOICES2)
    seen = models.BooleanField(
        default=False)
    date = models.DateTimeField(
        auto_now_add=False, default=now, null=True)
    text = models.CharField(max_length=200)
    picture = models.ImageField(null=True, blank=True)
