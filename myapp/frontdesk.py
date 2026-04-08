from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from .models import FrontDeskNotification, GuestPreferences, Booking, Housekeeping


# ── Serializers ──────────────────────────────────────────────────────────────

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FrontDeskNotification
        fields = '__all__'
        read_only_fields = ['hotel', 'created_at']


class GuestPreferencesSerializer(serializers.ModelSerializer):
    booking_id   = serializers.IntegerField(source='booking.booking_id', read_only=True)
    guest_name   = serializers.CharField(source='booking.guest.name', read_only=True)
    room_id      = serializers.CharField(source='booking.room.room_id', read_only=True)
    check_in_date  = serializers.DateField(source='booking.check_in_date', read_only=True)
    check_out_date = serializers.DateField(source='booking.check_out_date', read_only=True)
    booking_status = serializers.CharField(source='booking.status', read_only=True)
    booking_notes  = serializers.CharField(source='booking.notes', read_only=True)
    priority       = serializers.SerializerMethodField()

    def get_priority(self, obj):
        from datetime import date
        today = date.today()
        delta = (obj.booking.check_in_date - today).days
        if delta <= 1:
            return 'high'
        elif delta <= 3:
            return 'medium'
        return 'low'

    class Meta:
        model = GuestPreferences
        fields = [
            'id', 'booking_id', 'guest_name', 'room_id', 'booking_status',
            'check_in_date', 'check_out_date', 'priority',
            'booking_notes',
            'notes', 'preferences',
            'extra_bed', 'baby_crib', 'late_checkout', 'early_checkin',
            'updated_at',
        ]
        read_only_fields = [
            'booking_id', 'guest_name', 'room_id', 'booking_status',
            'check_in_date', 'check_out_date', 'priority', 'booking_notes', 'updated_at',
        ]


# ── Notifications ─────────────────────────────────────────────────────────────

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = FrontDeskNotification.objects.filter(hotel=request.user)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return Response(NotificationSerializer(qs, many=True).data)

    def post(self, request):
        s = NotificationSerializer(data=request.data)
        if s.is_valid():
            s.save(hotel=request.user)
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, pk, user):
        try:
            return FrontDeskNotification.objects.get(pk=pk, hotel=user), None
        except FrontDeskNotification.DoesNotExist:
            return None, Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        obj, err = self._get(pk, request.user)
        if err: return err
        s = NotificationSerializer(obj, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, err = self._get(pk, request.user)
        if err: return err
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Notify front desk when a room is marked ready ────────────────────────────

class NotifyRoomReadyView(APIView):
    """Called when housekeeping marks a room as ready — auto-creates a notification."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        room_id    = request.data.get('room_id')
        guest_name = request.data.get('guest_name', '')
        if not room_id:
            return Response({'detail': 'room_id required.'}, status=status.HTTP_400_BAD_REQUEST)

        notif = FrontDeskNotification.objects.create(
            hotel=request.user,
            room_id=room_id,
            guest_name=guest_name,
            notif_type='room_ready',
            message=f'Room {room_id} is clean and ready for check-in.',
            status='unread',
        )
        return Response(NotificationSerializer(notif).data, status=status.HTTP_201_CREATED)


# ── Guest Preferences ─────────────────────────────────────────────────────────

class GuestPreferencesListView(APIView):
    """List all upcoming + checked-in bookings sorted by check-in proximity (priority)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from datetime import date
        today = date.today()
        bookings = Booking.objects.filter(
            room__hotel=request.user,
            status__in=['booked', 'checked-in'],
            check_in_date__gte=today,
        ).select_related('guest', 'room').order_by('check_in_date')

        result = []
        for b in bookings:
            prefs, _ = GuestPreferences.objects.get_or_create(booking=b)
            result.append(GuestPreferencesSerializer(prefs).data)
        return Response(result)


class GuestPreferencesDetailView(APIView):
    """Get or update preferences for a specific booking."""
    permission_classes = [IsAuthenticated]

    def _get(self, booking_id, user):
        try:
            booking = Booking.objects.get(booking_id=booking_id, room__hotel=user)
            prefs, _ = GuestPreferences.objects.get_or_create(booking=booking)
            return prefs, None
        except Booking.DoesNotExist:
            return None, Response({'detail': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, booking_id):
        prefs, err = self._get(booking_id, request.user)
        if err: return err
        return Response(GuestPreferencesSerializer(prefs).data)

    def patch(self, request, booking_id):
        prefs, err = self._get(booking_id, request.user)
        if err: return err
        s = GuestPreferencesSerializer(prefs, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            # auto-create a notification for front desk
            FrontDeskNotification.objects.create(
                hotel=request.user,
                room_id=prefs.booking.room.room_id,
                guest_name=prefs.booking.guest.name,
                notif_type='guest_preference',
                message=f'Guest preferences updated for Room {prefs.booking.room.room_id} ({prefs.booking.guest.name}).',
                status='unread',
            )
            return Response(GuestPreferencesSerializer(prefs).data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
