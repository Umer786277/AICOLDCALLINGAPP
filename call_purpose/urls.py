from django.urls import path
from .views import DefineCallPurposeView, CallResponseView
from call_purpose import views



urlpatterns = [
    path('',views.index, name='index'),
    path('define-call-purpose', DefineCallPurposeView.as_view(), name='define-call-purpose'),
    path('call-response/<int:pk>/', CallResponseView.as_view(), name='call-response'),
    path('retrieve-person/<int:pk>/', views.retrieve_person, name='retrieve_person'),
    path('signup/',views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.logout_request, name='logout'),
    path('create/', views.create_company, name='create_company'),
    path('call/', views.create_call, name='call'),
    path('generate-call-summary/<str:call_id>/',views.get_call_summary, name='generate_call_summary'),
    path('send-to-llm', views.send_to_llm, name='send_to_llm'),
]


    
    

