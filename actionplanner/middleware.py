from django.conf import settings
from django.shortcuts import redirect


class LoginRequiredMiddleware:
    EXEMPT_URLS = [
        settings.LOGIN_URL,
        "/admin/",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path_info
            if not any(path.startswith(url) for url in self.EXEMPT_URLS):
                return redirect(f"{settings.LOGIN_URL}?next={path}")
        return self.get_response(request)
