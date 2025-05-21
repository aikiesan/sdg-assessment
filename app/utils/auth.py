"""
Authentication Utilities.

This file provides authentication-related utilities, specifically a decorator
for protecting Flask routes by requiring a valid JSON Web Token (JWT).
"""
import jwt as pyjwt  # Used for encoding and decoding JSON Web Tokens (JWTs). Renamed to pyjwt to avoid conflict if 'jwt' is used elsewhere.
from functools import wraps # Utility for creating decorators that preserve the original function's metadata.
from flask import request, jsonify, current_app, g # Flask utilities:
                                                 # `request` for accessing incoming request data (like headers).
                                                 # `jsonify` for creating JSON responses.
                                                 # `current_app` for accessing the current Flask application's configuration (e.g., SECRET_KEY).
                                                 # `g` (application global) for storing data during a request context (e.g., user_id from token).


def token_required(f):
    """
    Decorator for Flask routes to ensure a valid JSON Web Token (JWT) is present
    in the 'Authorization' header.

    If the token is valid, the decorated function is called, and the user's ID
    from the token payload is made available via `flask.g.user_id`.
    If the token is missing, invalid, or expired, an appropriate JSON error
    response with a 401 status code is returned.
    """
    @wraps(f) # Preserves the name, docstring, etc., of the decorated function `f`.
    def decorated(*args, **kwargs):
        """
        The wrapper function that implements the token validation logic.
        """
        # Attempt to fetch the 'Authorization' header from the incoming request.
        auth_header = request.headers.get('Authorization', None)
        
        # Check if the header exists and starts with 'Bearer '.
        # The 'Bearer ' prefix is standard for JWT authorization.
        if not auth_header or not auth_header.startswith('Bearer '):
            # Return a 401 Unauthorized error if the header is missing or malformed.
            return jsonify({'error': 'Authorization header missing or invalid (must be Bearer token)'}), 401
        
        # Extract the token string by splitting the header value (e.g., "Bearer <token_string>").
        token = auth_header.split(' ')[1] 
        
        try:
            # Attempt to decode the JWT.
            # `current_app.config['SECRET_KEY']` is used as the secret for decoding,
            # which must match the key used for encoding the token.
            # `algorithms=['HS256']` specifies the expected signing algorithm.
            payload = pyjwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            
            # If decoding is successful, store the 'user_id' from the token's payload
            # into `flask.g.user_id`. This makes the user ID accessible within the
            # protected route handler.
            g.user_id = payload['user_id']
            
        except pyjwt.ExpiredSignatureError:
            # Handle the case where the token has expired.
            return jsonify({'error': 'Token expired'}), 401
        except pyjwt.InvalidTokenError:
            # Handle cases where the token is otherwise invalid (e.g., malformed, wrong signature).
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            # Catch any other unexpected errors during token processing.
            # It's good practice to log such errors for debugging.
            # current_app.logger.error(f"Unexpected error during token decoding: {str(e)}")
            return jsonify({'error': f'Token processing error: {str(e)}'}), 401
            
        # If the token is successfully decoded and validated, call the original decorated route function.
        return f(*args, **kwargs)
    return decorated
