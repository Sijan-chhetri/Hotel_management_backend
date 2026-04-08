from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Booking, Payment, Housekeeping
from .serializers import  RoomBookingSerializer,PaymentSerializer
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import requests
from django.conf import settings
from .models import Booking 
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from .models import Booking

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from .models import Booking


logger = logging.getLogger(__name__)
import logging
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import redirect
from .models import Booking


import requests

class BookingDetailView(APIView):
    permission_classes = [IsAuthenticated]
    """
    Retrieve booking details including room information.
    """
    def get(self, request, booking_id):
        booking = get_object_or_404(
            Booking.objects.select_related('room', 'room__hotel', 'guest')
                           .prefetch_related('orders', 'orders__item'),
            booking_id=booking_id
        )
        serializer = RoomBookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)











def calculate_total_amount_in_paisa(booking):
    """
    Calculate the total amount (room + orders) for a booking in paisa.
    """
    from datetime import datetime
    from django.utils.timezone import make_aware

    check_in = booking.check_in_date
    check_out = booking.check_out_date

    if isinstance(check_in, datetime) and check_in.tzinfo is None:
        check_in = make_aware(check_in)
    if isinstance(check_out, datetime) and check_out.tzinfo is None:
        check_out = make_aware(check_out)

    duration = (check_out - check_in).days
    if duration <= 0:
        duration = 1

    room_rate = float(booking.room.rate) if booking.room and booking.room.rate else 0
    room_total = room_rate * duration

    orders = booking.orders.all()  # uses related_name

    order_total = sum(
        (float(order.item.price) * order.quantity)
        for order in orders
        if order.item and order.status.lower() not in ['cancelled', 'canceled']
    )


    total_amount = room_total + order_total
    return int(total_amount * 100)  # to paisa




logger = logging.getLogger(__name__)
class KhaltiPaymentAPI(APIView):
    """
    API View for initiating Khalti payment.
    Resolves hotel via booking.room.hotel and uses that hotel's
    configured Khalti credentials instead of a hardcoded key.
    """

    def post(self, request, *args, **kwargs):
        from .models import PaymentGatewayConfig
        from .encryption import encryption_service

        booking_id = request.data.get("booking_id")
        if not booking_id:
            return Response({'error': 'Booking ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            booking = Booking.objects.select_related('room__hotel').get(booking_id=booking_id)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

        # Resolve hotel from booking → room → hotel
        hotel = booking.room.hotel

        # Load this hotel's Khalti config — no fallback
        try:
            config = PaymentGatewayConfig.objects.get(
                hotel=hotel, gateway_type='khalti', is_enabled=True
            )
            try:
                secret_key = encryption_service.decrypt(config.secret_key)
            except Exception:
                logger.error(f"Failed to decrypt Khalti secret for hotel {hotel.id}")
                return Response({'error': 'Payment configuration error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except PaymentGatewayConfig.DoesNotExist:
            return Response(
                {'error': 'Khalti is not configured for this hotel. Go to Settings → Payment & OTA to add your Khalti credentials.'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        api_url = "https://a.khalti.com/api/v2/epayment/initiate/"
        headers = {
            'Authorization': f'Key {secret_key}',
            'Content-Type': 'application/json',
        }

        amount = calculate_total_amount_in_paisa(booking)
        return_url = f"{request.scheme}://{request.get_host().replace('8000', '3000')}/payment-success"

        payload = {
            'amount': amount,
            'return_url': return_url,
            'website_url': f"{request.scheme}://{request.get_host().replace('8000', '3000')}",
            'purchase_order_id': str(booking_id),
            'purchase_order_name': f"Room booking: {booking.room.room_type}",
        }

        try:
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return Response({'payment_url': data.get('payment_url')}, status=status.HTTP_200_OK)
        except requests.exceptions.HTTPError as http_err:
            return Response({'error': f'Gateway error: {http_err}'}, status=status.HTTP_400_BAD_REQUEST)
        except requests.exceptions.RequestException as e:
            return Response({'error': f'Gateway unreachable, please try again.'}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            return Response({'error': f'An error occurred: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
     
        
def _trigger_housekeeping_after_checkout(booking):
    """Set housekeeping to need-cleaning + high priority after checkout."""
    from django.utils.timezone import now as tz_now
    hk, created = Housekeeping.objects.get_or_create(
        booking=booking,
        defaults={'status': 'need-cleaning', 'priority': 'high', 'toiletries_restocked': False}
    )
    if not created:
        hk.status = 'need-cleaning'
        hk.priority = 'high'
        hk.toiletries_restocked = False
        hk.notes = f'Auto-triggered after checkout on {tz_now().strftime("%Y-%m-%d %H:%M")}'
        hk.save()


class KhaltiVerifyAPI(APIView):
    def get(self, request):
        status_param = request.GET.get('status')
        amount = request.GET.get('amount')
        transaction_id = request.GET.get('transaction_id')
        booking_id = request.GET.get('booking_id')

        if status_param and status_param.lower() == 'completed':
            try:
                booking = get_object_or_404(Booking, booking_id=booking_id)

                if Payment.objects.filter(booking=booking, payment_type='online').exists():
                    return Response({"error": "Payment already exists."}, status=status.HTTP_400_BAD_REQUEST)

                payment = Payment.objects.create(
                    booking=booking,
                    payment_type='online',
                    payment_status='Completed',
                    timestamp=now()
                )

                booking.status = 'checked-out'
                booking.save()

                _trigger_housekeeping_after_checkout(booking)

                return Response(
                    {"message": "✅ Payment verified successfully.", "id": payment.id},
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({"error": f"Payment not completed. Status: {status_param}"}, status=status.HTTP_402_PAYMENT_REQUIRED)




    

    
class PaymentView(APIView):
    
    def post(self, request):
        booking_id = request.data.get("booking_id")
        payment_type = request.data.get("payment_type")
        

        if not booking_id or not payment_type:
            return Response({"error": "Missing booking ID or payment type"}, status=status.HTTP_400_BAD_REQUEST)

        booking = get_object_or_404(Booking, booking_id=booking_id)


        # Create the payment and update booking
        payment = Payment.objects.create(booking=booking, payment_type=payment_type)
        booking.status = 'checked-out'
        booking.save()

        from .models import Housekeeping
        _trigger_housekeeping_after_checkout(booking)

        serializer = PaymentSerializer(payment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

