from functools import wraps
from flask import abort
from flask_login import current_user
from .models import Permission

def admin_required(func): 
    return permission_required(Permission.ADMIN)(func) #??????

def permission_required(permission):
    def decorator(func):
        @wraps(func)  #讓呼叫此decorator的屬性還維持func
        def decorated_function(*args,**kwargs):
            if not current_user.can(permission):
                abort(403)
            return func(*args,**kwargs) #裡面應是包裝呼叫permission_required裝飾的函數
        return decorated_function
    return decorator

