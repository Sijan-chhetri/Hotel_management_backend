from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from .models import Room, Booking, Item, OrderItem
from .serializers import OrderItemSerializer
from django.core.exceptions import ObjectDoesNotExist
from .serializers import OrderItemSerializers

class OrderItemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        booking_id = data.get("booking_id")
        items_data = data.get("items")
        hotel_id = request.user.id

        if not all([booking_id, items_data]):
            return Response({"error": "Missing booking_id or items"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Ensure the booking belongs to the authenticated hotel
            booking = Booking.objects.get(
                booking_id=booking_id, 
                status="checked-in", 
                check_in_date__lte=now().date(), 
                check_out_date__gte=now().date(),
                room__hotel_id=hotel_id  # Filter by hotel
            )
        except Booking.DoesNotExist:
            return Response({"error": "No active booking found for this booking_id"}, status=status.HTTP_404_NOT_FOUND)

        order_items = []
        for item_entry in items_data:
            try:
                # Ensure the item belongs to the authenticated hotel
                item = Item.objects.get(
                    id=item_entry["item_id"], 
                    available=True,
                    hotel_id=hotel_id  # Filter by hotel
                )
                quantity = int(item_entry.get("quantity", 1))
                order = OrderItem.objects.create(booking=booking, item=item, quantity=quantity)
                order_items.append(order)

                # ── Integration: deduct from inventory if item is linked ──
                _deduct_inventory_for_order(order, request.user)

                # ── Integration: if item is housekeeping-type, create a task ──
                if item.category.lower() in ('housekeeping', 'towels', 'toiletries', 'cleaning'):
                    _create_housekeeping_task_from_order(order, booking)

            except Item.DoesNotExist:
                return Response(
                    {"error": f"Item with ID {item_entry['item_id']} not found or unavailable"},
                    status=status.HTTP_404_NOT_FOUND
                )

        return Response({
            "message": f"{len(order_items)} items ordered successfully.",
            "order_details": OrderItemSerializer(order_items, many=True).data,
        }, status=status.HTTP_201_CREATED)
    
    def get(self, request):
        booking_id = request.query_params.get("booking_id")
        hotel_id = request.user.id

        if booking_id:
            try:
                # Ensure the booking belongs to the authenticated hotel
                booking = Booking.objects.get(
                    booking_id=booking_id,
                    status="checked-in",
                    check_in_date__lte=now().date(),
                    check_out_date__gte=now().date(),
                    room__hotel_id=hotel_id  # Filter by hotel
                )
            except Booking.DoesNotExist:
                return Response(
                    {"error": "No current booking found for this booking_id"},
                    status=status.HTTP_404_NOT_FOUND
                )

            orders = OrderItem.objects.filter(booking=booking)
        else:
            # Get all orders for bookings belonging to this hotel
            orders = OrderItem.objects.filter(
                booking__room__hotel_id=hotel_id
            ).select_related('booking', 'booking__room', 'item')

        serialized_orders = OrderItemSerializers(orders, many=True).data
        return Response({"orders": serialized_orders}, status=status.HTTP_200_OK)
    
    def patch(self, request, *args, **kwargs):
        order_id = kwargs.get("order_id") 
        new_status = request.data.get("status")
        hotel_id = request.user.id

        if not new_status:
            return Response({"error": "Missing status"}, status=status.HTTP_400_BAD_REQUEST)

        if new_status not in dict(OrderItem.ORDER_STATUS_CHOICES):
            return Response({"error": "Invalid status value"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Ensure the order belongs to the authenticated hotel
            order_item = OrderItem.objects.get(
                id=order_id,
                booking__room__hotel_id=hotel_id  # Filter by hotel
            )
        except OrderItem.DoesNotExist:
            return Response({"error": "Order item not found"}, status=status.HTTP_404_NOT_FOUND)

        order_item.status = new_status
        order_item.save()

        return Response({
            "message": "Order status updated successfully",
            "order_details": OrderItemSerializer(order_item).data
        }, status=status.HTTP_200_OK)



# ── Integration helpers ───────────────────────────────────────────────────────

def _deduct_inventory_for_order(order_item, hotel_user):
    """Deduct inventory stock when an order is placed for items marked as order-deductible."""
    from .models import HousekeepingConsumable, InventoryUsageLog, FrontDeskNotification, InventoryItem
    LOW = 10

    # Find inventory items belonging to this hotel that are order-deductible and match by name
    inv_items = InventoryItem.objects.filter(
        user=hotel_user,
        usage_type__in=('order', 'both'),
        name__iexact=order_item.item.name,
    )

    for inv in inv_items:
        deduct = min(order_item.quantity, inv.quantity)
        if deduct <= 0:
            continue
        inv.quantity -= deduct
        inv.save(update_fields=['quantity'])

        InventoryUsageLog.objects.create(
            hotel=hotel_user,
            inventory_item=inv,
            quantity_used=deduct,
            source='order',
            reference=f"Order #{order_item.id} — {order_item.item.name}",
        )

        if inv.quantity < LOW:
            FrontDeskNotification.objects.create(
                hotel=hotel_user,
                room_id=order_item.booking.room.room_id,
                notif_type='general',
                message=f'Low stock alert: {inv.name} has only {inv.quantity} units remaining.',
                status='unread',
            )


def _create_housekeeping_task_from_order(order_item, booking):
    """Auto-create a SpecialRequest housekeeping task when a guest orders a housekeeping item."""
    from .models import SpecialRequest, FrontDeskNotification

    category = order_item.item.category.lower()
    type_map = {
        'towels':      'towels',
        'housekeeping': 'cleaning',
        'toiletries':  'amenities',
        'cleaning':    'cleaning',
    }
    request_type = type_map.get(category, 'other')

    SpecialRequest.objects.create(
        hotel=booking.room.hotel,
        room_id=booking.room.room_id,
        guest_name=booking.guest.name,
        request_type=request_type,
        description=f"Guest ordered: {order_item.item.name} × {order_item.quantity}",
        status='pending',
    )

    FrontDeskNotification.objects.create(
        hotel=booking.room.hotel,
        room_id=booking.room.room_id,
        guest_name=booking.guest.name,
        notif_type='special_request',
        message=f"Housekeeping task created: {order_item.item.name} × {order_item.quantity} for Room {booking.room.room_id}.",
        status='unread',
    )
