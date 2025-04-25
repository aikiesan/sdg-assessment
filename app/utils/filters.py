"""
Custom template filters for the application.
"""

from datetime import datetime
try:
    import babel
except ImportError:
    babel = None

def format_datetime(value, format='medium'):
    """Format a datetime object for display."""
    if value is None:
        return ""
    # Ensure value is a datetime object
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            try:
                value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return value # Return original string if parsing fails
    elif not isinstance(value, datetime):
         return value # Return as is if not datetime or string
    if format == 'full':
        format_string = "EEEE, d MMMM y 'at' h:mm:ss a zzzz"
    elif format == 'medium':
        format_string = "MMM d, y, h:mm a"
    elif format == 'short_date':
        format_string = "MM/dd/yy"
    elif format == 'medium_date':
        format_string = "MMM d, y"
    else:
        format_string = "MMM d, y, h:mm a"
    if babel:
        try:
            return babel.dates.format_datetime(value, format_string)
        except Exception:
            pass
    # Fallback to strftime if Babel is not available
    return value.strftime('%b %d, %Y, %I:%M %p')

def format_date_filter(value):
    return format_datetime(value, format='medium_date')

def register_filters(app):
    app.jinja_env.filters['format_date'] = format_date_filter
    app.jinja_env.filters['format_datetime'] = format_datetime
