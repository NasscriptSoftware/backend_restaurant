from datetime import datetime, time, timedelta
from decimal import Decimal
from urllib import response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import TokenError, RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Avg, F, Value,DecimalField, IntegerField
from django.utils.dateparse import parse_date
from django.db.models import Q, Case, When
from django.db.models.functions import TruncDate, TruncHour, ExtractHour
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from delivery_drivers.models import DeliveryOrder
from delivery_drivers.serializers import DeliveryOrderSerializer
from restaurant_app.models import *
from restaurant_app.serializers import *
from rest_framework.decorators import api_view
from django.db.models.functions import Coalesce,Cast
from django.shortcuts import render
from rest_framework.pagination import PageNumberPagination
import win32print  # For Windows
# For Linux you would use: from cups import Connection
import tempfile
import os
from bs4 import BeautifulSoup

    
User = get_user_model()


def landing_page(request):
    return render(request, 'home.html')

class NoPagination(PageNumberPagination):
    page_size = 100  # Set a high number or limit

class SidebarItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SidebarItem.objects.all()  # Assuming SidebarItem is your model
    serializer_class = SidebarItemSerializer
    pagination_class = NoPagination


@staff_member_required
def toggle_sidebar_item_active(request, item_id):
    if request.method == 'POST':
        item = SidebarItem.objects.get(id=item_id)
        item.active = not item.active
        item.save()
        return JsonResponse({
            'success': True,
            'new_status': 'Active' if item.active else 'Inactive'
        })
    return JsonResponse({'success': False})


class LoginViewSet(viewsets.ModelViewSet, TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = (permissions.AllowAny,)
    http_method_names = ["post"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class PasscodeLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasscodeLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)

    @action(detail=False, methods=["post"])
    def logout(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"detail": "Successfully logged out"}, status=status.HTTP_200_OK
            )
        except TokenError as e:
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

# view set to change the logo info
class LogoInfoViewSet(viewsets.ModelViewSet):
    queryset = LogoInfo.objects.all()
    serializer_class = LogoInfoSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users in the system.

    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]
    pagination_class=None


class DishViewSet(viewsets.ModelViewSet):
    queryset = Dish.objects.all()
    serializer_class = DishSerializer
    pagination_class = None
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "price"]


class DishSizeViewSet(viewsets.ModelViewSet):
    queryset = DishSize.objects.all()
    serializer_class = DishSizeSerializer


class DishVariantViewSet(viewsets.ModelViewSet):
    queryset = DishVariant.objects.all()
    serializer_class = DishVariantSerializer

    def get_queryset(self):
        queryset = DishVariant.objects.all()
        dish_id = self.request.query_params.get('dish_id')
        
        if dish_id is not None:
            queryset = queryset.filter(dish_id=dish_id)
        
        return queryset


class OnlineOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing OnlineOrder data.

    This ViewSet provides CRUD operations (Create, Read, Update, Delete) for the `OnlineOrder` model.
    It is primarily used by third-party online order platforms like Zomato, Swiggy, etc., to integrate 
    and manage order data in the system.

    """
    queryset = OnlineOrder.objects.all()    
    serializer_class = OnlineOrderSerializer
    pagination_class = None


class CustomerDetailsViewSet(viewsets.ModelViewSet):
    queryset = CustomerDetails.objects.all()
    serializer_class = CustomerDetailsSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        order_type = self.request.query_params.get("order_type", None)
        if order_type:
            queryset = queryset.filter(order_type=order_type)
        return queryset

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def cancel_order(self, request, pk=None):
        order = self.get_object()
        if order.status == 'delivered':
            return Response({"detail": "Delivered orders cannot be cancelled."}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = 'cancelled'
        order.save()
        return Response({"detail": "Order has been cancelled."}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


    @action(detail=True, methods=['delete'], url_path='remove-item/(?P<item_id>[^/.]+)')
    def remove_item(self, request, pk=None, item_id=None):
        try:
            order = self.get_object()  # Retrieve the order
            order_item = OrderItem.objects.get(id=item_id, order=order)  # Find the item in this order

            # Check if this is the last item in the order
            if order.items.count() == 1:
                # If it's the last item, delete the entire order
                order.delete()
                return Response({"message": "Order deleted as it was the last item."}, status=status.HTTP_200_OK)
            else:
                # If it's not the last item, just delete the order item
                order_item.delete()

            # Recalculate the order total
            order.recalculate_total()

            return Response({"message": "Order item removed successfully."}, status=status.HTTP_200_OK)

        except OrderItem.DoesNotExist:
            return Response({"error": "Order item not found."}, status=status.HTTP_404_NOT_FOUND)

    def get_queryset_by_time_range(self, time_range):
        end_date = timezone.now()
        if time_range == "day":
            start_date = end_date - timedelta(days=1)
        elif time_range == "week":
            start_date = end_date - timedelta(weeks=1)
        elif time_range == "month":
            start_date = end_date - timedelta(days=30)
        elif time_range == "year":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)

        return self.queryset.filter(created_at__range=(start_date, end_date))
    
    @action(detail=False, methods=["get"])
    def user_order_history(self, request):
        customer_phone_number = request.query_params.get("customer_phone_number", None)
        
        # Initialize queryset
        queryset = self.get_queryset()
        
        # If customer_phone_number is provided, filter the queryset
        if customer_phone_number:
            queryset = queryset.filter(customer_phone_number=customer_phone_number)
        else:
            # Return an empty queryset if no customer_phone_number is provided
            queryset = queryset.none()
        
        # Serialize and return the response
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def sales_report(self, request):
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")
        order_type = request.query_params.get("order_type")
        payment_method = request.query_params.get("payment_method")
        status = request.query_params.get("order_status")

        from_date = parse_date(from_date) if from_date else None
        to_date = parse_date(to_date) if to_date else None

        queryset = self.get_queryset()

        # Apply date filters if provided
        if from_date and to_date:
            queryset = queryset.filter(
                created_at__date__gte=from_date, created_at__date__lte=to_date
            )
        elif from_date:
            queryset = queryset.filter(created_at__date__gte=from_date)
        elif to_date:
            queryset = queryset.filter(created_at__date__lte=to_date)

        # Apply additional filters based on query parameters
        if order_type:
            queryset = queryset.filter(order_type=order_type)
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        if status:
            queryset = queryset.filter(status=status)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def dashboard_data(self, request):
        time_range = request.query_params.get('time_range', 'week')
        today = timezone.now().date()

        # Set date range based on time_range parameter
        if time_range == 'day':
            start_date = today
            previous_start_date = today - timedelta(days=1)
            previous_end_date = previous_start_date
        elif time_range == 'week':
            # Current week: last 7 days including today
            start_date = today - timedelta(days=6)
            # Previous week: 7 days before the current period
            previous_end_date = start_date - timedelta(days=1)
            previous_start_date = previous_end_date - timedelta(days=6)
        elif time_range == 'month':
            # Get start of current month
            start_date = today.replace(day=1)
            # Previous month calculation
            last_day_of_prev_month = start_date - timedelta(days=1)
            previous_start_date = last_day_of_prev_month.replace(day=1)
            previous_end_date = last_day_of_prev_month
        else:  # year
            # Get start of current year
            start_date = today.replace(month=1, day=1)
            previous_start_date = start_date.replace(year=start_date.year-1)
            previous_end_date = today.replace(year=today.year-1)

        print(f"Current period - Time range: {time_range}, Start: {start_date}, End: {today}")
        print(f"Previous period - Start: {previous_start_date}, End: {previous_end_date}")

        # Base queryset for the date range - only delivered orders
        orders = Order.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=today,
            status='delivered'  # Only consider delivered orders
        )
        
        order_items = OrderItem.objects.filter(
            order__created_at__date__gte=start_date,
            order__created_at__date__lte=today,
            order__status='delivered'  # Only consider items from delivered orders
        )

        # Calculate metrics for delivered orders only
        total_income = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        total_orders = orders.count()
        avg_order_value = total_income / total_orders if total_orders > 0 else 0

        # Top dishes from delivered orders
        top_dishes = (
            order_items
            .values('dish_name')
            .annotate(
                orders=Count('id'),
                total_sales=Sum(F('price') * F('quantity'))
            )
            .annotate(
                name=F('dish_name')
            )   
            .order_by('-orders')[:5]
        )

        # Category sales from delivered orders
        category_sales = (
            order_items
            .values('dish_name')
            .annotate(
                value=Sum(F('price') * F('quantity'))
            )
            .order_by('-value')[:5]
        )

        # Popular time slots for delivered orders
        popular_time_slots = (
            orders
            .annotate(hour=ExtractHour('created_at'))
            .values('hour')
            .annotate(order_count=Count('id'))
            .order_by('-order_count')[:5]
        )

        # Daily sales data for delivered orders
        daily_sales = []
        current_date = start_date
        while current_date <= today:
            day_orders = orders.filter(created_at__date=current_date)
            daily_sales.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'total_sales': day_orders.aggregate(total=Sum('total_amount'))['total'] or 0,
                'order_count': day_orders.count()
            })
            current_date += timedelta(days=1)

        # Previous period orders
        previous_orders = Order.objects.filter(
            created_at__date__gte=previous_start_date,
            created_at__date__lte=previous_end_date,
            status='delivered'
        )

        previous_total_income = previous_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        previous_total_orders = previous_orders.count()
        previous_avg_order = previous_total_income / previous_total_orders if previous_total_orders > 0 else 0

        # Calculate percentage changes
        def calculate_trend(current, previous):
            if previous and previous != 0:
                return ((current - previous) / previous * 100)
            return 0
        
        total_income_trend = calculate_trend(total_income, previous_total_income)
        total_orders_trend = calculate_trend(total_orders, previous_total_orders)
        avg_order_trend = calculate_trend(avg_order_value, previous_avg_order)
        
        return Response({
            'total_income': total_income,
            'total_orders': total_orders,
            'avg_order_value': avg_order_value,
            'popular_time_slots': popular_time_slots,
            'daily_sales': daily_sales,
            'top_dishes': top_dishes,
            'category_sales': category_sales,
            'total_income_trend': total_income_trend,
            'total_orders_trend': total_orders_trend,
            'avg_order_value_trend': avg_order_trend,
            'previous_period': {
                'start_date': previous_start_date.strftime('%Y-%m-%d'),
                'end_date': previous_end_date.strftime('%Y-%m-%d'),
                'total_income': previous_total_income,
                'total_orders': previous_total_orders,
                'avg_order_value': previous_avg_order
            }
        })

    @action(detail=False, methods=["get"])
    def sales_trends(self, request):
        time_range = request.query_params.get("time_range", "month")
        today = timezone.now().date()
        
        # Set date ranges using the same logic as dashboard_data
        if time_range == 'day':
            start_date = today
            previous_start_date = today - timedelta(days=1)
            previous_end_date = previous_start_date
        elif time_range == 'week':
            # Current week: last 7 days including today
            start_date = today - timedelta(days=6)
            # Previous week: 7 days before the current period
            previous_end_date = start_date - timedelta(days=1)
            previous_start_date = previous_end_date - timedelta(days=6)
        elif time_range == 'month':
            start_date = today.replace(day=1)
            last_day_of_prev_month = start_date - timedelta(days=1)
            previous_start_date = last_day_of_prev_month.replace(day=1)
            previous_end_date = last_day_of_prev_month
        else:  # year
            start_date = today.replace(month=1, day=1)
            previous_start_date = start_date.replace(year=start_date.year-1)
            previous_end_date = today.replace(year=today.year-1)

        print(f"Current period - Time range: {time_range}, Start: {start_date}, End: {today}")
        print(f"Previous period - Start: {previous_start_date}, End: {previous_end_date}")

        current_queryset = self.queryset.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=today,
            status='delivered'
        )
        
        prev_queryset = self.queryset.filter(
            created_at__date__gte=previous_start_date,
            created_at__date__lte=previous_end_date,
            status='delivered'
        )

        current_stats = current_queryset.aggregate(
            total_income=Sum("total_amount"),
            total_orders=Count("id"),
            avg_order_value=Avg("total_amount"),
        )

        prev_stats = prev_queryset.aggregate(
            total_income=Sum("total_amount"),
            total_orders=Count("id"),
            avg_order_value=Avg("total_amount"),
        )

        def calculate_trend(current, previous):
            if previous and previous != 0:
                return ((current - previous) / previous) * 100
            return 0

        trends = {
            "total_income_trend": calculate_trend(
                current_stats["total_income"] or 0, prev_stats["total_income"] or 0
            ),
            "total_orders_trend": calculate_trend(
                current_stats["total_orders"] or 0, prev_stats["total_orders"] or 0
            ),
            "avg_order_value_trend": calculate_trend(
                current_stats["avg_order_value"] or 0,
                prev_stats["avg_order_value"] or 0,
            ),
        }
        
        # Return the response with all trend data
        return Response({
            "current_period": {
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": today.strftime('%Y-%m-%d'),
                "total_income": current_stats["total_income"] or 0,
                "total_orders": current_stats["total_orders"] or 0,
                "avg_order_value": current_stats["avg_order_value"] or 0,
            },
            "previous_period": {
                "start_date": previous_start_date.strftime('%Y-%m-%d'),
                "end_date": previous_end_date.strftime('%Y-%m-%d'),
                "total_income": prev_stats["total_income"] or 0, 
                "total_orders": prev_stats["total_orders"] or 0,
                "avg_order_value": prev_stats["avg_order_value"] or 0,
            },
            "trends": trends
        })

    @action(detail=False, methods=['get'])
    def product_wise_report(self, request):
        try:
            # Get parameters from request
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')
            dish_name = request.query_params.get('dish_name')
            
            # Base query for OrderItems
            query = OrderItem.objects.all()
            
            # Apply filters
            if from_date and to_date:
                query = query.filter(
                    order__created_at__date__range=[from_date, to_date]
                )
            
            # Filter by dish_name if provided
            if dish_name:
                query = query.filter(dish_name=dish_name)

            # Rest of the aggregation logic remains the same
            product_report = query.values(
                'dish_name',
                'order__invoice_number',
                'order__created_at',
                'order__order_type',
                'order__payment_method'
            ).annotate(
                total_quantity=Sum('quantity'),
                total_amount=Sum(F('price') * F('quantity')),
                cash_amount=Case(
                    When(order__payment_method='cash', then=F('price') * F('quantity')),
                    default=Value(0),
                    output_field=DecimalField()
                ),
                bank_amount=Case(
                    When(order__payment_method='bank', then=F('price') * F('quantity')),
                    default=Value(0),
                    output_field=DecimalField()
                ),
                credit_amount=Case(
                    When(order__payment_method='credit', then=F('price') * F('quantity')),
                    default=Value(0),
                    output_field=DecimalField()
                )
            ).order_by('dish_name')

            # Format the response
            formatted_report = [{
                'dish_name': item['dish_name'],
                'total_quantity': item['total_quantity'],
                'total_amount': str(item['total_amount']),
                'invoice_number': item['order__invoice_number'],
                'order_created_at': item['order__created_at'],
                'order_type': item['order__order_type'],
                'payment_method': item['order__payment_method'],
                'cash_amount': str(item['cash_amount']),
                'bank_amount': str(item['bank_amount']),
                'credit_amount': str(item['credit_amount'])
            } for item in product_report]

            return Response(formatted_report)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['GET'], url_path='online-delivery-report')
    def online_delivery_report(self, request):
        """
        Retrieve a report of online delivery orders, filtered by date range and/or online platform ID.
        """
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        online_order_id = request.query_params.get('online_order_id')

        # Start with base query
        orders = self.queryset.filter(order_type='onlinedelivery')

        # Apply date filters if provided
        if from_date and to_date:
            orders = orders.filter(
                created_at__date__gte=from_date,
                created_at__date__lte=to_date
            )

        # Apply online platform filter if provided
        if online_order_id:
            orders = orders.filter(online_order_id=online_order_id)

        # Select related to avoid N+1 queries
        orders = orders.select_related('online_order')

        report_data = []
        for order in orders:
            percentage = order.online_order.percentage if order.online_order else 0
            total_amount = order.total_amount

            # Calculate percentage_amount and balance_amount
            percentage_amount = (percentage / 100) * total_amount if percentage > 0 else 0
            balance_amount = total_amount - percentage_amount

            report_data.append({
                'onlineordername': order.online_order.name if order.online_order else None,
                'percentage': percentage,
                'invoice': order.invoice_number,
                'date': order.created_at.date(),
                'order_type': order.order_type,
                'payment_method': order.payment_method,
                'order_status': order.status,
                'total_amount': total_amount,
                'percentage_amount': percentage_amount,
                'balance_amount': balance_amount,
            })

        return Response(report_data)
    
    @action(detail=False, methods=['GET'], url_path='staff-user-order-report')
    def staff_user_order_report(self, request):
        """
        Retrieve all orders placed by staff users, optionally filtered by date range.
        """
        return self._get_staff_orders(request)

    @action(detail=True, methods=['GET'], url_path='staff-user-order-report')
    def staff_user_order_report_detail(self, request, pk=None):
        """
        Retrieve orders for a specific staff user, optionally filtered by date range.
        """
        return self._get_staff_orders(request, pk)

    def _get_staff_orders(self, request, pk=None):
        """
        Helper method to get staff orders, either for all staff or a specific staff member.
        """
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        
        if pk:
            try:
                # Check for both staff and admin roles
                user = User.objects.get(
                    pk=pk,
                    role__in=['staff', 'admin']  # Allow both staff and admin roles
                )
                orders = Order.objects.filter(user=user)
            except User.DoesNotExist:
                return Response({'error': 'Staff/Admin user not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Filter orders by all staff and admin users
            orders = Order.objects.filter(user__role__in=['staff', 'admin'])

        # Apply date filtering if provided
        if from_date:
            from_date_parsed = parse_date(from_date)
            if from_date_parsed:
                orders = orders.filter(created_at__date__gte=from_date_parsed)

        if to_date:
            to_date_parsed = parse_date(to_date)
            if to_date_parsed:
                orders = orders.filter(created_at__date__lte=to_date_parsed)

        # Only prefetch items since dish is no longer a relationship
        orders = orders.prefetch_related('items')
        
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'], url_path='driver-report')
    def driver_report_list(self, request):
        """
        Retrieve a report of orders for all drivers or filtered by date range.
        """
        return self._generate_driver_report(request)

    @action(detail=True, methods=['GET'], url_path='driver-report')
    def driver_report_detail(self, request, pk=None):
        """
        Retrieve a report of orders for a specific driver.
        """
        return self._generate_driver_report(request, driver_id=pk)

    def _generate_driver_report(self, request, driver_id=None):
        """
        Helper method to generate driver report for both list and detail views.
        """
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        delivery_driver_id = request.query_params.get('delivery_driver_id') or driver_id

        # Start with all delivery orders
        orders = self.queryset.filter(order_type='delivery')

        # Apply driver filter if provided
        if delivery_driver_id:
            orders = orders.filter(delivery_driver_id=delivery_driver_id)
            print(f"Filtering for driver ID: {delivery_driver_id}")  # Add this log
        else:
            print("No driver ID provided, returning all delivery orders")  # Add this log

        # Apply date range filter if provided
        if from_date:
            from_date = parse_date(from_date)
            orders = orders.filter(created_at__date__gte=from_date)
        if to_date:
            to_date = parse_date(to_date)
            orders = orders.filter(created_at__date__lte=to_date)

        # Select the fields we need
        report_data = orders.values(
            'id',
            'invoice_number',
            'customer_name',
            'address',
            'payment_method',
            'total_amount',
            'bank_amount',
            'cash_amount',
            'delivery_charge',
            'delivery_driver_id',
            'credit_amount'
        )

        print(f"Number of orders in report: {len(report_data)}")  # Add this log

        return Response(list(report_data))


class OrderStatusUpdateViewSet(viewsets.GenericViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderStatusUpdateSerializer

    def partial_update(self, request, pk=None):
        try:
            order = self.get_object()
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            # Handle online delivery specific logic
            if request.data.get('order_type') == 'onlinedelivery':
                if not request.data.get('online_order'):
                    return Response(
                        {"error": "online_order is required for online delivery orders"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            updated_order = serializer.save()

            # Handle credit payment method
            if updated_order.payment_method == "credit":
                credit_user_id = updated_order.credit_user_id
                try:
                    credit_user = CreditUser.objects.get(pk=credit_user_id)
                except CreditUser.DoesNotExist:
                    return Response(
                        {"error": "Invalid credit user"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if not credit_user.is_active:
                    return Response(
                        {"error": "Credit user account is inactive due to overdue payment"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                CreditOrder.objects.get_or_create(order=updated_order, credit_user=credit_user)
                credit_user.add_to_total_due(updated_order.total_amount)

            return Response({"detail": "Order updated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# view for changing the order type

class OrderTypeChangeViewSet(viewsets.ViewSet):

    @action(detail=True, methods=['put'], url_path='change-type')
    def change_order_type(self, request, pk=None):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderTypeChangeSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            order = serializer.save()

            # Handle the creation or update of DeliveryOrder
            if order.order_type == 'delivery':
                delivery_order, created = DeliveryOrder.objects.get_or_create(order=order)
                delivery_order.driver_id = serializer.validated_data.get('delivery_driver_id')
                delivery_order.status = request.data.get('delivery_order_status', 'pending')
                delivery_order.save()

                # Include the DeliveryOrder details in the response
                delivery_order_serializer = DeliveryOrderSerializer(delivery_order)
                response_data = serializer.data
                response_data['delivery_order'] = delivery_order_serializer.data

                return Response(response_data, status=status.HTTP_200_OK)

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def partial_update(self, request, *args, **kwargs):
        order_item = self.get_object()
        
        # Check if the associated order is already delivered
        if order_item.order.status == "delivered":
            return Response(
                {"error": "Cannot modify items of delivered orders"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the price
        serializer = self.get_serializer(order_item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Recalculate the order total
            order_item.order.recalculate_total()
            
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class BillViewSet(viewsets.ModelViewSet):
    queryset = Bill.objects.all()
    serializer_class = BillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')  # Get the status from query params
        if status_param:
            queryset = queryset.filter(order__status=status_param)  # Filter based on order status
        return queryset



class CancelOrderByBillView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, bill_id=None):
        try:
            # Get the bill instance by primary key (bill_id)
            bill = Bill.objects.get(pk=bill_id)
            order = bill.order

            # Check if the order is already canceled
            if order.status == 'cancelled':
                return Response({"detail": "Order is already cancelled."}, status=status.HTTP_400_BAD_REQUEST)

            # Change the status of the order to 'cancelled'
            order.status = "cancelled"
            order.save()

            # Ensure the bill remains unaffected by this change
            bill.save()  # This might be redundant, ensure you don't trigger a new save unintentionally.

            # Return a response indicating the order was cancelled
            return Response({"detail": "Order status updated to cancelled."}, status=status.HTTP_200_OK)

        except Bill.DoesNotExist:
            return Response({"detail": "Bill not found."}, status=status.HTTP_404_NOT_FOUND)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)




class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by("-created_at")
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"status": "notification marked as read"})

    @action(detail=False, methods=["get"])
    def unread(self, request):
        unread_notifications = self.queryset.filter(is_read=False)
        serializer = self.get_serializer(unread_notifications, many=True)
        return Response(serializer.data)


class FloorViewSet(viewsets.ModelViewSet):
    queryset = Floor.objects.all()
    serializer_class = FloorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        names = [item["name"] for item in serializer.data]
        return Response(names)


class TableViewSet(viewsets.ModelViewSet):
    serializer_class = TableSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Table.objects.all()
        floor = self.request.query_params.get("floor")
        if floor:
            queryset = queryset.filter(floor__name=floor)
        return queryset



class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MessTypeViewSet(viewsets.ModelViewSet):
    queryset = MessType.objects.all()
    serializer_class = MessTypeSerializer


class MenuViewSet(viewsets.ModelViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["mess_type", "is_custom", "created_by"]
    search_fields = ["name", "created_by"]

    def get_queryset(self):
        queryset = super().get_queryset()
        mess_type = self.request.query_params.get("mess_type")
        is_custom = self.request.query_params.get("is_custom")
        created_by = self.request.query_params.get("created_by")

        if mess_type:
            try:
                mess_type = int(mess_type)
                queryset = queryset.filter(mess_type=mess_type)
            except ValueError:
                raise ValueError("mess_type should be a number")

        if is_custom is not None:
            is_custom_bool = is_custom.lower() == "true"
            queryset = queryset.filter(is_custom=is_custom_bool)

        if created_by:
            queryset = queryset.filter(created_by=created_by)

        return queryset
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mess = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        mess = serializer.save()
        return Response(serializer.data)
    

class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer


class MessViewSet(viewsets.ModelViewSet):
    queryset = Mess.objects.all()
    serializer_class = MessSerializer

    def create(self, request, *args, **kwargs):
        # Ensure no `id` is included in the creation data
        data = request.data.copy()
        data.pop("id", None)  # Remove `id` if present

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(detail=False, methods=["get"])
    def mess_report(self, request):
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")
        payment_method = request.query_params.get("payment_method")
        credit = request.query_params.get("credit")
        mess_type_name = request.query_params.get("mess_type")

        # Convert to datetime objects for filtering
        from_date = parse_date(from_date) if from_date else None
        to_date = parse_date(to_date) if to_date else None
        print("from :", from_date, "to :", to_date)

        queryset = self.get_queryset()

        if from_date and to_date:
            queryset = queryset.filter(
                Q(start_date__gte=from_date) & Q(end_date__lte=to_date))
        elif from_date:
            queryset = queryset.filter(start_date__gte=from_date)
        elif to_date:
            queryset = queryset.filter(end_date__lte=to_date)
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        if credit:
            queryset = queryset.filter(pending_amount__gt=0)
        if mess_type_name:
            try:
                mess_type_instance = MessType.objects.get(name=mess_type_name)
                mess_type_id = mess_type_instance.id
                queryset = queryset.filter(mess_type=mess_type_id)
            except MessType.DoesNotExist:
                return Response({"detail": "Invalid mess_type"}, status=400)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SearchDishesAPIView(APIView):
    def get(self, request):
        query = request.GET.get("search", "")
        if query:
            dishes = Dish.objects.filter(name__icontains=query)
            serializer = DishSerializer(dishes, many=True)
            return Response({"results": serializer.data}, status=status.HTTP_200_OK)
        return Response({"results": []}, status=status.HTTP_200_OK)


class CreditUserViewSet(viewsets.ModelViewSet):
    queryset = CreditUser.objects.all()
    serializer_class = CreditUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["get"])
    def get_active_users(self, request, pk=None):
        active_users = CreditUser.objects.filter(is_active=True)
        serializer = self.get_serializer(active_users, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def make_payment(self, request, pk=None):
        credit_user = self.get_object()
        amount = Decimal(request.data.get("payment_amount", 0))

        if amount <= 0:
            return Response(
                {"error": "Invalid payment amount"}, status=status.HTTP_400_BAD_REQUEST
            )

        credit_user.make_payment(amount)
        return Response(CreditUserSerializer(credit_user).data)

    @action(detail=False, methods=["get"], url_path='find-user')
    def find_user(self, request):
        mobile_number = request.query_params.get('mobile_number', None)     
        
        if not mobile_number:
            return Response(
                {"error": "Mobile number is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Attempt to retrieve the user by mobile number
            user = CreditUser.objects.get(mobile_number=mobile_number)
            
            # Check if the user is active
            if user.is_active:
                serializer = self.get_serializer(user)
                return Response({"data": serializer.data}, status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": "The given user is not active."}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        except CreditUser.DoesNotExist:
            return Response(
                {"error": "No credit user found with this mobile number."}, 
                status=status.HTTP_404_NOT_FOUND
            )


class CreditOrderViewSet(viewsets.ModelViewSet):
    queryset = CreditOrder.objects.all()
    serializer_class = CreditOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

class MessTransactionViewSet(viewsets.ModelViewSet):
    queryset = MessTransaction.objects.all()
    serializer_class = MessTransactionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        mess_id = self.request.query_params.get('mess_id', None)
        if mess_id is not None:
            queryset = queryset.filter(mess_id=mess_id)
        return queryset

class CreditTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = CreditTransactionSerializer
    queryset = CreditTransaction.objects.all()

    
    def get_queryset(self):
        queryset = CreditTransaction.objects.all()
        credit_user_id = self.request.query_params.get('credit_user', None)
        if credit_user_id is not None:
            queryset = queryset.filter(credit_user_id=credit_user_id)
        return queryset
    
    @action(detail=False, methods=['get'])
    def latest_transaction(self, request):
        credit_user_id = request.query_params.get('credit_user', None)
        if not credit_user_id:
            return Response({"error": "credit_user parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the latest transaction based on both date and time
        try:
            latest_transaction = CreditTransaction.objects.filter(credit_user_id=credit_user_id).order_by('-date', '-id').first()
            if not latest_transaction:
                return Response({"error": "No transactions found for the given credit_user"}, status=status.HTTP_404_NOT_FOUND)
            
            serializer = self.get_serializer(latest_transaction)
            return Response(serializer.data)
        except CreditTransaction.DoesNotExist:
            return Response({"error": "No transactions found for the given credit_user"}, status=status.HTTP_404_NOT_FOUND)


from .models import Chairs
from .serializers import ChairsSerializer

class ChairsViewSet(viewsets.ModelViewSet):
    """
    A ModelViewSet for managing chair bookings.

    Use Case:
    ---------
    This view is particularly useful for systems or apps that handle chair 
    reservations or bookings for customers, such as for events, restaurants, 
    or conferences. It allows easy integration with APIs for creating, 
    updating, or retrieving chair booking information.

    Endpoints:
    ----------
    - GET /chairs/ : List all chair bookings.
    - GET /chairs/<id>/ : Retrieve a single chair booking.
    - POST /chairs/ : Create a new chair booking.
    - PUT /chairs/<id>/ : Update a chair booking.
    - DELETE /chairs/<id>/ : Delete a chair booking.

    """
    queryset = Chairs.objects.all()
    serializer_class = ChairsSerializer
    pagination_class = None


class FOCProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for FOCProduct model.

    Provides basic CRUD operations for managing free of cost products (FOCProduct).
    
    Actions:
    --------
    - list: Retrieve all free of cost products.
    - create: Add a new free of cost product.
    - retrieve: Get a specific free of cost product by its ID.
    - update: Update an existing free of cost product.
    - partial_update: Partially update an existing free of cost product.
    - destroy: Delete a free of cost product.
    """
    queryset = FOCProduct.objects.all()
    serializer_class = FOCProductSerializer
    pagination_class = None

class ChairBookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chair bookings.
    
    Provides CRUD operations for chair bookings with additional endpoints for:
    - Checking availability
    - Confirming bookings
    - Cancelling bookings
    """
    queryset = ChairBooking.objects.all()
    serializer_class = ChairBookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    
    def get_queryset(self):
        queryset = ChairBooking.objects.all()
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        
        if from_date and to_date:
            # Convert string dates to datetime objects
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
            queryset = queryset.filter(booked_date__range=[from_date, to_date])
        
        return queryset.order_by('-booked_date', '-start_time')
    
    @action(detail=False, methods=['GET'])
    def check_availability(self, request):
        """
        Check chair availability for a given time period.
        """
        chair_id = request.query_params.get('chair_id')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        
        if not all([chair_id, start_time, end_time]):
            return Response(
                {"error": "chair_id, start_time, and end_time are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            start_time = parse_datetime(start_time)
            end_time = parse_datetime(end_time)
        except ValueError:
            return Response(
                {"error": "Invalid datetime format"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        overlapping_bookings = ChairBooking.objects.filter(
            selected_chair_id=chair_id,
            status='confirmed',
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        
        is_available = not overlapping_bookings.exists()
        
        return Response({
            "is_available": is_available,
            "conflicting_bookings": ChairBookingSerializer(
                overlapping_bookings, 
                many=True
            ).data if not is_available else []
        })
    
    @action(detail=True, methods=['POST'])
    def confirm_booking(self, request, pk=None):
        """
        Confirm a pending booking.
        """
        booking = self.get_object()
        if booking.status != 'pending':
            return Response(
                {"error": "Only pending bookings can be confirmed"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        booking.status = 'confirmed'
        booking.save()
        
        return Response(ChairBookingSerializer(booking).data)
    
    @action(detail=True, methods=['POST'])
    def cancel_booking(self, request, pk=None):
        """
        Cancel a booking.
        """
        booking = self.get_object()
        if booking.status == 'completed':
            return Response(
                {"error": "Completed bookings cannot be cancelled"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        booking.status = 'cancelled'
        booking.save()
        
        return Response(ChairBookingSerializer(booking).data)

    def partial_update(self, request, *args, **kwargs):
        """
        Handle PATCH requests to update booking status
        """
        booking = self.get_object()
        new_status = request.data.get('status')
        
        # Validate status transitions
        if booking.status == 'completed' and new_status != 'completed':
            return Response(
                {"error": "Completed bookings cannot be changed"},
                status=status.HTTP_400_BAD_REQUEST
            )            
        if booking.status == 'cancelled' and new_status not in ['pending', 'cancelled']:
            return Response(
                {"error": "Cancelled bookings can only be set to pending"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().partial_update(request, *args, **kwargs)

class PrintViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['POST'])
    def print_receipt(self, request):
        try:
            printer_type = request.data.get('type')
            html_content = request.data.get('content', '')
            
            # Map printer types to printer names
            printer_mapping = {
                'pizza': 'kitchenprint',
                'shawarma': 'kitchenprint',
                'kitchen': 'kitchenprint',
                'sales': 'salesprint'
            }
            # printer_mapping = {
            #     'pizza': 'pizzaprint',
            #     'shawarma': 'shawarmaprint',
            #     'kitchen': 'kitchenprint',
            #     'sales': 'salesprint'
            # }
            
            # Get the correct printer name based on type
            printer_name = printer_mapping.get(printer_type)
            if not printer_name:
                return JsonResponse({
                    'success': False,
                    'error': f"Invalid printer type: '{printer_type}'"
                }, status=400)

            # Convert HTML to plain text and format
            soup = BeautifulSoup(html_content, 'html.parser')
            formatted_content = self.format_content(soup, printer_type)

            # Print the content
            self.print_to_printer(printer_name, formatted_content)

            return JsonResponse({'success': True})
            
        except Exception as e:
            logger.exception("Error in print_receipt")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    def format_content(self, soup, printer_type):
        formatted_content = ""
        
        # Add headers based on printer type
        if printer_type == 'pizza':
            formatted_content += "\n" + "="*32 + "\n"
            formatted_content += "PIZZA ORDER".center(32) + "\n"
            formatted_content += "="*32 + "\n\n"
        elif printer_type == 'shawarma':
            formatted_content += "\n" + "="*32 + "\n"
            formatted_content += "SHAWARMA ORDER".center(32) + "\n"
            formatted_content += "="*32 + "\n\n"
        elif printer_type == 'kitchen':
            formatted_content += "\n" + "="*32 + "\n"
            formatted_content += "KITCHEN ORDER".center(32) + "\n"
            formatted_content += "="*32 + "\n\n"
        elif printer_type == 'sales':
            formatted_content += "\n" + "="*32 + "\n"
            formatted_content += "SALES RECEIPT".center(32) + "\n"
            formatted_content += "="*32 + "\n\n"

        # Process each line with proper formatting
        for element in soup.stripped_strings:
            line = str(element).strip()
            if line:
                if 'QAR' in line or any(c.isdigit() for c in line):
                    formatted_content += line.rjust(32) + "\n"
                else:
                    formatted_content += line.ljust(32) + "\n"
                
                if line.startswith('='):
                    formatted_content += "\n"

        # Add footer
        formatted_content += "\n" + "="*32 + "\n"
        
        return formatted_content

    def print_to_printer(self, printer_name, content):
        # Create temporary file with content
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        try:
            # Windows printing
            printer_handle = win32print.OpenPrinter(printer_name)
            try:
                job = win32print.StartDocPrinter(printer_handle, 1, ("Receipt", None, "RAW"))
                try:
                    win32print.StartPagePrinter(printer_handle)
                    with open(temp_path, 'rb') as f:
                        win32print.WritePrinter(printer_handle, f.read())
                    win32print.EndPagePrinter(printer_handle)
                finally:
                    win32print.EndDocPrinter(printer_handle)
            finally:
                win32print.ClosePrinter(printer_handle)
        finally:
            # Clean up temp file
            os.unlink(temp_path)
