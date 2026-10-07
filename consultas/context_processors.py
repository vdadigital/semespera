def empresa_context(request):
    """Injeta a empresa do usuário logado em todos os templates."""
    if request.user.is_authenticated:
        try:
            return {'empresa': request.user.perfil.empresa}
        except Exception:
            pass
    return {'empresa': None}
