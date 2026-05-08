from flask import session, redirect, url_for

def login_required(func):
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth_bp.login"))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper