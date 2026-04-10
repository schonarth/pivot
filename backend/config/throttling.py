from rest_framework.throttling import SimpleRateThrottle


class AuthenticatedRateThrottle(SimpleRateThrottle):
    scope = "authenticated"

    def get_rate(self):
        return "100/min"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return self.cache_format % {"scope": self.scope, "ident": request.user.pk}
        return None


class RefreshRateThrottle(SimpleRateThrottle):
    scope = "refresh"

    def get_rate(self):
        return "2/min"

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = f"{request.user.pk}"
            view = request.parser_context.get("kwargs", {})
            if "pk" in view:
                ident += f":{view['pk']}"
            return self.cache_format % {"scope": self.scope, "ident": ident}
        return None