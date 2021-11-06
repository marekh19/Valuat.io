from django.urls import path
from . import views

urlpatterns = [
    path('', views.ticker_form, name='roi_calculator-ticker_form'),
    path('<str:ticker>/', views.ticker_view, name='roi_calculator-ticker_view'),
]
