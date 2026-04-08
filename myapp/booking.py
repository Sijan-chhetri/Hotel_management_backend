from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import  BookingSerializer, RoomBookingSerializer
from .models import Booking, Guest
from django.core.mail import send_mail
from django.conf import settings


from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

class BookingListCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    """
    Create a booking with additional logic for availability check and guest linking.
    """

    def get(self, request):
        hotel_id = request.user.id
        bookings = Booking.objects.filter(
            room__hotel_id=hotel_id
        ).select_related(
            'room', 'room__hotel', 'guest'
        ).prefetch_related(
            'orders', 'orders__item'
        )
        serializer = RoomBookingSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            guest_data = serializer.validated_data.pop('guest')
            room = serializer.validated_data['room']
            check_in_date = serializer.validated_data['check_in_date']
            check_out_date = serializer.validated_data['check_out_date']

            # Check room availability
            overlapping_bookings = Booking.objects.filter(
                room=room,
                status__in=['booked', 'checked-in'],
                check_in_date__lt=check_out_date,
                check_out_date__gt=check_in_date
            )

            if overlapping_bookings.exists():
                return Response({"error": "Room is already booked for the selected dates."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Create or get guest
            guest, created = Guest.objects.get_or_create(
                email=guest_data['email'],
                defaults={
                    'name': guest_data['name'],
                    'phone': guest_data['phone'],
                    'gender': guest_data.get('gender', 'Male'),
                    'dob': guest_data.get('dob'),
                    'nationality': guest_data.get('nationality'),
                    'doc_type': guest_data['doc_type'],
                    'doc_number': guest_data['doc_number']
                }
            )

            # Create booking
            booking = Booking.objects.create(guest=guest, **serializer.validated_data)

            # Send booking confirmation email
            email_sent = send_booking_email(booking)

            response_serializer = BookingSerializer(booking)

            if email_sent:
                return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    response_serializer.data,
                    status=status.HTTP_201_CREATED,
                    headers={"X-Email-Status": "Failed to send confirmation email."}
                )

        # DEBUG: Print validation errors
        print("Validation Errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    def patch(self, request, id):
        try:
            booking = Booking.objects.get(booking_id=id)  # Use booking_id instead of id
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = BookingSerializer(booking, data=request.data, partial=True)  # partial=True allows updating just certain fields
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Booking, Guest, Room
from .serializers import BookingSerializer
from django.db import transaction

class MultiBookingView(APIView):
    def post(self, request):
        data = request.data
        guest_data = data.get("guest")
        room_ids = data.get("rooms", [])
        check_in_date = data.get("check_in_date")
        check_out_date = data.get("check_out_date")

        if not guest_data or not room_ids or not check_in_date or not check_out_date:
            return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # Create or get guest
                guest, _ = Guest.objects.get_or_create(
                    email=guest_data['email'],
                    defaults={
                        'name': guest_data['name'],
                        'phone': guest_data['phone'],
                        'gender': guest_data.get('gender', 'Male'),
                        'dob': guest_data.get('dob'),
                        'nationality': guest_data.get('nationality'),
                        'doc_type': guest_data['doc_type'],
                        'doc_number': guest_data['doc_number']
                    }
                )

                successful_bookings = []
                successful_booking_objects = []
                failed_rooms = []

                for room_id in room_ids:
                    try:
                        room = Room.objects.get(id=room_id)
                    except Room.DoesNotExist:
                        failed_rooms.append({"room_id": room_id, "error": "Room not found."})
                        continue

                    overlapping = Booking.objects.filter(
                        room=room,
                        status__in=["booked", "checked-in"],
                        check_in_date__lt=check_out_date,
                        check_out_date__gt=check_in_date
                    )

                    if overlapping.exists():
                        failed_rooms.append({"room_id": room_id, "error": "Room is already booked."})
                        continue

                    booking = Booking.objects.create(
                        guest=guest,
                        room=room,
                        check_in_date=check_in_date,
                        check_out_date=check_out_date,
                        status="booked"
                    )

                    successful_bookings.append(BookingSerializer(booking).data)
                    successful_booking_objects.append(booking)

                # Send ONE summary email for all successful bookings
                if successful_booking_objects:
                    send_multi_booking_email(guest, successful_booking_objects, check_in_date, check_out_date)

                return Response({
                    "success_count": len(successful_bookings),
                    "failures": failed_rooms,
                    "bookings": successful_bookings
                }, status=status.HTTP_201_CREATED if successful_bookings else status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    

def send_booking_email(booking):
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    from datetime import date

    guest = booking.guest
    room = booking.room

    # Handle both date objects and strings
    def to_date(d):
        if isinstance(d, date):
            return d
        return date.fromisoformat(str(d))

    check_in = to_date(booking.check_in_date)
    check_out = to_date(booking.check_out_date)
    nights = max(1, (check_out - check_in).days)
    total_amount = float(room.rate) * nights

    context = {
        'guest_name': guest.name,
        'booking_id': booking.booking_id,
        'room_id': room.room_id,
        'room_type': room.room_type.capitalize(),
        'room_rate': f"{float(room.rate):,.0f}",
        'check_in_date': check_in.strftime('%B %d, %Y'),
        'check_out_date': check_out.strftime('%B %d, %Y'),
        'nights': nights,
        'nights_label': f"{nights} night{'s' if nights != 1 else ''}",
        'total_amount': f"{total_amount:,.0f}",
    }

    html_message = render_to_string('booking_confirmation_email.html', context)
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject=f"Booking Confirmed — #{booking.booking_id} | The HMS",
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[guest.email],
            fail_silently=False,
            html_message=html_message,
        )
        return True
    except Exception as e:
        # Retry once on transient SMTP disconnect
        try:
            send_mail(
                subject=f"Booking Confirmed — #{booking.booking_id} | The HMS",
                message=plain_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[guest.email],
                fail_silently=False,
                html_message=html_message,
            )
            return True
        except Exception as e2:
            print(f"Error sending booking email: {e2}")
            return False



def send_multi_booking_email(guest, bookings, check_in_date, check_out_date):
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    from datetime import date

    def to_date(d):
        if isinstance(d, date):
            return d
        return date.fromisoformat(str(d))

    check_in = to_date(check_in_date)
    check_out = to_date(check_out_date)
    nights = max(1, (check_out - check_in).days)

    rooms_info = []
    grand_total = 0.0
    for b in bookings:
        rate = float(b.room.rate)
        room_total = rate * nights
        grand_total += room_total
        rooms_info.append({
            'booking_id': b.booking_id,
            'room_id': b.room.room_id,
            'room_type': b.room.room_type.capitalize(),
            'rate': f"{rate:,.0f}",
            'room_total': f"{room_total:,.0f}",
        })

    context = {
        'guest_name': guest.name,
        'room_count': len(bookings),
        'rooms': rooms_info,
        'check_in_date': check_in.strftime('%B %d, %Y'),
        'check_out_date': check_out.strftime('%B %d, %Y'),
        'nights': nights,
        'nights_label': f"{nights} night{'s' if nights != 1 else ''}",
        'grand_total': f"{grand_total:,.0f}",
    }

    html_message = render_to_string('multi_booking_confirmation_email.html', context)
    plain_message = strip_tags(html_message)

    subject = f"{len(bookings)} Rooms Confirmed | The HMS"

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[guest.email],
            fail_silently=False,
            html_message=html_message,
        )
        return True
    except Exception:
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[guest.email],
                fail_silently=False,
                html_message=html_message,
            )
            return True
        except Exception as e:
            print(f"Error sending multi booking email: {e}")
            return False
