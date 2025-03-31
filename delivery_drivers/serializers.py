from rest_framework import serializers
from .models import DeliveryDriver, DeliveryOrder
from restaurant_app.serializers import OrderSerializer

class DeliveryDriverSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    mobile_number = serializers.CharField(source="user.mobile_number", read_only=True)

    class Meta:
        model = DeliveryDriver
        fields = ["id", "username", "email", "mobile_number", "is_active", "is_available"]


class DeliveryOrderSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(source="driver.user.username", read_only=True)
    order = OrderSerializer()

    class Meta:
        model = DeliveryOrder
        fields = [
            "id",
            "driver",
            "driver_name",
            "status",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

class DeliveryOrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryOrder
        fields = ["status", "driver"]
        extra_kwargs = {
            "status": {"required": False},
            "driver": {"required": False},
        }

class OrderTypeChangeSerializer(serializers.ModelSerializer):
    delivery_order_status = serializers.CharField(write_only=True, required=False)
    delivery_driver_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = DeliveryOrder  # Or Order if this is the main order serializer
        fields = [
            "order_type",
            "customer_name",
            "address",
            "customer_phone_number",
            "delivery_charge",
            "delivery_order_status",
            "delivery_driver_id",
        ]

    def update(self, instance, validated_data):
        delivery_order_status = validated_data.pop('delivery_order_status', None)
        delivery_driver_id = validated_data.pop('delivery_driver_id', None)
        
        if delivery_driver_id:
            driver = DeliveryDriver.objects.get(id=delivery_driver_id)
            instance.delivery_order.driver = driver
        
        if delivery_order_status:
            instance.delivery_order.status = delivery_order_status
        
        instance.delivery_order.save()
        return super().update(instance, validated_data)
