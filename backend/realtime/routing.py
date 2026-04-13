from django.urls import path
from .consumers import PortfolioConsumer

websocket_urlpatterns = [
    path("ws/portfolio/", PortfolioConsumer.as_asgi()),
]