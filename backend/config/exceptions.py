from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None:
        detail = exc.detail if hasattr(exc, "detail") else str(exc)
        if isinstance(detail, dict):
            response.data = {"error": detail}
        elif isinstance(detail, list):
            response.data = {"error": {"code": "validation_error", "message": detail}}
        else:
            response.data = {"error": {"code": getattr(exc, "default_code", "error"), "message": str(detail)}}
    return response