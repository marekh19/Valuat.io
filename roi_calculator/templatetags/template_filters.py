from django import template
from datetime import datetime

register = template.Library()

@register.filter('2decimal_percentage')
def percentage(value):
    return format(value / 100, ".2%").replace('%', ' %') if value != None else None

@register.filter('timestamp_to_time')
def convert_timestamp_to_time(timestamp):
    return datetime.fromtimestamp(int(timestamp)) if timestamp != None else None