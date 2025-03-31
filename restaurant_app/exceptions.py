from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data['status_code'] = response.status_code

    return response


class InsufficientStockError(Exception):
    pass


def insufficient_stock_error_handler(exc, context):
    return Response({
        'error': 'Insufficient stock for one or more items in your order.',
        'status_code': status.HTTP_400_BAD_REQUEST
    }, status=status.HTTP_400_BAD_REQUEST)
