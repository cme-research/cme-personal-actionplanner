from django import template

register = template.Library()


@register.filter
def estimation_display(value):
    """Format a timedelta as '2 days, 4 hours' or '3 hours' etc."""
    if not value:
        return ""
    total_seconds = int(value.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    parts = []
    if days:
        parts.append(f"{days} {'day' if days == 1 else 'days'}")
    if hours:
        parts.append(f"{hours} {'hour' if hours == 1 else 'hours'}")
    return ", ".join(parts) if parts else "0 hours"
