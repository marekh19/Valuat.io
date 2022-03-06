from django import forms


class TickerForm(forms.Form):
    ticker = forms.CharField(label="", max_length=6, widget=forms.TextInput(
        attrs={'class': 'drac-input drac-input-lg drac-input-green drac-text-green drac-m-xs center'}))


class TickerFormSmall(forms.Form):
    ticker = forms.CharField(label="", max_length=6, widget=forms.TextInput(
        attrs={'placeholder': "Enter ticker...", 'class': 'drac-input drac-input-green drac-text-green drac-m-xs'}))
