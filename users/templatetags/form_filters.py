from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={'class': css_class})

@register.filter(name='remove_placeholder')
def remove_placeholder(field):
    return field.as_widget(attrs={'placeholder': ' '})