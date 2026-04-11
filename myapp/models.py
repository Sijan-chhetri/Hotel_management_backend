from datetime import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now


from django.contrib.auth.models import BaseUserManager

# class CustomUserManager(BaseUserManager):
#     def create_user(self, email, password=None, **extra_fields):
#         if not email:
#             raise ValueError('The Email field must be set')
#         email = self.normalize_email(email)
#         user = self.model(email=email, **extra_fields)
#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, email, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)
#         extra_fields.setdefault('is_active', True)

#         if extra_fields.get('is_staff') is not True:
#             raise ValueError('Superuser must have is_staff=True.')
#         if extra_fields.get('is_superuser') is not True:
#             raise ValueError('Superuser must have is_superuser=True.')

#         return self.create_user(email, password, **extra_fields)






class WebUser(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255) 
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=True)  # Default to True
    created_at = models.DateTimeField(auto_now_add=True)
 
    
    def __str__(self):
        return self.email


class User(AbstractUser):
    username = None  # Remove username
    hotel_name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, null=True, blank=True)
    zipcode = models.CharField(max_length=20, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(unique=True) 
    description = models.TextField(null=True, blank=True)


    USERNAME_FIELD = 'email'  
    REQUIRED_FIELDS = ['hotel_name']  
    
    # objects = CustomUserManager()  

    def __str__(self):
        return self.hotel_name
    

class SubUser(models.Model):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("receptionist", "Receptionist"),
        ("inventoryManager", "Inventory Manager"),
        ("kitchenManager", "Kitchen Manager"),
        ("staffManager", "Staff Manager"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subusers")
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    role_description = models.TextField(blank=True, null=True) 
    is_active = models.BooleanField(default=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.email} - {self.role}"
    
   
class Room(models.Model):
    hotel = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rooms")
    room_id = models.CharField(max_length=100)
    room_desc = models.TextField()
    room_type = models.CharField(
        max_length=50,
        choices=[('single', 'Single'), ('double', 'Double'), ('suite', 'Suite'), ('family', 'Family')]
    )
    floor = models.IntegerField()
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    max_guest = models.IntegerField()
    free_child = models.IntegerField()
    room_pictures = models.ImageField(upload_to='room_images/')
    
    bed_type = models.CharField(max_length=50)
    room_size = models.IntegerField()
    amenities = models.JSONField(default=list)  

    class Meta:
        unique_together = ('hotel', 'room_id')
        ordering = ['hotel', 'room_id']

    def __str__(self):
        return f"Room {self.room_id} ({self.room_type})"
    
    



class Employee(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)  # Foreign key to User
    employee_id = models.IntegerField(unique=True, primary_key=True)
    employee_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(unique=True)  
    department = models.CharField(max_length=255)
    position = models.CharField(max_length=255) 
    salary=  models.IntegerField()
    joined_at = models.DateField()  

    def __str__(self):
        return self.employee_name  
    

    
from django.db import models

class Guest(models.Model):
    DOC_TYPE_CHOICES = [
        ('passport', 'Passport'),
        ('nid', 'National ID'),
        ('license', 'Driver License'),
    ]
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Others', 'Others'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    gender = models.CharField(max_length=15, choices=GENDER_CHOICES)
    dob = models.DateField(null=True, blank=True)  # Date of Birth
    nationality = models.CharField(max_length=50, blank=True)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES)
    doc_number = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Booking(models.Model):
    STATUS_CHOICES = [
        ('booked', 'Booked'),
        ('checked-in', 'Checked-in'),
        ('checked-out', 'Checked-out'),
        ('canceled', 'Canceled'),
    ]

    booking_id = models.AutoField(primary_key=True)
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name="bookings")
    room = models.ForeignKey("Room", on_delete=models.CASCADE, related_name="bookings")
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='booked')
    notes = models.TextField(blank=True, default='')
    group_id = models.CharField(max_length=50, blank=True, default='')  # shared across multi-room bookings  # Guest notes added at reservation time

    def __str__(self):
        return f"Booking {self.booking_id} - {self.guest.name} ({self.room.room_id})"
    
from django.db import models
from django.utils import timezone


class Housekeeping(models.Model):
    STATUS_CHOICES = [
        ('in-progress', 'Cleaning in Progress'),
        ('ready', 'Ready'),
        ('need-cleaning', 'Need Cleaning'),
        ('inspecting', 'Inspecting'),
    ]

    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    booking = models.OneToOneField('Booking', on_delete=models.CASCADE, related_name='housekeeping')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='need-cleaning')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    notes = models.TextField(blank=True, default='')
    toiletries_restocked = models.BooleanField(default=False)
    last_cleaned_at = models.DateTimeField(null=True, blank=True)
    assigned_to = models.CharField(max_length=100, blank=True, default='')

    def __str__(self):
        return f"Housekeeping for Room {self.booking.room.room_id} - Status: {self.status}, Priority: {self.priority}"



class Payment(models.Model):
    PAYMENT_CHOICES = [('cash', 'Cash'), ('online', 'Online')]
    
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE)
    payment_type = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    payment_status = models.CharField(max_length=50, default="Completed")
    timestamp = models.DateTimeField(auto_now_add=True)
    


from django.db import models

class Invoice(models.Model):
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE)  
    payment = models.ForeignKey('Payment', on_delete=models.CASCADE)
    room = models.ForeignKey("Room", on_delete=models.SET_NULL, null=True, blank=True)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    payment_type = models.CharField(max_length=10, choices=[('cash', 'Cash'), ('online', 'Online')])
    room_type = models.CharField(max_length=50)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    generated_on = models.DateTimeField(auto_now_add=True)
    invoice_pdf = models.FileField(upload_to='invoices/', null=True, blank=True)

    def __str__(self):
        return f"Invoice {self.id} for Booking {self.booking.booking_id}"

    


class InventoryItem(models.Model):
    USAGE_TYPE_CHOICES = [
        ('general',      'General'),
        ('housekeeping', 'Housekeeping'),
        ('order',        'Order / Kitchen'),
        ('both',         'Both (Housekeeping & Orders)'),
    ]

    user = models.ForeignKey('User', on_delete=models.CASCADE) 
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    vendor = models.CharField(max_length=255)
    date_added = models.DateTimeField(default=now)
    usage_type = models.CharField(max_length=20, choices=USAGE_TYPE_CHOICES, default='general')

    def __str__(self):
        return self.name
    

class InventoryRequest(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('canceled', 'Canceled'),
        ('out_of_stock', 'Out of Stock'),
        ('accepted', 'Accepted'),
    ]

    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='requests')
    user = models.ForeignKey('User', on_delete=models.CASCADE)  
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    created_at = models.DateTimeField(auto_now_add=True)
 

    def __str__(self):
        return f"Request for {self.inventory_item.name} by {self.user}"



class Item(models.Model):
    ITEM_TYPE_CHOICES = [
        ('Food', 'Food'),
        ('Beverage', 'Beverage'),
    ]
    
    hotel = models.ForeignKey(User, on_delete=models.CASCADE, related_name="items")  # Add hotel relationship
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    available = models.BooleanField(default=True)
    item_type = models.CharField(max_length=8, choices=ITEM_TYPE_CHOICES)
    category = models.CharField(max_length=50)
    food_type = models.CharField(max_length=50)
    image = models.ImageField(upload_to='item_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.item_type} - {self.name}"


 
from django.db import models
from django.utils import timezone

class OrderItem(models.Model):
    ORDER_STATUS_CHOICES = [
        ('delivered', 'Delivered'),
        ('undelivered', 'Undelivered'),
        ('canceled', 'Canceled'),
    ]
    booking = models.ForeignKey("Booking", on_delete=models.CASCADE, related_name="orders")
    item = models.ForeignKey("Item", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    ordered_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='undelivered',  
    )
    
    def __str__(self):
        return f"Order {self.id} - {self.item.name} - {self.status}"
    


    def __str__(self):
        return f"Order #{self.id} - {self.item.name} x {self.quantity} for Booking {self.booking_id}"








# ── Payment Gateway Config ──────────────────────────────────────────────────

class PaymentGatewayConfig(models.Model):
    GATEWAY_CHOICES = [
        ('khalti',   'Khalti'),
        ('esewa',    'eSewa'),
        ('phonepay', 'PhonePay'),
        ('card',     'Card'),
    ]
    MODE_CHOICES = [
        ('test', 'Test'),
        ('live', 'Live'),
    ]

    hotel           = models.ForeignKey('User', on_delete=models.CASCADE, related_name='payment_configs')
    gateway_type    = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    is_enabled      = models.BooleanField(default=False)
    mode            = models.CharField(max_length=10, choices=MODE_CHOICES, default='test')
    merchant_id     = models.TextField(blank=True)   # plain text — not a secret
    public_key      = models.TextField(blank=True)   # Fernet-encrypted
    secret_key      = models.TextField(blank=True)   # Fernet-encrypted
    last_webhook_at = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('hotel', 'gateway_type')

    def __str__(self):
        return f"{self.hotel.hotel_name} — {self.gateway_type} ({self.mode})"


# ── OTA Channel Config ──────────────────────────────────────────────────────

class OTAChannelConfig(models.Model):
    PLATFORM_TYPE_CHOICES = [
        ('channel_manager', 'Channel Manager'),
        ('ota',             'OTA'),
    ]

    hotel         = models.ForeignKey('User', on_delete=models.CASCADE, related_name='ota_configs')
    platform_name = models.CharField(max_length=100)
    platform_type = models.CharField(max_length=20, choices=PLATFORM_TYPE_CHOICES)
    api_key       = models.TextField()               # Fernet-encrypted
    api_secret    = models.TextField(blank=True)     # Fernet-encrypted, optional
    extra_config  = models.TextField(blank=True)     # Fernet-encrypted JSON blob, optional
    is_connected  = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('hotel', 'platform_name')

    def __str__(self):
        return f"{self.hotel.hotel_name} — {self.platform_name}"


# ── Credential Audit Log ────────────────────────────────────────────────────

class CredentialAuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]

    hotel      = models.ForeignKey('User', on_delete=models.CASCADE, related_name='audit_logs')
    model_name = models.CharField(max_length=50)
    record_id  = models.IntegerField()
    action     = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.hotel.hotel_name} — {self.action} {self.model_name}#{self.record_id}"


# ── Housekeeping Staff Assignment ──────────────────────────────────────────

class HousekeepingAssignment(models.Model):
    hotel       = models.ForeignKey('User', on_delete=models.CASCADE, related_name='hk_assignments')
    room_id     = models.CharField(max_length=100)
    staff_name  = models.CharField(max_length=100)
    shift       = models.CharField(max_length=20, choices=[('morning','Morning'),('afternoon','Afternoon'),('night','Night')], default='morning')
    date        = models.DateField()
    completed   = models.BooleanField(default=False)
    notes       = models.TextField(blank=True, default='')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'shift']

    def __str__(self):
        return f"{self.staff_name} → Room {self.room_id} ({self.date})"


# ── Lost & Found ────────────────────────────────────────────────────────────

class LostAndFound(models.Model):
    STATUS_CHOICES = [
        ('found',    'Found'),
        ('claimed',  'Claimed'),
        ('disposed', 'Disposed'),
    ]

    hotel        = models.ForeignKey('User', on_delete=models.CASCADE, related_name='lost_found')
    room_id      = models.CharField(max_length=100)
    item_name    = models.CharField(max_length=200)
    description  = models.TextField(blank=True, default='')
    found_date   = models.DateField()
    found_by     = models.CharField(max_length=100, blank=True, default='')
    guest_name   = models.CharField(max_length=100, blank=True, default='')
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='found')
    returned_at  = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-found_date']

    def __str__(self):
        return f"{self.item_name} — Room {self.room_id} ({self.status})"


# ── Special Requests ────────────────────────────────────────────────────────

class SpecialRequest(models.Model):
    TYPE_CHOICES = [
        ('extra_bed',    'Extra Bed'),
        ('baby_crib',    'Baby Crib'),
        ('cleaning',     'Cleaning'),
        ('towels',       'Extra Towels'),
        ('amenities',    'Amenities'),
        ('maintenance',  'Maintenance'),
        ('other',        'Other'),
    ]
    STATUS_CHOICES = [
        ('pending',     'Pending'),
        ('in_progress', 'In Progress'),
        ('completed',   'Completed'),
        ('cancelled',   'Cancelled'),
    ]

    hotel       = models.ForeignKey('User', on_delete=models.CASCADE, related_name='special_requests')
    booking     = models.ForeignKey('Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='special_requests')
    room_id     = models.CharField(max_length=100)
    guest_name  = models.CharField(max_length=100, blank=True, default='')
    request_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    description = models.TextField(blank=True, default='')
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.CharField(max_length=100, blank=True, default='')
    source      = models.CharField(max_length=20, default='manual')  # 'manual' | 'reservation'
    created_at  = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.request_type} — Room {self.room_id} ({self.status})"


# ── Linen Tracking ──────────────────────────────────────────────────────────

class LinenRecord(models.Model):
    TYPE_CHOICES = [
        ('towel',        'Towel'),
        ('bedsheet',     'Bedsheet'),
        ('pillow_cover', 'Pillow Cover'),
        ('duvet',        'Duvet Cover'),
        ('bathmat',      'Bath Mat'),
    ]
    STATUS_CHOICES = [
        ('in_use',   'In Use'),
        ('washed',   'Washed'),
        ('damaged',  'Damaged'),
        ('disposed', 'Disposed'),
    ]

    hotel       = models.ForeignKey('User', on_delete=models.CASCADE, related_name='linen_records')
    linen_type  = models.CharField(max_length=20, choices=TYPE_CHOICES)
    quantity    = models.PositiveIntegerField(default=1)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_use')
    room_id     = models.CharField(max_length=100, blank=True, default='')
    notes       = models.TextField(blank=True, default='')
    updated_at  = models.DateTimeField(auto_now=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['linen_type', 'status']

    def __str__(self):
        return f"{self.linen_type} × {self.quantity} ({self.status})"


# ── Front Desk Notification ─────────────────────────────────────────────────

class FrontDeskNotification(models.Model):
    TYPE_CHOICES = [
        ('room_ready',       'Room Ready'),
        ('special_request',  'Special Request'),
        ('guest_preference', 'Guest Preference Update'),
        ('general',          'General'),
    ]
    STATUS_CHOICES = [
        ('unread', 'Unread'),
        ('read',   'Read'),
        ('dismissed', 'Dismissed'),
    ]

    hotel      = models.ForeignKey('User', on_delete=models.CASCADE, related_name='fd_notifications')
    room_id    = models.CharField(max_length=100)
    guest_name = models.CharField(max_length=100, blank=True, default='')
    notif_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='general')
    message    = models.TextField()
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unread')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notif_type}] Room {self.room_id} — {self.status}"


# ── Guest Preferences ───────────────────────────────────────────────────────

class GuestPreferences(models.Model):
    booking    = models.OneToOneField('Booking', on_delete=models.CASCADE, related_name='preferences')
    notes      = models.TextField(blank=True, default='')          # general booking/check-in notes
    preferences = models.TextField(blank=True, default='')         # free-text guest preferences
    extra_bed  = models.BooleanField(default=False)
    baby_crib  = models.BooleanField(default=False)
    late_checkout = models.BooleanField(default=False)
    early_checkin = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for Booking {self.booking.booking_id}"


# ── Attendance ──────────────────────────────────────────────────────────────

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present',  'Present'),
        ('absent',   'Absent'),
        ('late',     'Late'),
        ('half_day', 'Half Day'),
    ]

    employee   = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='attendance')
    hotel      = models.ForeignKey('User', on_delete=models.CASCADE, related_name='attendance')
    date       = models.DateField()
    check_in   = models.TimeField(null=True, blank=True)
    check_out  = models.TimeField(null=True, blank=True)
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')
    overtime_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    notes      = models.TextField(blank=True, default='')

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.employee_name} — {self.date} ({self.status})"


# ── Shift Schedule ──────────────────────────────────────────────────────────

class ShiftSchedule(models.Model):
    SHIFT_CHOICES = [
        ('morning',   'Morning (6am–2pm)'),
        ('afternoon', 'Afternoon (2pm–10pm)'),
        ('night',     'Night (10pm–6am)'),
    ]

    employee  = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='shifts')
    hotel     = models.ForeignKey('User', on_delete=models.CASCADE, related_name='shifts')
    date      = models.DateField()
    shift     = models.CharField(max_length=20, choices=SHIFT_CHOICES)
    notes     = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['date', 'shift']

    def __str__(self):
        return f"{self.employee.employee_name} — {self.shift} on {self.date}"


# ── Leave Request ───────────────────────────────────────────────────────────

class LeaveRequest(models.Model):
    TYPE_CHOICES = [
        ('sick',      'Sick Leave'),
        ('vacation',  'Vacation'),
        ('emergency', 'Emergency'),
        ('other',     'Other'),
    ]
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    employee   = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='leaves')
    hotel      = models.ForeignKey('User', on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    start_date = models.DateField()
    end_date   = models.DateField()
    reason     = models.TextField(blank=True, default='')
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.employee_name} — {self.leave_type} ({self.status})"


# ── Housekeeping Consumables ────────────────────────────────────────────────
# Defines which inventory items are consumed per room clean

class HousekeepingConsumable(models.Model):
    hotel          = models.ForeignKey('User', on_delete=models.CASCADE, related_name='hk_consumables')
    inventory_item = models.ForeignKey('InventoryItem', on_delete=models.CASCADE, related_name='hk_consumables')
    qty_per_clean  = models.PositiveIntegerField(default=1)  # units used each time a room is cleaned

    class Meta:
        unique_together = ('hotel', 'inventory_item')

    def __str__(self):
        return f"{self.inventory_item.name} × {self.qty_per_clean} per clean"


# ── Inventory Usage Log ─────────────────────────────────────────────────────

class InventoryUsageLog(models.Model):
    SOURCE_CHOICES = [
        ('housekeeping', 'Housekeeping'),
        ('order',        'Order'),
    ]

    hotel          = models.ForeignKey('User', on_delete=models.CASCADE, related_name='usage_logs')
    inventory_item = models.ForeignKey('InventoryItem', on_delete=models.CASCADE, related_name='usage_logs')
    quantity_used  = models.PositiveIntegerField()
    source         = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    reference      = models.CharField(max_length=200, blank=True, default='')  # e.g. "Room 101 cleaned" or "Order #5"
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.inventory_item.name} −{self.quantity_used} ({self.source})"
