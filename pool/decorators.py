from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from functools import wraps

def role_required(allowed_roles):
    """
    Function-based view'larda kullanıcının rolünü kontrol eden dekoratör.
    Kullanım: @role_required(['SHOP', 'ADMIN'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
                
            user_role = getattr(request.user, 'role', None)
            
            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
                
            # Yetkisiz erişim denemesi
            if user_role == 'SHOP':
                return redirect('shop_dashboard')
            elif user_role == 'COURIER':
                return redirect('courier_dashboard')
            
            raise PermissionDenied("Bu işlem için yetkiniz bulunmamaktadır.")
        return _wrapped_view
    return decorator
