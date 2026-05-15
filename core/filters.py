import django_filters
from django import forms
from django_filters import DateFilter, CharFilter
from django.forms.widgets import TextInput

from .models import *


class ProductFilter(django_filters.FilterSet):
    id_contains = CharFilter(
        field_name='elevator_id__id', label='Elevator ID ', lookup_expr='icontains')
    start_date = DateFilter(label='From ',
                            field_name="date", lookup_expr='gte', widget=TextInput(attrs={'placeholder': 'e.g 2021-12-23'}))
    end_date = DateFilter(
        label='Until ', field_name="date", lookup_expr='lte', widget=TextInput(attrs={'placeholder': 'e.g 2021-12-23'}))

    class Meta:
        model = service
        fields = ['stuff_id']


class ClientFilter(django_filters.FilterSet):
    surname_contains = CharFilter(
        field_name='last_name', lookup_expr='icontains')

    class Meta:
        model = User
        fields = ['email', 'phone_number']


class ElevatorFilter(django_filters.FilterSet):
    id_contains = CharFilter(
        field_name='id', lookup_expr='icontains')
    bookcode_contains = CharFilter(
        field_name='book_code', lookup_expr='icontains')
    lastkteo_before = DateFilter(label='Passed KTEO before ',
                                 field_name="last_kteo", lookup_expr='gte', widget=TextInput(attrs={'placeholder': 'e.g 2021-12-23'}))

    class Meta:
        model = elevators
        fields = ['client_id', 'elevator_type', ]


class MessageFilter(django_filters.FilterSet):

    class Meta:
        model = Message
        fields = ['seen', 'message_type', 'sender']
