from django.shortcuts import redirect
from functools import wraps


def master_required(view_func):
    """
    Decorator: só superusuário acessa. Redireciona para login se não autenticado,
    ou para painel da empresa se autenticado mas não for superuser.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_superuser:
            return redirect('agendar_dia')
        return view_func(request, *args, **kwargs)
    return wrapper
