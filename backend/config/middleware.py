import time

from django.db import connection

from .query_observability import QueryCapture, record_request_stat


class QueryObservabilityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        capture = QueryCapture()
        started_at = time.perf_counter()
        with connection.execute_wrapper(capture):
            response = self.get_response(request)

        record_request_stat(
            request.method,
            request.path,
            response.status_code,
            (time.perf_counter() - started_at) * 1000,
            capture.queries,
        )
        return response
