from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from restaurant_app.models import Order

User = get_user_model()


class DeliveryDriver(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="driver_profile"
    )
    is_active = models.BooleanField(default=False)
    is_available = models.BooleanField(default=False)

    class Meta:
        ordering = ("-is_active",)

    def __str__(self):
        return f"{self.user.username} - {'Active' if self.is_active else 'Inactive'}"


class DeliveryOrder(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("in_progress", "In Progress"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    )

    driver = models.ForeignKey(
        DeliveryDriver, on_delete=models.SET_NULL, null=True, related_name="orders"
    )
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="delivery_order"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)

    def __str__(self):
        return f"Order {self.id} - {self.status}"


@receiver(post_save, sender=Order)
def create_delivery_order(sender, instance, created, **kwargs):
    if instance.is_delivery_order():
        driver = None
        if not instance.is_scanned:
            driver = DeliveryDriver.objects.get(
                id=instance.delivery_driver_id
            )
            DeliveryOrder.objects.create(order=instance, driver=driver)
            instance.is_scanned = True
            instance.save()
