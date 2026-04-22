from django.urls import path

from . import inventory
from . import views
from . import rooms
from . import employee
from .import subuser
from . import password
from . import checkout
from . import invoice
from . import booking
from . import Item
from . import Order
from . import housekepping
from . import Forgetpassword
from . import webadmin
from .payment_config_views import (
    PaymentGatewayConfigView, PaymentGatewayConfigDetailView,
    OTAChannelConfigView, OTAChannelConfigDetailView,
    PaymentWebhookView,
)
from .housekeeping_extended import (
    AssignmentView, AssignmentDetailView,
    LostFoundView, LostFoundDetailView,
    SpecialRequestView, SpecialRequestDetailView,
    LinenView, LinenDetailView,
    LinenIssueView, LinenCollectView,
)
from .employee_management import (
    AttendanceListView, AttendanceDetailView,
    ShiftListView, ShiftDetailView,
    LeaveListView, LeaveDetailView,
)
from .frontdesk import (
    NotificationListView, NotificationDetailView,
    NotifyRoomReadyView,
    GuestPreferencesListView, GuestPreferencesDetailView,
)
from .integration import (
    ConsumableListView, ConsumableDetailView,
    RoomCleanedDeductView,
    UsageLogView, LowStockView,
    ManualDeductView,
)


urlpatterns = [
    
    
    path('register/', views.RegisterHotelView.as_view(), name='register-hotel'),
    path('login/', views.LoginView.as_view(), name='register-hotel'),

    path('profile/', views.UserDetailView.as_view(), name='register-hotel'),

    path('password/', password.ChangePasswordView.as_view(), name='password'),
    
    path('check-email/', Forgetpassword.ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', Forgetpassword.ResetPasswordConfirmView.as_view(), name='reset password'),
    


    path('subuser/', subuser.SubUserManageView.as_view(), name='subuser'),
    path('subuser/<int:pk>/', subuser.SubUserManageView.as_view(), name='subuser-detail'),
   
    
    path('add-room/', rooms.AddRoomView.as_view(), name='add-room'),
    path('rooms/', rooms.RoomListView.as_view(), name='room-list'),
    path('rooms/<str:room_id>/', rooms.EditRoomView.as_view(), name='edit-room'),


    path('employees/', employee.EmployeeListCreateAPIView.as_view(), name='employee-list-create'),
    path('employees/<int:employee_id>/', employee.EmployeeDetailAPIView.as_view(), name='employee-detail'),


    path('guests/', views.GuestListCreateView.as_view(), name='guest-list-create'),
    path('guests/<int:pk>/', views.GuestDetailView.as_view(), name='guest-detail'),


    
    path('bookings/', booking.BookingListCreateView.as_view(), name='booking-list-create'),
    path('bookings/multi/', booking.MultiBookingView.as_view(), name='multi-booking'),
    path('bookings/<int:id>/', booking.BookingListCreateView.as_view(), name='booking-update'),
    

    


    path('checkout/<int:booking_id>/',checkout.BookingDetailView.as_view(), name='checkout-detail'),
    path('initiate-khalti-payment/', checkout.KhaltiPaymentAPI.as_view(), name='verify-khalti-payment'),
    path('verify-khalti-payment/', checkout.KhaltiVerifyAPI.as_view(), name='verify-khalti-payment'),


    path('payment/', checkout.PaymentView.as_view(), name='payment'),
    path('generate-invoice/', invoice.GenerateInvoiceView.as_view(), name='generate-invoice'),
   
    



    path('inventory/', inventory.InventoryListCreateAPIView.as_view(), name="inventory-list"),  
    path('inventory/<int:id>/', inventory.InventoryDetailAPIView.as_view(), name="inventory-detail"),  
    path('inventory/request/', inventory.InventoryRequestCreateView.as_view(), name='request-inventory'),
    path('inventory/request/<int:pk>/', inventory.InventoryRequestCreateView.as_view(), name='update-inventory-request'),
    
    
    path('items/', Item.ItemListCreateView.as_view(), name='item-list-create'),  
    path('items/<int:pk>/', Item.ItemDetailView.as_view(), name='item-detail'),  
    
    
    
    path('order-item/', Order.OrderItemView.as_view(), name='order-item'),
    path('order-item/<int:order_id>/', Order.OrderItemView.as_view(), name='order-item'),
    
    
    path('housekeeping', housekepping.CreateHousekeepingAPIView.as_view(), name='housekeeping-detail'),

    path('housekeeping/today-checked-in/', housekepping.ActiveCheckedInAPIView.as_view(), name='today-checked-in'),
    
    # not used
    path('housekeeping/update-status/', housekepping.UpdateHousekeepingAPIView.as_view(), name='update-housekeeping-status'),
    
    
    path('webuser/register', webadmin.WebuserRegisterView.as_view(), name='webuser register'),
    path('webuser/login',  webadmin.WebuserLoginView.as_view(), name='webuserlogin'),
    path('get/user',  webadmin.UserListView.as_view(), name='getuser'),
    path('user/<int:user_id>/update-status/', webadmin.UpdateUserStatusView.as_view(), name='update-user-status'),
    
    path('get/admins/',  webadmin.AdminListView.as_view(), name='getuser'),
    path('webadmin/<int:user_id>/update-status/', webadmin.AdminStatusUpdateView.as_view(), name='update-user-status'),

    # Payment Gateway Config
    path('payment-gateway-configs/', PaymentGatewayConfigView.as_view(), name='payment-gateway-configs'),
    path('payment-gateway-configs/<int:pk>/', PaymentGatewayConfigDetailView.as_view(), name='payment-gateway-config-detail'),

    # OTA Channel Config
    path('ota-channel-configs/', OTAChannelConfigView.as_view(), name='ota-channel-configs'),
    path('ota-channel-configs/<int:pk>/', OTAChannelConfigDetailView.as_view(), name='ota-channel-config-detail'),

    # Webhook receiver
    path('webhooks/payment/<str:gateway_type>/', PaymentWebhookView.as_view(), name='payment-webhook'),

    # Housekeeping extended modules
    path('hk/assignments/', AssignmentView.as_view(), name='hk-assignments'),
    path('hk/assignments/<int:pk>/', AssignmentDetailView.as_view(), name='hk-assignment-detail'),
    path('hk/lost-found/', LostFoundView.as_view(), name='hk-lost-found'),
    path('hk/lost-found/<int:pk>/', LostFoundDetailView.as_view(), name='hk-lost-found-detail'),
    path('hk/special-requests/', SpecialRequestView.as_view(), name='hk-special-requests'),
    path('hk/special-requests/<int:pk>/', SpecialRequestDetailView.as_view(), name='hk-special-request-detail'),
    path('hk/linen/', LinenView.as_view(), name='hk-linen'),
    path('hk/linen/<int:pk>/', LinenDetailView.as_view(), name='hk-linen-detail'),
    path('hk/linen/<int:pk>/issue/', LinenIssueView.as_view(), name='hk-linen-issue'),
    path('hk/linen/<int:pk>/collect/', LinenCollectView.as_view(), name='hk-linen-collect'),

    # Front Desk Coordination
    path('fd/notifications/', NotificationListView.as_view(), name='fd-notifications'),
    path('fd/notifications/<int:pk>/', NotificationDetailView.as_view(), name='fd-notification-detail'),
    path('fd/notify-room-ready/', NotifyRoomReadyView.as_view(), name='fd-notify-room-ready'),
    path('fd/guest-preferences/', GuestPreferencesListView.as_view(), name='fd-guest-preferences'),
    path('fd/guest-preferences/<int:booking_id>/', GuestPreferencesDetailView.as_view(), name='fd-guest-preferences-detail'),

    # Employee Management
    path('em/attendance/', AttendanceListView.as_view(), name='em-attendance'),
    path('em/attendance/<int:pk>/', AttendanceDetailView.as_view(), name='em-attendance-detail'),
    path('em/shifts/', ShiftListView.as_view(), name='em-shifts'),
    path('em/shifts/<int:pk>/', ShiftDetailView.as_view(), name='em-shift-detail'),
    path('em/leaves/', LeaveListView.as_view(), name='em-leaves'),
    path('em/leaves/<int:pk>/', LeaveDetailView.as_view(), name='em-leave-detail'),

    # Integration: Housekeeping ↔ Inventory ↔ Orders
    path('integration/consumables/', ConsumableListView.as_view(), name='int-consumables'),
    path('integration/consumables/<int:pk>/', ConsumableDetailView.as_view(), name='int-consumable-detail'),
    path('integration/room-cleaned/', RoomCleanedDeductView.as_view(), name='int-room-cleaned'),
    path('integration/manual-deduct/', ManualDeductView.as_view(), name='int-manual-deduct'),
    path('integration/usage-log/', UsageLogView.as_view(), name='int-usage-log'),
    path('integration/low-stock/', LowStockView.as_view(), name='int-low-stock'),
]
    

