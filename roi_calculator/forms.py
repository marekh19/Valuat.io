from django import forms


class TickerForm(forms.Form):
    ticker = forms.CharField(label="Ticker", max_length=6)


class TickerFormSmall(forms.Form):
    ticker = forms.CharField(label="", max_length=6, widget=forms.TextInput(attrs={'placeholder': "Enter ticker..."}))
