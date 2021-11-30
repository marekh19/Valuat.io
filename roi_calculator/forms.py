from django import forms


class TickerForm(forms.Form):
    ticker = forms.CharField(label="e.g. 'AMD' or 'AAPL'", max_length=6)

class TickerFormSmall(forms.Form):
    ticker = forms.CharField(max_length=6, widget=forms.TextInput(attrs={'placeholder': "e.g. 'AMD' or 'AAPL'"}))
