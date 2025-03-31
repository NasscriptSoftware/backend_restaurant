from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import DeliveryDriver, DeliveryOrder
from .serializers import DeliveryDriverSerializer, DeliveryOrderSerializer, DeliveryOrderUpdateSerializer
from restaurant_app.models import Order
from restaurant_app.serializers import OrderTypeChangeSerializer
from django.utils.dateparse import parse_date


class DeliveryDriverViewSet(viewsets.ModelViewSet):
    queryset = DeliveryDriver.objects.all()
    serializer_class = DeliveryDriverSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return DeliveryDriver.objects.filter(is_active=True)
        return DeliveryDriver.objects.filter(user=self.request.user)

    @action(detail=True, methods=["patch"])
    def toggle_active(self, request, pk=None):
        driver = self.get_object()
        driver.is_active = not driver.is_active
        driver.save()
        return Response({"status": "active status updated"})

    @action(detail=True, methods=["patch"])
    def toggle_available(self, request, pk=None):
        driver = self.get_object()

        # Check if the driver has any active orders before allowing them to become available
        active_orders = DeliveryOrder.objects.filter(
            driver=driver, status__in=["accepted", "in_progress"]
        )

        if active_orders.exists() and not driver.is_available:
            return Response(
                {"error": "Cannot set availability to True while having active orders"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        driver.is_available = not driver.is_available
        driver.save()
        return Response({"status": "availability status updated"})


class DeliveryOrderViewSet(viewsets.ModelViewSet):
    queryset = DeliveryOrder.objects.all()
    serializer_class = DeliveryOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return DeliveryOrder.objects.all()
        return DeliveryOrder.objects.filter(driver__user=self.request.user)

    @action(detail=True, methods=["patch"])
    def update_status(self, request, pk=None):
        delivery_order = self.get_object()
        new_status = request.data.get("status")
        if new_status in dict(DeliveryOrder.STATUS_CHOICES):
            old_status = delivery_order.status
            delivery_order.status = new_status
            delivery_order.save()

            # Update driver availability if status changes to 'accepted' or 'in_progress'
            if new_status in ["accepted", "in_progress"]:
                self.update_driver_availability(delivery_order.driver, False)

            # If status was 'accepted' or 'in_progress' and now it's not, check if driver can be made available
            elif old_status in ["accepted", "in_progress"] and new_status not in [
                "accepted",
                "in_progress",
            ]:
                self.check_and_update_driver_availability(delivery_order.driver)

            return Response({"status": "Delivery order status updated"})
        return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["patch"])
    def change_type(self, request, pk=None):
        """
        Change the order type and update delivery order information.
        """
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderTypeChangeSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            # Save the order type change and related fields
            order = serializer.save()

            # Update or create the corresponding delivery order
            delivery_data = request.data.get("delivery_order", {})
            if delivery_data:
                delivery_order, created = DeliveryOrder.objects.get_or_create(order=order)
                delivery_order_serializer = DeliveryOrderUpdateSerializer(
                    delivery_order, data=delivery_data, partial=True
                )
                if delivery_order_serializer.is_valid():
                    delivery_order_serializer.save()
                else:
                    return Response(delivery_order_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update_driver_availability(self, driver, is_available):
        if driver:
            driver.is_available = is_available
            driver.save()

    def check_and_update_driver_availability(self, driver):
        if driver:
            # Check if the driver has any other active orders
            active_orders = DeliveryOrder.objects.filter(
                driver=driver, status__in=["accepted", "in_progress"]
            ).exclude(id=self.get_object().id)

            if not active_orders.exists():
                driver.is_available = True
                driver.save()
    
    @action(detail=False, methods=['get'], url_path='driver-orders-report')
    def driver_orders_report(self, request):
        """
        Returns the list of orders for the current driver filtered by optional from_date and to_date.
        If no user is authenticated, returns an empty list.
        """
        if not request.user.is_authenticated:
            return Response([], status=status.HTTP_200_OK)

        try:
            delivery_driver = DeliveryDriver.objects.get(user=request.user)
        except DeliveryDriver.DoesNotExist:
            return Response([], status=status.HTTP_200_OK)

        delivery_orders = DeliveryOrder.objects.filter(driver=delivery_driver)
        
        # Extract query parameters
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')
        
        # Filter by from_date and to_date if provided
        if from_date:
            from_date_parsed = parse_date(from_date)
            delivery_orders = delivery_orders.filter(created_at__gte=from_date_parsed)
        if to_date:
            to_date_parsed = parse_date(to_date)
            delivery_orders = delivery_orders.filter(created_at__lte=to_date_parsed)
            
        # Serialize and return the filtered data
        serializer = self.get_serializer(delivery_orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
