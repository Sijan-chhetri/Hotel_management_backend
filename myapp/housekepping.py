from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Housekeeping, Booking
from .serializers import HousekeepingSerializer,  BookingRoom
from datetime import date



class HousekeepingDetailAPIView(APIView):
    def get(self, request, pk):
        try:
            housekeeping = Housekeeping.objects.get(pk=pk)
        except Housekeeping.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = HousekeepingSerializer(housekeeping)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        try:
            housekeeping = Housekeeping.objects.get(pk=pk)
        except Housekeeping.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = HousekeepingSerializer(housekeeping, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




from datetime import date
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Booking
from .serializers import RoomBookingSerializer

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.timezone import now
from datetime import date


class ActiveCheckedInAPIView(APIView):
    permission_classes = [IsAuthenticated]  
    
    def get(self, request):
        today = date.today()
        hotel_id = request.user.id
        
        # Filter bookings by hotel and display both room and booking
        checked_in_bookings = Booking.objects.filter(
            status="checked-in",
            room__hotel_id=hotel_id  # Filter by hotel
        ).select_related('room')
        
        housekeeping_records = Housekeeping.objects.filter(
            booking__room__hotel_id=hotel_id  # Filter by hotel
        ).select_related('booking', 'booking__room')

        room_to_best_record = {}
        
        for record in housekeeping_records:
            room_id = record.booking.room_id
            check_in = record.booking.check_in_date

            if room_id not in room_to_best_record:
                room_to_best_record[room_id] = record
            else:
                existing = room_to_best_record[room_id]
                existing_diff = abs((existing.booking.check_in_date - today).days)
                current_diff = abs((check_in - today).days)

                if current_diff < existing_diff:
                    room_to_best_record[room_id] = record

        rooms_with_housekeeping = set(room_to_best_record.keys())
        missing_rooms = []
        for booking in checked_in_bookings:
            room_id = booking.room_id
            if room_id not in rooms_with_housekeeping:
                # Create a dummy object with only booking (safe fallback)
                missing_record = Housekeeping(booking=booking)
                # If fields like cleaned or notes exist, you can set them here
                missing_rooms.append(missing_record)

        final_records = list(room_to_best_record.values()) + missing_rooms
        serializer = HousekeepingSerializer(final_records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Housekeeping
from .serializers import HousekeepingSerializer

class UpdateHousekeepingAPIView(APIView):

    def get_housekeeping(self, room_id):
        try:
            return Housekeeping.objects.get(booking__room__room_id=room_id)
        except Housekeeping.DoesNotExist:
            return None

    def post(self, request, room_id):
        housekeeping = self.get_housekeeping(room_id)
        if not housekeeping:
            return Response({"error": "Housekeeping record not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = HousekeepingSerializer(housekeeping, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Housekeeping status updated successfully (POST).",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, room_id):
        housekeeping = self.get_housekeeping(room_id)
        if not housekeeping:
            return Response({"error": "Housekeeping record not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = HousekeepingSerializer(housekeeping, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Housekeeping status updated successfully (PATCH).",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from datetime import date
from .models import Booking, Housekeeping
from .serializers import HousekeepingSerializer


class CreateHousekeepingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        today = date.today()
        room_id = request.data.get('room_id')
        hotel_id = request.user.id

        # All updatable fields
        updatable = {
            'status':               request.data.get('status'),
            'priority':             request.data.get('priority'),
            'notes':                request.data.get('notes'),
            'toiletries_restocked': request.data.get('toiletries_restocked'),
            'last_cleaned_at':      request.data.get('last_cleaned_at'),
            'assigned_to':          request.data.get('assigned_to'),
        }
        # Remove keys not provided in the request
        updatable = {k: v for k, v in updatable.items() if v is not None}

        try:
            booking = Booking.objects.filter(
                room__room_id=room_id,
                room__hotel_id=hotel_id,
                check_in_date__lte=today,
                status__in=['booked', 'checked-in', 'checked-out']
            ).order_by('-check_in_date').first()

            if not booking:
                return Response({'error': 'No matching booking found for that room.'}, status=status.HTTP_404_NOT_FOUND)

            if hasattr(booking, 'housekeeping'):
                housekeeping = booking.housekeeping
                for field, value in updatable.items():
                    setattr(housekeeping, field, value)
                housekeeping.save()
            else:
                housekeeping = Housekeeping.objects.create(
                    booking=booking,
                    **{k: v for k, v in updatable.items() if v is not None}
                )

            serializer = HousekeepingSerializer(housekeeping)
            return Response({'message': 'Housekeeping updated.', 'data': serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
