from django.shortcuts import render
from django.http import HttpResponse
from .forms import TickerForm
from .utils import valuation_dictionary
import yfinance as yf


def ticker_form(request):
    if request.method == 'POST':
        form = TickerForm(request.POST)
        if form.is_valid():
            ticker = form.cleaned_data['ticker']
            print(yf.Ticker(ticker).earnings)
            print(yf.Ticker(ticker).financials)
            print(yf.Ticker(ticker).quarterly_financials)
            print(yf.Ticker(ticker).quarterly_balance_sheet)
    form = TickerForm()
    return render(request, 'search.html', {'form': form})
