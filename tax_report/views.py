from rest_framework import generics, response, status, views

from .models import Transaction
from .serializers import CreateTransactionsSerializer, TransactionSerializer


class CreateTransactionsAPIView(views.APIView):
    serializer_class = CreateTransactionsSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        results = serializer.save()
        serialized_response = TransactionSerializer(data=results, many=True)
        serialized_response.is_valid()
        return response.Response(
            data=serialized_response.data, status=status.HTTP_201_CREATED
        )


class ReportsAPIView(views.APIView):
    def get(self, request):
        return response.Response(
            data=Transaction.get_report(), status=status.HTTP_200_OK
        )
