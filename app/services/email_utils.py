"""
Email Utility Functions.

This module provides utility functions for sending emails asynchronously,
such as user email confirmation and password reset emails. It integrates
with Flask-Mail and uses threading to prevent blocking the main application
while emails are being sent.
"""
from flask_mail import Message  # Used to construct email messages.
from app import mail  # Flask-Mail extension instance from the main application.
from flask import current_app, render_template, url_for # `current_app` for accessing app context in threads, `render_template` for email bodies, `url_for` for generating URLs.
from threading import Thread  # Used for sending emails in a separate thread.

def send_async_email(app, msg):
    """
    Sends an email asynchronously in a separate thread.

    This function is intended to be run in a background thread to prevent
    the email sending process from blocking the main application, improving
    response times for user requests.

    Args:
        app (Flask): The Flask application instance. This is needed to
                     establish an application context within the thread.
        msg (Message): The Flask-Mail Message object to be sent.
    """
    # The Flask application context is required for extensions like Flask-Mail
    # to function correctly, especially when operations are run outside of
    # a typical request context (e.g., in a separate thread).
    with app.app_context():
        mail.send(msg) # Sends the email using the Flask-Mail instance.

def send_email(subject, recipients, html_body, text_body=None):
    """
    Constructs an email message and sends it asynchronously.

    This function prepares a Flask-Mail Message object with the given subject,
    recipients, HTML body, and an optional plain text body. It then dispatches
    the email sending operation to a background thread using `send_async_email`.

    Args:
        subject (str): The subject line of the email.
        recipients (list[str]): A list of email addresses to send the email to.
        html_body (str): The HTML content of the email.
        text_body (str, optional): The plain text content of the email.
                                   If None, `html_body` is used for the text body as well (though this is not ideal for pure text clients).
    """
    # Create a new Message object.
    msg = Message(subject, recipients=recipients)
    
    # Set the plain text body. If not provided, it defaults to the HTML body,
    # which is not standard but provides a fallback. Ideally, a distinct text body is better.
    msg.body = text_body or html_body 
    msg.html = html_body # Set the HTML body.
    
    # Start a new thread to send the email asynchronously.
    # `current_app._get_current_object()` is used to pass the actual Flask app
    # instance to the new thread, ensuring it works correctly with app contexts.
    thread = Thread(target=send_async_email, args=(current_app._get_current_object(), msg))
    thread.start()

def send_confirmation_email(user):
    """
    Sends an email confirmation email to a newly registered user.

    This function generates a unique confirmation token for the user,
    constructs a confirmation URL, and renders email templates (both HTML
    and plain text) with this URL. It then uses `send_email` to dispatch
    the confirmation email.

    Args:
        user (User): The user object (instance of `app.models.user.User`)
                     to whom the confirmation email will be sent. The user
                     object must have `generate_confirmation_token` and `email` attributes.
    """
    # Generate a time-sensitive confirmation token for the user.
    # Assumes the User model has a method `generate_confirmation_token()`.
    token = user.generate_confirmation_token()
    
    # Create the confirmation URL using `url_for`. `_external=True` generates an absolute URL.
    # 'auth.confirm_email' refers to the route/endpoint for email confirmation.
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    
    # Render the HTML and plain text versions of the email using templates.
    # These templates should include the `confirm_url` and user details.
    html = render_template('auth/email/confirm_email.html', confirm_url=confirm_url, user=user)
    text = render_template('auth/email/confirm_email.txt', confirm_url=confirm_url, user=user)
    
    subject = "Please confirm your email"
    # Send the email using the generic send_email function.
    send_email(subject, [user.email], html, text)

def send_password_reset_email(user):
    """
    Sends a password reset email to a user who has requested it.

    This function generates a unique password reset token for the user,
    constructs a password reset URL, and renders email templates (HTML and
    plain text) with this URL. It then uses `send_email` to dispatch the email.

    Args:
        user (User): The user object (instance of `app.models.user.User`)
                     who requested the password reset. The user object must
                     have `generate_reset_token` and `email` attributes.
    """
    # Generate a time-sensitive password reset token for the user.
    # Assumes the User model has a method `generate_reset_token()`.
    token = user.generate_reset_token()
    
    # Create the password reset URL. `_external=True` ensures an absolute URL.
    # 'auth.reset_password' refers to the route/endpoint for handling password resets.
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    # Render the HTML and plain text versions of the email.
    # Templates should include the `reset_url` and user details.
    html = render_template('auth/email/reset_password.html', reset_url=reset_url, user=user)
    text = render_template('auth/email/reset_password.txt', reset_url=reset_url, user=user)
    
    subject = "Password Reset Request"
    # Send the email using the generic send_email function.
    send_email(subject, [user.email], html, text)