from django import template

register = template.Library()

@register.filter(name='is_int')
def is_int(value):
    try:
        int(value)
    except ValueError:
        return False
    except TypeError:
        return False
    
    return True