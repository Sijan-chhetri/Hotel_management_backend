from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import now
from .models import Room, Booking, Item, OrderItem
from .serializers import OrderItemSerializer
from django.core.exceptions import ObjectDoesNotExist
from .serializers import OrderItemSerializers

class OrderItemView(APIView):

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

