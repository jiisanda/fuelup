from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


# Create your views here.
class OptimalRouteView(APIView):
    """
    API endpoint to calculate optimal route with fuel stops
    """

    def post(self, request, *args, **kwargs) -> Response:
        """
        POST method to calculate optimal route
        :param request: Expected input: {
            "start_location": "Start City, State",
            "end_location": "End City, State",
        }
        :return: Response with optimal route and fuel stops
        """
        start_location = request.data.get('start_location')
        end_location = request.data.get('end_location')

        # Validate input
        if not start_location or not end_location:
            return Response({
                "error": "Missing required fields: start_location, end_location"
            }, status=400)

        # Calculate optimal route with fuel stops
        optimal_route = self.calculate_optimal_route(start_location, end_location)

        return Response(
            {
                "optimal_route": optimal_route
            },
            status=status.HTTP_200_OK
        )

    def calculate_optimal_route(self, start_location: str, end_location: str):
        ...
