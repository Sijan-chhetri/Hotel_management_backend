from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    User, SubUser, Room, Guest, Booking, Employee,
    InventoryItem, InventoryRequest, Item, OrderItem,
    Payment, Invoice, Housekeeping,
    PaymentGatewayConfig, OTAChannelConfig,
    HousekeepingAssignment, LostAndFound, SpecialRequest, LinenRecord,
    FrontDeskNotification, Attendance, ShiftSchedule, LeaveRequest,
    HousekeepingConsumable, InventoryUsageLog,
)

admin.site.site_header = "The HMS"
admin.site.site_title  = "The HMS Admin"
admin.site.index_title = "Hotel Management System"


# ── User ──────────────────────────────────────────────────────────────────────
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['-date_joined']
    list_display  = ['email', 'hotel_name', 'phone_number', 'city', 'is_active', 'is_staff', 'date_joined']
    list_filter   = ['is_active', 'is_staff', 'city']
    search_fields = ['email', 'hotel_name', 'phone_number']
    list_per_page = 20
    fieldsets = (
        ("Login",       {'fields': ('email', 'password')}),
        ("Hotel Info",  {'fields': ('hotel_name', 'phone_number', 'description')}),
        ("Address",     {'fields': ('address', 'city', 'state', 'zipcode')}),
        ("Permissions", {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ("Dates",       {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': (
            'email', 'hotel_name', 'password1', 'password2',
            'phone_number', 'address', 'city', 'state', 'zipcode',
        )}),
    )
    readonly_fields = ['last_login', 'date_joined']


# ── SubUser ───────────────────────────────────────────────────────────────────
@admin.register(SubUser)
class SubUserAdmin(admin.ModelAdmin):
    list_display  = ['email', 'role', 'role_description', 'is_active_badge', 'hotel']
    list_filter   = ['role', 'is_active']
    search_fields = ['email', 'role']
    list_per_page = 25

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#10b981;font-weight:700">● Active</span>')
        return format_html('<span style="color:#ef4444;font-weight:700">● Inactive</span>')
    is_active_badge.short_description = 'Status'

    def hotel(self, obj):
        return obj.user.hotel_name if obj.user else '—'
    hotel.short_description = 'Hotel'


# ── Room ──────────────────────────────────────────────────────────────────────
@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display  = ['room_id', 'type_badge', 'floor', 'rate_display', 'max_guest', 'status_badge', 'hotel_name']
    list_filter   = ['room_type', 'floor']
    search_fields = ['room_id', 'room_type', 'hotel__hotel_name']
    list_per_page = 25
    ordering      = ['floor', 'room_id']

    def type_badge(self, obj):
        c = {'single':'#6366f1','double':'#10b981','suite':'#f59e0b','family':'#ec4899','deluxe':'#8b5cf6'}.get(obj.room_type.lower(),'#6b7280')
        return format_html('<span style="background:{}20;color:{};padding:3px 10px;border-radius:6px;font-size:11px;font-weight:700">{}</span>', c, c, obj.room_type.title())
    type_badge.short_description = 'Type'

    def rate_display(self, obj):
        return format_html('<strong>Rs {:,.0f}</strong>', float(obj.rate))
    rate_display.short_description = 'Rate/Night'

    def status_badge(self, obj):
        if obj.is_available:
            return format_html('<span style="color:#10b981;font-weight:700">● Available</span>')
        return format_html('<span style="color:#ef4444;font-weight:700">● Occupied</span>')
    status_badge.short_description = 'Status'

    def hotel_name(self, obj):
        return obj.hotel.hotel_name if obj.hotel else '—'
    hotel_name.short_description = 'Hotel'


# ── Guest ─────────────────────────────────────────────────────────────────────
@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display  = ['name', 'email', 'phone', 'gender', 'nationality', 'doc_type', 'doc_number']
    search_fields = ['name', 'email', 'phone', 'doc_number']
    list_filter   = ['nationality', 'doc_type', 'gender']
    list_per_page = 25
    ordering      = ['name']


# ── Booking ───────────────────────────────────────────────────────────────────
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display  = ['booking_id', 'guest_name', 'room_info', 'check_in_date', 'check_out_date', 'nights_col', 'status_badge']
    list_filter   = ['status', 'check_in_date']
    search_fields = ['booking_id', 'guest__name', 'guest__email', 'room__room_id']
    list_per_page = 20
    ordering      = ['-check_in_date']
    date_hierarchy = 'check_in_date'

    def guest_name(self, obj):
        return obj.guest.name if obj.guest else '—'
    guest_name.short_description = 'Guest'

    def room_info(self, obj):
        if obj.room:
            return format_html('{} <span style="color:#9ca3af;font-size:11px">({})</span>', obj.room.room_id, obj.room.room_type.title())
        return '—'
    room_info.short_description = 'Room'

    def nights_col(self, obj):
        if obj.check_in_date and obj.check_out_date:
            return format_html('<span style="font-weight:600">{}</span>', (obj.check_out_date - obj.check_in_date).days)
        return '—'
    nights_col.short_description = 'Nights'

    def status_badge(self, obj):
        colors = {'booked':('#1d4ed8','rgba(59,130,246,0.12)'),'checked-in':('#065f46','rgba(16,185,129,0.12)'),'checked-out':('#374151','rgba(107,114,128,0.12)'),'canceled':('#991b1b','rgba(239,68,68,0.12)')}
        c, bg = colors.get(obj.status, ('#374151','#f3f4f6'))
        return format_html('<span style="color:{};background:{};padding:3px 10px;border-radius:6px;font-size:11px;font-weight:700">{}</span>', c, bg, obj.status.replace('-',' ').title())
    status_badge.short_description = 'Status'


# ── Employee ──────────────────────────────────────────────────────────────────
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display  = ['employee_name', 'position', 'department', 'email', 'phone_number', 'salary_display', 'joined_at']
    list_filter   = ['department', 'position']
    search_fields = ['employee_name', 'email', 'department']
    list_per_page = 25
    ordering      = ['department', 'employee_name']

    def salary_display(self, obj):
        return format_html('Rs {:,.0f}', float(obj.salary))
    salary_display.short_description = 'Salary'


# ── Inventory ─────────────────────────────────────────────────────────────────
@admin.register(InventoryItem)
class InventoryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'category', 'qty_badge', 'price_display', 'vendor', 'usage_type', 'date_added']
    list_filter   = ['category', 'usage_type']
    search_fields = ['name', 'vendor', 'category']
    list_per_page = 25

    def qty_badge(self, obj):
        color = '#ef4444' if obj.quantity < 10 else '#10b981'
        return format_html('<span style="color:{};font-weight:700">{}</span>', color, obj.quantity)
    qty_badge.short_description = 'Qty'

    def price_display(self, obj):
        return format_html('Rs {:,.2f}', float(obj.price))
    price_display.short_description = 'Price'


@admin.register(InventoryRequest)
class InventoryRequestAdmin(admin.ModelAdmin):
    list_display  = ['id', 'inventory_item', 'quantity', 'status_badge', 'created_at']
    list_filter   = ['status']
    search_fields = ['inventory_item__name']
    list_per_page = 25

    def status_badge(self, obj):
        colors = {'requested':('#f59e0b','rgba(245,158,11,0.12)'),'accepted':('#10b981','rgba(16,185,129,0.12)'),'canceled':('#ef4444','rgba(239,68,68,0.12)'),'out_of_stock':('#6b7280','rgba(107,114,128,0.12)')}
        c, bg = colors.get(obj.status, ('#374151','#f3f4f6'))
        return format_html('<span style="color:{};background:{};padding:3px 10px;border-radius:6px;font-size:11px;font-weight:700">{}</span>', c, bg, obj.status.replace('_',' ').title())
    status_badge.short_description = 'Status'


# ── Item (Menu) ───────────────────────────────────────────────────────────────
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display  = ['name', 'item_type', 'category', 'food_type', 'price_display', 'avail_badge']
    list_filter   = ['item_type', 'category', 'available', 'food_type']
    search_fields = ['name', 'category']
    list_per_page = 25

    def price_display(self, obj):
        return format_html('Rs {:,.2f}', float(obj.price))
    price_display.short_description = 'Price'

    def avail_badge(self, obj):
        if obj.available:
            return format_html('<span style="color:#10b981;font-weight:700">● Available</span>')
        return format_html('<span style="color:#ef4444;font-weight:700">● Unavailable</span>')
    avail_badge.short_description = 'Status'


# ── Order ─────────────────────────────────────────────────────────────────────
@admin.register(OrderItem)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ['id', 'item_name', 'guest_name', 'room_col', 'quantity', 'total_col', 'status_badge', 'ordered_at']
    list_filter   = ['status', 'ordered_at']
    search_fields = ['item__name', 'booking__guest__name', 'booking__room__room_id']
    list_per_page = 25
    ordering      = ['-ordered_at']
    date_hierarchy = 'ordered_at'

    def item_name(self, obj): return obj.item.name if obj.item else '—'
    item_name.short_description = 'Item'

    def guest_name(self, obj): return obj.booking.guest.name if obj.booking and obj.booking.guest else '—'
    guest_name.short_description = 'Guest'

    def room_col(self, obj): return obj.booking.room.room_id if obj.booking and obj.booking.room else '—'
    room_col.short_description = 'Room'

    def total_col(self, obj):
        total = float(obj.item.price) * obj.quantity if obj.item else 0
        return format_html('Rs {:,.0f}', total)
    total_col.short_description = 'Total'

    def status_badge(self, obj):
        colors = {'undelivered':('#92400e','rgba(245,158,11,0.12)'),'delivered':('#065f46','rgba(16,185,129,0.12)'),'canceled':('#991b1b','rgba(239,68,68,0.12)')}
        c, bg = colors.get(obj.status, ('#374151','#f3f4f6'))
        return format_html('<span style="color:{};background:{};padding:3px 10px;border-radius:6px;font-size:11px;font-weight:700">{}</span>', c, bg, obj.status.title())
    status_badge.short_description = 'Status'


# ── Payment ───────────────────────────────────────────────────────────────────
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ['id', 'booking_ref', 'method_badge', 'payment_status', 'timestamp']
    list_filter   = ['payment_type', 'payment_status']
    search_fields = ['booking__booking_id', 'booking__guest__name']
    list_per_page = 25
    ordering      = ['-timestamp']

    def booking_ref(self, obj): return f'#{obj.booking.booking_id}' if obj.booking else '—'
    booking_ref.short_description = 'Booking'

    def method_badge(self, obj):
        colors = {'cash':('#065f46','rgba(16,185,129,0.12)'),'online':('#1d4ed8','rgba(59,130,246,0.12)')}
        c, bg = colors.get(obj.payment_type.lower(), ('#374151','#f3f4f6'))
        return format_html('<span style="color:{};background:{};padding:3px 10px;border-radius:6px;font-size:11px;font-weight:700">{}</span>', c, bg, obj.payment_type.title())
    method_badge.short_description = 'Method'


# ── Invoice ───────────────────────────────────────────────────────────────────
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display  = ['id', 'guest_col', 'room_col', 'check_in_date', 'check_out_date', 'method_badge', 'total_col', 'pdf_link']
    list_filter   = ['payment_type', 'check_in_date']
    search_fields = ['booking__guest__name', 'booking__booking_id', 'room__room_id']
    list_per_page = 20
    ordering      = ['-id']

    def guest_col(self, obj): return obj.booking.guest.name if obj.booking and obj.booking.guest else '—'
    guest_col.short_description = 'Guest'

    def room_col(self, obj): return obj.room.room_id if obj.room else '—'
    room_col.short_description = 'Room'

    def method_badge(self, obj):
        colors = {'cash':('#065f46','rgba(16,185,129,0.12)'),'online':('#1d4ed8','rgba(59,130,246,0.12)')}
        c, bg = colors.get(obj.payment_type.lower(), ('#374151','#f3f4f6'))
        return format_html('<span style="color:{};background:{};padding:3px 10px;border-radius:6px;font-size:11px;font-weight:700">{}</span>', c, bg, obj.payment_type.title())
    method_badge.short_description = 'Method'

    def total_col(self, obj): return format_html('<strong>Rs {:,.0f}</strong>', float(obj.total_amount))
    total_col.short_description = 'Total'

    def pdf_link(self, obj):
        if obj.invoice_pdf:
            return format_html('<a href="{}" target="_blank" style="color:#e9fe8d;font-size:11px;font-weight:700">↓ PDF</a>', obj.invoice_pdf.url)
        return format_html('<span style="color:#9ca3af;font-size:11px">—</span>')
    pdf_link.short_description = 'PDF'


# ── Housekeeping ──────────────────────────────────────────────────────────────
@admin.register(Housekeeping)
class HousekeepingAdmin(admin.ModelAdmin):
    list_display  = ['room_col', 'status_badge', 'priority_badge', 'assigned_to', 'toiletries_restocked', 'last_cleaned_at']
    list_filter   = ['status', 'priority', 'toiletries_restocked']
    search_fields = ['booking__room__room_id', 'assigned_to']
    list_per_page = 25

    def room_col(self, obj): return obj.booking.room.room_id if obj.booking and obj.booking.room else '—'
    room_col.short_description = 'Room'

    def status_badge(self, obj):
        colors = {'need-cleaning':('#ef4444','rgba(239,68,68,0.12)'),'in-progress':('#f59e0b','rgba(245,158,11,0.12)'),'inspecting':('#6366f1','rgba(99,102,241,0.12)'),'ready':('#10b981','rgba(16,185,129,0.12)')}
        c, bg = colors.get(obj.status, ('#374151','#f3f4f6'))
        return format_html('<span style="color:{};background:{};padding:3px 10px;border-radius:6px;font-size:11px;font-weight:700">{}</span>', c, bg, obj.status.replace('-',' ').title())
    status_badge.short_description = 'Status'

    def priority_badge(self, obj):
        c = {'high':'#ef4444','medium':'#f59e0b','low':'#10b981'}.get(obj.priority,'#9ca3af')
        return format_html('<span style="color:{};font-weight:700">{}</span>', c, obj.priority.title())
    priority_badge.short_description = 'Priority'


# ── Extended models ───────────────────────────────────────────────────────────
@admin.register(HousekeepingAssignment)
class HKAssignmentAdmin(admin.ModelAdmin):
    list_display = ['room_id', 'staff_name', 'shift', 'date', 'completed']
    list_filter  = ['shift', 'completed', 'date']
    search_fields = ['room_id', 'staff_name']
    list_per_page = 25

@admin.register(LostAndFound)
class LostFoundAdmin(admin.ModelAdmin):
    list_display = ['item_name', 'room_id', 'found_by', 'found_date', 'status', 'guest_name']
    list_filter  = ['status', 'found_date']
    search_fields = ['item_name', 'room_id', 'found_by', 'guest_name']
    list_per_page = 25

@admin.register(SpecialRequest)
class SpecialRequestAdmin(admin.ModelAdmin):
    list_display = ['room_id', 'guest_name', 'request_type', 'status', 'assigned_to', 'created_at']
    list_filter  = ['status', 'request_type']
    search_fields = ['room_id', 'guest_name']
    list_per_page = 25

@admin.register(LinenRecord)
class LinenAdmin(admin.ModelAdmin):
    list_display = ['linen_type', 'quantity', 'status', 'room_id', 'updated_at']
    list_filter  = ['status', 'linen_type']
    list_per_page = 25

@admin.register(FrontDeskNotification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['notif_type', 'room_id', 'guest_name', 'status', 'created_at']
    list_filter  = ['status', 'notif_type']
    list_per_page = 25

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'check_in', 'check_out', 'status', 'overtime_hours']
    list_filter  = ['status', 'date']
    search_fields = ['employee__employee_name']
    list_per_page = 25
    date_hierarchy = 'date'

@admin.register(ShiftSchedule)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'shift']
    list_filter  = ['shift', 'date']
    search_fields = ['employee__employee_name']
    list_per_page = 25

@admin.register(LeaveRequest)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'status']
    list_filter  = ['status', 'leave_type']
    search_fields = ['employee__employee_name']
    list_per_page = 25

@admin.register(PaymentGatewayConfig)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'gateway_type', 'mode', 'is_enabled']
    list_filter  = ['gateway_type', 'mode', 'is_enabled']
    list_per_page = 25

@admin.register(OTAChannelConfig)
class OTAAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'platform_name', 'platform_type', 'is_connected']
    list_filter  = ['platform_type', 'is_connected']
    list_per_page = 25

@admin.register(HousekeepingConsumable)
class ConsumableAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'inventory_item', 'qty_per_clean']
    list_per_page = 25

@admin.register(InventoryUsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display  = ['inventory_item', 'quantity_used', 'source', 'reference', 'created_at']
    list_filter   = ['source', 'created_at']
    search_fields = ['inventory_item__name', 'reference']
    list_per_page = 25
    date_hierarchy = 'created_at'
