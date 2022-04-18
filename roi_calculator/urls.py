from django.urls import path
from . import views

urlpatterns = [
    path('', views.ticker_form, name='roi_calculator-ticker_form'),
    path('ticker/<str:ticker>/', views.ticker_view, name='roi_calculator-ticker_view'),
    path('e404/', views.temp_404, name='temp404'),
    path('e500/', views.temp_500, name='temp500'),
]
