from django.urls import path
from . import views

urlpatterns = [
    path('', views.ticker_form, name='roi_calculator-ticker_form'),
]
