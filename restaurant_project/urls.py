from rest_framework.routers import DefaultRouter
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from rest_framework_simplejwt.views import TokenRefreshView
from restaurant_app.views import (
    ChairBookingViewSet,
    ChairsViewSet,
    CustomerDetailsViewSet,
    DishSizeViewSet,
    FOCProductViewSet,
    OnlineOrderViewSet,
    OrderItemViewSet,
    PrintViewSet,
    UserViewSet,
    toggle_sidebar_item_active,
    CategoryViewSet,
    DishViewSet,
    LogoInfoViewSet,
    OrderStatusUpdateViewSet,
    OrderViewSet,
    NotificationViewSet,
    BillViewSet,
    LoginViewSet,
    PasscodeLoginView,
    LogoutView,
    FloorViewSet,
    TableViewSet,
    CouponViewSet,
    MenuViewSet,
    MenuItemViewSet,
    MessViewSet,
    MessTypeViewSet,
    SearchDishesAPIView,
    CreditUserViewSet,
    CreditOrderViewSet,
    MessTransactionViewSet,
    OrderTypeChangeViewSet,
    DishVariantViewSet,
    CancelOrderByBillView,
    CreditTransactionViewSet,
    landing_page,
    SidebarItemViewSet
)
from delivery_drivers.views import (
    DeliveryDriverViewSet,
    DeliveryOrderViewSet,
)
from transactions_app.views import (CashCountSheetViewSet, NatureGroupViewSet,
 MainGroupViewSet, 
 LedgerViewSet, 
 TransactionViewSet, 
 ShareUserManagementViewSet,
 ProfitLossShareTransactionViewSet,
 )

router = DefaultRouter()
#User Management
router.register(r'users', UserViewSet)


router.register(r"login", LoginViewSet, basename="login")
router.register(r"dishes", DishViewSet, basename="dishes")
router.register(r'dish-sizes', DishSizeViewSet, basename="dish-sizes")
router.register(r'variants', DishVariantViewSet, basename="variants")
router.register(r"categories", CategoryViewSet, basename="categories")

#Order Mangement
router.register(r'customer-details', CustomerDetailsViewSet, basename='customer-details')
router.register(r'online-orders', OnlineOrderViewSet)
router.register(r"orders", OrderViewSet, basename="orders")  # Primary Orders ViewSet
router.register(r'order-items', OrderItemViewSet, basename="order-items")
router.register(r"order-type", OrderTypeChangeViewSet, basename="order_type")  # Separate route for changing order types
router.register(r"bills", BillViewSet, basename="bills")
router.register(r"notifications", NotificationViewSet, basename="notifications")
router.register(r"floors", FloorViewSet, basename="floors")
router.register(r"tables", TableViewSet, basename="tables")
router.register(r"coupons", CouponViewSet, basename="coupons")
router.register(r"mess-types", MessTypeViewSet, basename="mess_types")
router.register(r"menus", MenuViewSet, basename="menus")
router.register(r"menu-items", MenuItemViewSet, basename="menu_items")
router.register(r"messes", MessViewSet, basename="messes")
router.register(r'mess-transactions', MessTransactionViewSet, basename="mess-transactions")

#FOC Product
router.register(r'focproducts', FOCProductViewSet, basename='focproduct')

#Chair Mangement
router.register(r'chairs', ChairsViewSet)
router.register(r'chair-bookings', ChairBookingViewSet)
# Credit User URLs
router.register(r"credit-users", CreditUserViewSet, basename="credit_users")
router.register(r"credit-orders", CreditOrderViewSet, basename="credit_orders")
router.register(r'credit-transactions', CreditTransactionViewSet, basename="credit-transactions")

# Delivery Driver URLs
router.register(r"delivery-drivers", DeliveryDriverViewSet, basename="delivery_drivers")
router.register(r"delivery-orders", DeliveryOrderViewSet, basename="delivery_orders")

# for updating the status of the order
router.register(r'order-status', OrderStatusUpdateViewSet, basename='order-status')

# to change the logo of the users
router.register(r'logo-info', LogoInfoViewSet, basename='logoinfo')
router.register(r'sidebar-items', SidebarItemViewSet)

# Accounts Transactions
router.register(r'nature-groups', NatureGroupViewSet)
router.register(r'main-groups', MainGroupViewSet)
router.register(r'ledgers', LedgerViewSet)
router.register(r'transactions', TransactionViewSet, basename="transactions")
router.register(r'share-user-management', ShareUserManagementViewSet, basename="share-user-management")
router.register(r'profit-loss-share-transactions',ProfitLossShareTransactionViewSet,basename='profit-loss-share-transactions')
router.register(r'cashcount-sheet', CashCountSheetViewSet,basename="cashcount-sheet")
router.register(r'print', PrintViewSet, basename='print')


urlpatterns = [
    path('', landing_page, name='landing_page'),
    path("admin/", admin.site.urls),        
    path("api/", include(router.urls)),
    path("api/login-passcode/", PasscodeLoginView.as_view(), name="login-passcode"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/logout/", LogoutView.as_view({"post": "logout"}), name="logout"),
    path("api/search-dishes/", SearchDishesAPIView.as_view(), name="search_dishes"),  # Include the search API endpoint

    # Register the new Cancel Order API
    path("api/bills/<int:bill_id>/cancel_order/", CancelOrderByBillView.as_view(), name="cancel-order-by-bill"),
    path('admin/restaurant_app/sidebaritem/<int:item_id>/toggle-active/', toggle_sidebar_item_active, name='toggle_sidebar_item_active'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
