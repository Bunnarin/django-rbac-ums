from django import template

register = template.Library()

@register.filter
def get_attr_from_object(value, arg):
    """
    Gets an attribute of an object dynamically using its string name.
    Example: {{ obj|get_attr_from_object:'my_field_name' }}
    Handles cases where the attribute might be a callable (like get_FOO_display).
    """
    if "." in arg:
        # chain the attribute
        primary_attr = getattr(value, arg.split(".")[0])
        secondary_attr = getattr(primary_attr, arg.split(".")[1])
        return secondary_attr
    return getattr(value, arg)
