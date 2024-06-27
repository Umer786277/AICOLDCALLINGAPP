from django.urls import path
from .views import DefineCallPurposeView
from call_purpose import views


urlpatterns = [
    path('',views.index, name='index'),
    path('define-call-purpose', DefineCallPurposeView.as_view(), name='define-call-purpose'),
    path('signup/',views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.logout_request, name='logout'),

    
    
]
