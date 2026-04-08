"""
Integration layer: Housekeeping ↔ Inventory ↔ Orders
- Room cleaned  → deduct consumables from inventory, log usage, fire low-stock alerts
- Order placed  → deduct food/beverage items from inventory (if linked), log usage
- Low-stock     → list items below threshold
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from .models import (
    HousekeepingConsumable, InventoryUsageLog,
    InventoryItem, FrontDeskNotification,
)

LOW_STOCK_THRESHOLD = 10  # items below this trigger an alert


# ── Serializers ──────────────────────────────────────────────────────────────

class ConsumableSerializer(serializers.ModelSerializer):
    item_name     = serializers.CharField(source='inventory_item.name', read_only=True)
    item_category = serializers.CharField(source='inventory_item.category', read_only=True)
    current_stock = serializers.IntegerField(source='inventory_item.quantity', read_only=True)

    class Meta:
        model = HousekeepingConsumable
        fields = ['id', 'inventory_item', 'item_name', 'item_category', 'current_stock', 'qty_per_clean']
        read_only_fields = ['hotel']


class UsageLogSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='inventory_item.name', read_only=True)

    class Meta:
        model = InventoryUsageLog
        fields = ['id', 'item_name', 'quantity_used', 'source', 'reference', 'created_at']
        read_only_fields = ['hotel', 'created_at']


# ── Consumables config ────────────────────────────────────────────────────────

class ConsumableListView(APIView):
    """List / add consumables that housekeeping uses per room clean."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = HousekeepingConsumable.objects.filter(hotel=request.user).select_related('inventory_item')
        return Response(ConsumableSerializer(qs, many=True).data)

    def post(self, request):
        s = ConsumableSerializer(data=request.data)
        if s.is_valid():
            # verify item belongs to this hotel
            item = s.validated_data['inventory_item']
            if item.user_id != request.user.id:
                return Response({'detail': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)
            s.save(hotel=request.user)
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class ConsumableDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, pk, user):
        try:
            return HousekeepingConsumable.objects.get(pk=pk, hotel=user), None
        except HousekeepingConsumable.DoesNotExist:
            return None, Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        obj, err = self._get(pk, request.user)
        if err: return err
        s = ConsumableSerializer(obj, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, err = self._get(pk, request.user)
        if err: return err
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Room cleaned → deduct inventory ──────────────────────────────────────────

class RoomCleanedDeductView(APIView):
    """
    Called when a room is marked as cleaned (status → ready).
    Deducts all configured consumables from inventory and logs usage.
    Returns list of items that went low-stock after deduction.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        room_id    = request.data.get('room_id', '')
        guest_name = request.data.get('guest_name', '')
        reference  = f"Room {room_id} cleaned" + (f" ({guest_name})" if guest_name else "")

        consumables = HousekeepingConsumable.objects.filter(
            hotel=request.user
        ).select_related('inventory_item')

        low_stock_alerts = []
        deducted = []

        for c in consumables:
            item = c.inventory_item
            qty  = c.qty_per_clean

            if item.quantity <= 0:
                continue  # nothing to deduct

            actual_deduct = min(qty, item.quantity)
            item.quantity -= actual_deduct
            item.save(update_fields=['quantity'])

            InventoryUsageLog.objects.create(
                hotel=request.user,
                inventory_item=item,
                quantity_used=actual_deduct,
                source='housekeeping',
                reference=reference,
            )

            deducted.append({'item': item.name, 'deducted': actual_deduct, 'remaining': item.quantity})

            # Fire low-stock notification
            if item.quantity < LOW_STOCK_THRESHOLD:
                low_stock_alerts.append(item.name)
                FrontDeskNotification.objects.create(
                    hotel=request.user,
                    room_id=room_id,
                    notif_type='general',
                    message=f'Low stock alert: {item.name} has only {item.quantity} units remaining.',
                    status='unread',
                )

        return Response({
            'deducted': deducted,
            'low_stock_alerts': low_stock_alerts,
        }, status=status.HTTP_200_OK)


# ── Usage log ─────────────────────────────────────────────────────────────────

class UsageLogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = InventoryUsageLog.objects.filter(hotel=request.user).select_related('inventory_item')
        source = request.query_params.get('source')
        if source:
            qs = qs.filter(source=source)
        return Response(UsageLogSerializer(qs[:100], many=True).data)  # last 100


# ── Low-stock list ────────────────────────────────────────────────────────────

class LowStockView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        threshold = int(request.query_params.get('threshold', LOW_STOCK_THRESHOLD))
        items = InventoryItem.objects.filter(user=request.user, quantity__lt=threshold)
        data = [{'id': i.id, 'name': i.name, 'category': i.category, 'quantity': i.quantity, 'vendor': i.vendor} for i in items]
        return Response(data)
