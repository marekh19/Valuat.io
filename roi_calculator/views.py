from django.shortcuts import render
from django.http import HttpResponse
from .forms import TickerForm
from .utils import ticker_info


def ticker_form(request):

    if request.method == 'POST':
        form = TickerForm(request.POST)
        if form.is_valid():
            ticker = form.cleaned_data['ticker']
        print(ticker)
        print(ticker_info(ticker))

    form = TickerForm()
    return render(request, 'search.html', {'form': form})
