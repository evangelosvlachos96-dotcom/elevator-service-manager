import stripe
import datetime
from datetime import date
from core.models import *
from .decorators import allowed_users
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

from django.conf import settings  # new
from django.http.response import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from django.views.generic.base import TemplateView

from .filters import ProductFilter, ClientFilter, ElevatorFilter, MessageFilter


from .forms import ElevatorForm, paswdChange, UpdateUser, ServiceForm, CommentServiceForm, CustomUserCreationForm

stripe.api_key = settings.STRIPE_SECRET_KEY


def SuccessView(request):

    context = {}
    return render(request, 'payments/success.html', context)


class CancelledView(TemplateView):
    template_name = 'payments/cancelled.html'


# AJAX function


@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)


@csrf_exempt
def create_checkout_session(request, pk):
    if request.method == 'GET':
        domain_url = 'http://127.0.0.1:8000/'
        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            # Create new Checkout Session for the order
            # Other optional params include:
            # [billing_address_collection] - to display billing address details on the page
            # [customer] - if you have an existing Stripe Customer ID
            # [payment_intent_data] - capture the payment later
            # [customer_email] - prefill the email input in the form
            # For full details see https://stripe.com/docs/api/checkout/sessions/create

            # ?session_id={CHECKOUT_SESSION_ID} means the redirect will have the session ID set as a query param

            checkout_session = stripe.checkout.Session.create(
                success_url=domain_url +
                'success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + 'cancelled/',
                payment_method_types=['card'],
                mode='payment',
                line_items=[
                    {
                        'name': 'Elevator Service',
                        'quantity': 1,
                        'currency': 'eur',
                        'amount': int(pk) * 100,
                    }
                ]
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})


# Login view

def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            group = request.user.groups.all()[0].name
            if group == 'Client':
                return redirect('client')
            if group == 'Company':
                return redirect('company')
        else:
            messages.error(request, 'Username or password is incorrect!')
    return render(request, 'login.html')


# Client view

@ allowed_users(allowed_roles=['Client'])
@ login_required(login_url='login')
def client_view(request):
    user = request.user
    elevator_owned = elevators.objects.filter(client_id=user.id)
    ordered_services = service.objects.all().order_by('-date')
    service_done = []
    for elvtr in elevator_owned:
        if service.objects.filter(elevator_id=elvtr.id):
            service_done.append(
                ordered_services.filter(elevator_id=elvtr.id))

    messages = Message.objects.filter(receiver=user.username)
    total_new_messages = 0
    for msg in messages:
        if msg.seen == False:
            total_new_messages += 1
    current_week = week.objects.all().last()
    username = current_week.todays_shift
    technician = User.objects.get(username=username)

    context = {'technician': technician, 'total_new_messages': total_new_messages,
               'elevator_owned': elevator_owned, 'service_done': service_done}
    return render(request, 'client.html', context)

# Payment session


@ login_required(login_url='login')
def payService(request):

    context = {}
    return render(request, 'payment.html', context)


@ login_required(login_url='login')
def charge(request):

    context = {}
    return render(request, 'payment.html', context)


# company view


@ allowed_users(allowed_roles=['Company'])
@ login_required(login_url='login')
def company_view(request):

    clientss = User.objects.filter(groups__name='Client')

    elevatorss = elevators.objects.all()
    user = request.user.username
    group = request.user.groups.all().last()
    messages = Message.objects.all()
    if group.name == "Company":
        messages = messages.filter(receiver=user)
    if group.name == "Administrator":
        messages = messages.filter(sender__in=clientss)
    new_messages = messages.filter(seen='False')
    total_new_messages = new_messages.count()

    myFilter = ElevatorFilter(request.GET, queryset=elevatorss)
    elevatorss = myFilter.qs
    services = service.objects.all().order_by('-id')[:10]
    servicess = service.objects.all()

    clientss = User.objects.filter(groups__name='Client')
    stuffs = User.objects.filter(groups__name='Company')

    total_clients = clientss.count()
    total_elevators = elevatorss.count()
    total_services = servicess.count()
    total_stuff = stuffs.count()
    now = datetime.datetime.now()
    if now.strftime("%A") == "Monday":
        if str(week.objects.latest('id').week_year) != str(date.today()):
            book = week.objects.create()
            book.week_year = date.today()
            book.save()

    current_week = week.objects.latest('id')

    if request.method == 'POST':
        monday = request.POST['mon']
        tuesday = request.POST['tue']
        wednesday = request.POST['wed']
        thursday = request.POST['thu']
        friday = request.POST['fri']
        saturday = request.POST['sat']
        sunday = request.POST['sun']
        shift = request.POST['shift']

        current_week.mon = monday
        current_week.tue = tuesday
        current_week.wed = wednesday
        current_week.thu = thursday
        current_week.fri = friday
        current_week.sat = saturday
        current_week.sun = sunday
        current_week.todays_shift = shift
        current_week.save()

    context = {'total_new_messages': total_new_messages, 'myFilter': myFilter, 'clientss': clientss, 'elevators': elevatorss,
               'total_clients': total_clients, 'total_elevators': total_elevators,
               'total_services': total_services, 'services': services, 'stuffs': stuffs, 'total_stuff': total_stuff, 'current_week': current_week}
    return render(request, 'company.html', context)

# Search


@ allowed_users(allowed_roles=['Company'])
@ login_required(login_url='login')
def ServiceHistory(request):
    services = service.objects.all()
    myFilter = ProductFilter(request.GET, queryset=services)
    services = myFilter.qs
    context = {'services': services, 'myFilter': myFilter}
    return render(request, 'search/ServiceHistory.html', context)


@ allowed_users(allowed_roles=['Company'])
@ login_required(login_url='login')
def SearchElevator(request):
    elevatorss = elevators.objects.all()

    myFilter = ElevatorFilter(request.GET, queryset=elevatorss)
    elevatorss = myFilter.qs
    context = {'elevatorss': elevatorss, 'myFilter': myFilter}
    return render(request, 'search/SearchElevator.html', context)


@ login_required(login_url='login')
def ElevatorCard(request, pk):
    elvtr = elevators.objects.get(id=pk)
    services = service.objects.filter(elevator_id=pk)
    print(services)

    context = {'elvtr': elvtr, 'services': services}
    return render(request, 'ElevatorCard.html', context)

# Create views


@ allowed_users(allowed_roles=['Company'])
@ login_required(login_url='login')
def makeService(request, pk):
    ServiceFormm = inlineformset_factory(elevators, service, fields=('stuff_id', 'cost', 'recipe_code', 'date_ekd', 'date_ejof', 'date'), widgets={
        'elevator_id': forms.Select(attrs={'class': 'dropdown_menu col-md-12'}),
        'stuff_id': forms.Select(attrs={'class': 'dropdown_menu'}),
    }, max_num=1, can_delete=False)

    elevatorr = elevators.objects.get(id=pk)
    current_week = week.objects.latest('id')
    staf_working = current_week.todays_shift

    formset = ServiceFormm(queryset=service.objects.none(),
                           instance=elevatorr)

    if request.method == 'POST':
        formset = ServiceFormm(request.POST, instance=elevatorr)
        if formset.is_valid():
            formset.save()
            return redirect('company')
    context = {'formset': formset, 'elevatorr': elevatorr}
    return render(request, 'add/makeService.html', context)


@ allowed_users(allowed_roles=['Company'])
@ login_required(login_url='login')
def addMember(request):
    form = CustomUserCreationForm
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_group = Group.objects.get(name='Company')

            user.groups.add(user_group)

            return redirect('company')
    context = {'form': form}
    return render(request, 'add/addStuff.html', context)


@ allowed_users(allowed_roles=['Company'])
@ login_required(login_url='login')
def addClient(request):
    form = CustomUserCreationForm
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            user_group = Group.objects.get(name='Client')

            user.groups.add(user_group)

            return redirect('company')
    context = {'form': form}
    return render(request, 'add/addClient.html', context)


@ allowed_users(allowed_roles=['Company'])
@ login_required(login_url='login')
def addElevator(request, pk):
    ElevatorFormm = inlineformset_factory(
        User, elevators, fields=('id', 'elevator_type', 'moter_cauldron', 'book_code', 'chassi', 'control_panel', 'watt', 'station', 'wire_ropes', 'last_kteo', 'comment'), widgets={'elevator_type': forms.Select(attrs={'class': 'dropdown_menu'})}, max_num=1, can_delete=False)
    clien = User.objects.get(id=pk)
    formset = ElevatorFormm(
        queryset=elevators.objects.none(), instance=clien)
    if request.method == 'POST':
        formset = ElevatorFormm(request.POST, instance=clien)
        if formset.is_valid():
            formset.save()
            return redirect('company')
    context = {'formset': formset, 'client': clien.last_name}
    return render(request, 'add/addElevator.html', context)


# Delete views

@ allowed_users(allowed_roles=['Company'])
@ login_required(login_url='login')
def deleteClient(request, pk):
    client = User.objects.get(id=pk)
    if request.method == "POST":
        client.delete()
        return redirect('company')

    context = {'item': client}
    return render(request, 'delete/deleteC.html', context)


@ allowed_users(allowed_roles=['Company'])
@ login_required(login_url='login')
def deleteStuff(request, pk):
    stuf = User.objects.get(id=pk)
    if request.method == "POST":
        stuf.delete()
        return redirect('company')

    context = {'item': stuf}
    return render(request, 'delete/deleteSt.html', context)


@ allowed_users(allowed_roles=['Company'])
@ login_required(login_url='login')
def deleteElev(request, pk):
    elevator = elevators.objects.get(id=pk)
    if request.method == "POST":
        elevator.delete()
        return redirect('company')

    context = {'item': elevator}
    return render(request, 'delete/deleteE.html', context)


@ allowed_users(allowed_roles=['Company'])
@ login_required(login_url='login')
def deleteServ(request, pk):
    servic = service.objects.get(id=pk)
    if request.method == "POST":
        servic.delete()
        return redirect('company')

    context = {'item': servic}
    return render(request, 'delete/deleteS.html', context)


# Update views

@ login_required(login_url='login')
def updateClient(request, pk):
    one = Group.objects.filter(name='Client')
    client = User.objects.get(id=pk)
    form = UpdateUser(instance=client)
    if request.method == 'POST':
        form = UpdateUser(request.POST, instance=client)
        if form.is_valid():
            form.save()
        if request.user.groups.filter(name='Company').exists():
            return redirect('company')
        elif request.user.groups.filter(name='Client').exists():
            return redirect('client')

    context = {'form': form, 'client': client}
    return render(request, 'update/updateClient.html', context)


@ login_required(login_url='login')
def change_password(request, pk):
    one = Group.objects.filter(name='Client')
    client = User.objects.get(id=pk)
    form = CustomUserCreationForm(instance=client)
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
        if request.user.groups.filter(name='Company').exists():
            return redirect('company')
        elif request.user.groups.filter(name='Client').exists():
            return redirect('client')

    context = {'form': form, 'client': client}
    return render(request, 'update/changePassword.html', context)


@ login_required(login_url='login')
def updateElevator(request, pk):
    elevator = elevators.objects.get(id=pk)
    form = ElevatorForm(instance=elevator)
    if request.method == 'POST':
        form = ElevatorForm(request.POST, instance=elevator)
        if form.is_valid():
            form.save()
            return redirect('company')

    context = {'form': form, 'elevator': elevator}
    return render(request, 'update/updateElevator.html', context)


@ allowed_users(allowed_roles=['Company'])
@ login_required(login_url='login')
def updateService(request, pk):
    servic = service.objects.get(id=pk)
    form = ServiceForm(instance=servic)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=servic)
        if form.is_valid():
            form.save()
            return redirect('company')

    context = {'form': form, 'servic': servic}
    return render(request, 'update/updateService.html', context)


@ allowed_users(allowed_roles=['Client'])
@ login_required(login_url='login')
def ServiceComment(request, pk):
    servic = service.objects.get(id=pk)
    form = CommentServiceForm(instance=servic)
    if request.method == 'POST':
        form = CommentServiceForm(request.POST, instance=servic)
        if form.is_valid():
            form.save()
            return redirect('client')

    context = {'form': form, 'servic': servic}
    return render(request, 'update/createServiceComment.html', context)


# Messages


@ allowed_users(allowed_roles=['Client'])
@ login_required(login_url='login')
def AlertMessage(request, pk, ig):
    MessageForm = inlineformset_factory(
        User, Message, fields=('categorized_problems', 'text', 'picture',),  widgets={'categorized_problems': forms.Select(attrs={'class': 'dropdown_menu'}), 'text': forms.Textarea(attrs={
            "class": "dropdown_menu",
            'style': 'width: 450px; height:150px; resize:none; text-align: left; ',
            "rows": "3",

        })}, max_num=1, can_delete=False)

    sender = User.objects.get(id=pk)
    formset = MessageForm(queryset=Message.objects.none(),
                          instance=sender)
    if request.method == 'POST':
        formset = MessageForm(request.POST, request.FILES, instance=sender)
        if formset.is_valid():
            formset.save()
            message = Message.objects.all().last()
            current_week = week.objects.all().last()
            message.message_type = 'Alert'
            message.receiver = current_week.todays_shift
            message.elvtr = ig
            message.save()

            return redirect('client')
    current_week = week.objects.all().last()
    shift = current_week.todays_shift
    receiver = User.objects.get(username=shift)
    context = {'receiver': receiver,
               'formset': formset, 'sender': sender, 'elvtr': ig}
    return render(request, 'messages/send_report_message.html', context)


@ login_required(login_url='login')
def ReplyMessage(request, pk):
    msg = Message.objects.get(id=pk)
    MessageForm = inlineformset_factory(
        User, Message, fields=('text', 'picture',),  widgets={'categorized_problems': forms.Select(attrs={'class': 'dropdown_menu'}), 'text': forms.Textarea(attrs={
            "class": "dropdown_menu",
            'style': 'width: 450px; height:150px; resize:none; text-align: left; ',
            "rows": "3",

        })}, max_num=1, can_delete=False)

    sender = request.user
    receiver = msg.sender
    formset = MessageForm(queryset=Message.objects.none(),
                          instance=sender)
    if request.method == 'POST':
        formset = MessageForm(request.POST, request.FILES, instance=sender)
        if formset.is_valid():
            formset.save()
            message = Message.objects.all().last()
            message.receiver = receiver.username
            message.save()

            return redirect('allMessages')

    context = {'formset': formset, 'msg': msg, }
    return render(request, 'messages/reply_message.html', context)


@ login_required(login_url='login')
def allMessages(request):
    clientss = User.objects.filter(groups__name='Client')
    compnyy = User.objects.filter(groups__name='Company')
    user = request.user.username
    group = request.user.groups.all().last()
    messages = Message.objects.all()
    sndr = User.objects.get(username=user)
    messages_as_sender = Message.objects.filter(sender=sndr)
    if group.name == "Administrator":
        messages = messages.filter(sender__in=clientss)
        messages_as_sender = Message.objects.filter(sender__in=compnyy)
    if group.name == "Company":
        messages = messages.filter(receiver=user)
    if group.name == "Client":
        messages = messages.filter(receiver=user)
    total_sent_messages = messages_as_sender.count()
    total_messages = messages.count()
    myFilter = MessageFilter(request.GET, queryset=messages)
    messages = myFilter.qs
    messages = messages.order_by('-date')
    messages_as_sender = messages_as_sender.order_by('-date')

    context = {'total_sent_messages': total_sent_messages, 'messages_as_sender': messages_as_sender, 'myFilter': myFilter,
               'total_messages': total_messages, 'messages': messages, }
    return render(request, 'messages/all_messages.html', context)


@ login_required(login_url='login')
def viewMessage(request, pk):
    message = Message.objects.get(id=pk)
    message.seen = True
    message.save()
    client = message.sender
    user_id = client.id
    user = request.user
    elevator_owned = elevators.objects.filter(client_id=user_id)
    context = {'user': user, 'message': message,
               'elevator_owned': elevator_owned, }
    return render(request, 'messages/view_message.html', context)


@ login_required(login_url='login')
def SimpleMessage(request):
    clientss = User.objects.filter(groups__name='Client')
    companyy = User.objects.filter(groups__name='Company')
    user = request.user.username
    group = request.user.groups.all().last()
    receiver_group = clientss
    if group.name == "Client":
        receiver_group = companyy
    else:
        receiver_group = clientss
    MessageForm = inlineformset_factory(
        User, Message, fields=('text', 'picture',),  widgets={'categorized_problems': forms.Select(attrs={'class': 'dropdown_menu'}), 'text': forms.Textarea(attrs={
            "class": "dropdown_menu",
            'style': 'width: 450px; height:150px; resize:none; text-align: left; ',
            "rows": "3",

        })}, max_num=1, can_delete=False)
    sender = request.user
    formset = MessageForm(queryset=Message.objects.none(),
                          instance=sender)
    if request.method == 'POST':
        receiverr = request.POST['drop1']
        if receiverr == 'All':
            receiverr = clientss
        if receiverr == 'tocompany':
            receiverr = companyy
        if receiverr == clientss or receiverr == companyy:
            for user in receiverr:
                formset = MessageForm(
                    request.POST, request.FILES, instance=sender)
                if formset.is_valid():
                    formset.save()
                    message = Message.objects.all().last()
                    message.receiver = user.username
                    message.save()
        else:
            formset = MessageForm(request.POST, request.FILES, instance=sender)
            if formset.is_valid():
                formset.save()
                message = Message.objects.all().last()
                message.receiver = receiverr
                message.save()

        return redirect('allMessages')

    context = {'receiver_group': receiver_group, 'formset': formset, }
    return render(request, 'messages/send_simple_message.html', context)


# Logout


@ login_required(login_url='login')
def logoutUser(request):
    logout(request)
    return redirect('login')
