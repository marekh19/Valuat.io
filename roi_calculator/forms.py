from django import forms


class TickerForm(forms.Form):
    ticker = forms.CharField(label="e.g. 'AMD' or 'AAPL'", max_length=6)
