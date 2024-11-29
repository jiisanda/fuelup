from django.urls import path

from fuel_route.views import OptimalRouteView, HomePageView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('optimal-route/', OptimalRouteView.as_view(), name='optimal_route'),
]
