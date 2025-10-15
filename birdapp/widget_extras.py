from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    """Add CSS class to form field."""
    css_classes = value.field.widget.attrs.get('class', '')
    if css_classes:
        css_classes = f"{css_classes} {arg}"
    else:
        css_classes = arg
    return value.as_widget(attrs={'class': css_classes})

@register.filter(name='add_attrs')
def add_attrs(value, arg):
    """Add multiple attributes to form field."""
    attrs = {}
    for attr in arg.split(','):
        key, val = attr.split(':', 1)
        attrs[key.strip()] = val.strip()
    return value.as_widget(attrs=attrs)