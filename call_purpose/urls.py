from django.urls import path
from call_purpose import views
from .views import DefineCallPurposeView, create_call



urlpatterns = [
    path('',views.index, name='index'),
    path('define-call-purpose', DefineCallPurposeView.as_view(), name='define-call-purpose'),
    # path('call-response/<int:pk>/', CallResponseView.as_view(), name='call-response'),
    
    # path('api/signup/', SignupView.as_view(), name='api-signup'),
    path('signup/', views.signup, name='signup-page'),
    path('signin/', views.signin, name='signin'),
    
    path('logout/', views.logout_request, name='logout'),
    path('call/', views.create_call, name='call'),
    path('generate_shopifystoresdetail/', views.generate_shopifystoresdetail, name='generate-shopifystoresdetail'),
    path('show-leads/', views.show_leads, name='all-leads'),
    path('lead/add/', views.add_lead, name='add-lead'),
    path('lead/<int:id>/',views.get_or_update_lead, name='get-or-update-lead'),
    path('lead/find/', views.find_leads, name='find-leads'),
    path('lead/<int:id>/add_notes/',views.add_notes, name='add-notes'),
]


    
    

