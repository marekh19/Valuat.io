from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import TickerForm, TickerFormSmall
from .utils import valuation_dictionary, seven_yrs_overview, return_on_investment, candlestick


def ticker_form(request):
    if request.method == 'GET':
        form = TickerForm()
        return render(request, 'search.html', {'form': form})
    if request.method == 'POST':
        form = TickerForm(request.POST)
        if form.is_valid():
            ticker = form.cleaned_data['ticker'].upper()
        return redirect('/' + ticker + '/')


def ticker_view(request, ticker):
    if request.method == 'GET':
        fundamentals = valuation_dictionary(ticker)
        overview = seven_yrs_overview(fundamentals)
        roi = return_on_investment(fundamentals, overview)
        form = TickerFormSmall()
        context = {
            'fundamentals': fundamentals,
            '7yrs': overview,
            'roi': roi,
            'form': form,
            'candlestick': candlestick(ticker),
        }
        return render(request, 'ticker.html', context)
    if request.method == 'POST':
        form = TickerFormSmall(request.POST)
        if form.is_valid():
            ticker = form.cleaned_data['ticker'].upper()
        return redirect('/' + ticker + '/')
