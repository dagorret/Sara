from django.urls import path
from coreui.views import home

urlpatterns = [
    path('', home),
]