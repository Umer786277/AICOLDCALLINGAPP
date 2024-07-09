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
    # path('signin/', views.signin_page, name='signin'),

    path('logout/', views.logout_request, name='logout'),
   
    path('call/', views.create_call, name='call'),
#     path('generate-call-summary/<str:call_id>/',views.get_call_summary, name='generate_call_summary'),
#     path('send-to-llm/', views.send_to_llm, name='send_to_llm'),
]


    
    

