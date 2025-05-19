from django import forms

class PaymentForm(forms.Form):
    course_id = forms.IntegerField(widget=forms.HiddenInput())
