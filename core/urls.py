from django.urls import path
from . import views


urlpatterns = [
    path('', views.loginPage, name="login"),
    path('company/', views.company_view, name="company"),
    path('client/', views.client_view, name="client"),
    path('logout/', views.logoutUser, name="logout"),





    # Delete urls
    path('deleteStuff/<str:pk>/', views.deleteStuff, name="delete_stuff"),
    path('deleteElevator/<str:pk>/', views.deleteElev, name="delete_elevator"),
    path('deleteService/<str:pk>/', views.deleteServ, name="delete_service"),
    path('deleteClient/<str:pk>/', views.deleteClient, name="delete_client"),

    # Update urls
    path('updateElevator/<str:pk>/', views.updateElevator, name="update_elevator"),
    path('updateService/<str:pk>/', views.updateService, name="update_service"),
    path('updateClient/<str:pk>/', views.updateClient, name="update_client"),
    path('changePassword/<str:pk>/', views.change_password, name="change_password"),
    path('createServiceComment/<str:pk>/',
         views.ServiceComment, name="service_comment"),

    # Creation urls
    path('make_service/<str:pk>/', views.makeService, name="make_service"),
    path('company/add_member/', views.addMember, name="add_member"),
    path('company/add_client/', views.addClient, name="add_client"),
    path('company/add_elevator/<str:pk>/',
         views.addElevator, name="add_elevator"),

    # Payment session
    path('config/', views.stripe_config),
    path('create-checkout-session/<str:pk>/', views.create_checkout_session),
    path('success/', views.SuccessView),
    path('cancelled/', views.CancelledView.as_view()),



    # Search
    path('serviceHistory/', views.ServiceHistory, name="service_history"),
    path('searchElevator/', views.SearchElevator, name="search_elevator"),
    path('elevatorCard/<str:pk>/', views.ElevatorCard, name="elevator_card"),


    # Messages
    path('alert-message/<str:pk>/<str:ig>/',
         views.AlertMessage, name="send_alert_message"),
    path('allMessages/',
         views.allMessages, name="allMessages"),
    path('viewMessage/<str:pk>/',
         views.viewMessage, name="messageview"),
    path('reply-message/<str:pk>/',
         views.ReplyMessage, name="reply_message"),
    path('simple-message/',
         views.SimpleMessage, name="simple_message"),

]
