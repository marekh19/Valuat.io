from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import TickerForm
from .utils import valuation_dictionary


def ticker_form(request):
    if request.method == 'GET':
        form = TickerForm()
        return render(request, 'search.html', {'form': form})
    if request.method == 'POST':
        form = TickerForm(request.POST)
        if form.is_valid():
            ticker = form.cleaned_data['ticker'].upper().replace('.', '-')
        return redirect('/' + ticker + '/')


def ticker_view(request, ticker):
    context = {'fundamentals': valuation_dictionary(ticker)}
    return render(request, 'ticker.html', context)
