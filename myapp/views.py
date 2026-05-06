from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer, RoomSerializer, EmployeeSerializer, GuestSerializer, BookingSerializer, BookingCreateSerializer, BookingStatusUpdateSerializer # Updated import
from .models import User, Room, Booking, Employee,  Guest
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from datetime import timedelta
from django.contrib.auth import login
from rest_framework_simplejwt.settings import api_settings
from django.db import IntegrityError
from rest_framework import generics
from django.shortcuts import get_object_or_404



class RegisterHotelView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                user = serializer.save()
                # Set 7-day trial expiry
                user.trial_expires_at = timezone.now() + timedelta(days=7)
                user.is_trial = True
                user.save(update_fields=['trial_expires_at', 'is_trial'])

                response_data = {
                    "id": user.id,
                    "hotel_name": user.hotel_name,
                    "email": user.email,
                    "trial_expires_at": user.trial_expires_at,
                    "message": "Hotel registered successfully. Your 7-day free trial has started!"
                }
                return Response(response_data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(
                    {"error": "An unexpected error occurred during registration.", "details": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)








from datetime import timedelta
from django.contrib.auth.hashers import check_password
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login

from .models import User, SubUser  # Import your User and SubUser models

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user = User.objects.get(email=email)

            # Check if main user is active
            if not user.is_active:
                return Response({"error": "Your account is banned."}, status=status.HTTP_403_FORBIDDEN)

            if not check_password(password, user.password):
                raise User.DoesNotExist()

            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            login(request, user)

            access_token["hotel_id"] = user.id  
            access_token["role"] = "admin"  
            access_token.set_exp(lifetime=timedelta(days=30))

            response_data = {
                "message": "Login successful",
                "access_token": str(access_token),
                "refresh_token": str(refresh),
                "user_id": user.id,
                "hotel_name": user.hotel_name,
                "hotel_id": user.id,
                "role": "admin",
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            try:
                subuser = SubUser.objects.get(email=email)

                if not subuser.is_active:
                    return Response({"error": "Subuser account is inactive."}, status=status.HTTP_403_FORBIDDEN)

                if not check_password(password, subuser.password):
                    raise SubUser.DoesNotExist()

                refresh = RefreshToken.for_user(subuser.user)
                access_token = refresh.access_token
                login(request, subuser.user)

                access_token["hotel_id"] = subuser.user.id
                access_token["role"] = subuser.role
                access_token.set_exp(lifetime=timedelta(days=30))

                response_data = {
                    "message": "Subuser login successful",
                    "access_token": str(access_token),
                    "refresh_token": str(refresh),
                    "user_id": subuser.user.id,
                    "hotel_name": subuser.user.hotel_name,
                    "hotel_id": subuser.user.id,
                    "subuser_email": subuser.email,
                    "role": subuser.role,
                }
                return Response(response_data, status=status.HTTP_200_OK)

            except SubUser.DoesNotExist:
                return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)


class UserDetailView(APIView):
    """
    View for retrieving and updating user details.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Retrieve the user details based on the authenticated user.
        """
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        """
        Update the user details based on the authenticated user.
        """
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)  # partial=True allows updating only provided fields
        if serializer.is_valid():
            # If the password is included in the update, hash it before saving
            if 'password' in request.data:
                user.set_password(request.data['password'])
                user.save()
            
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)












class BookingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            guest_name = request.data.get("guest_name")
            room_id = request.data.get("room_id")  # Expecting room_id as input
            check_in_date = request.data.get("check_in_date")
            check_out_date = request.data.get("check_out_date")
            status_value = request.data.get("status", "booked")  # Default to "booked"

            # Validate required fields
            if not guest_name or not room_id or not check_in_date or not check_out_date:
                return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the room exists
            try:
                room = Room.objects.get(room_id=room_id)
            except Room.DoesNotExist:
                return Response({"error": "Room does not exist"}, status=status.HTTP_400_BAD_REQUEST)

            # Create the booking
            booking = Booking.objects.create(
                guest_name=guest_name,
                room=room,  # Assign the Room object
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                status=status_value
            )

            # Serialize and return response
            serializer = BookingSerializer(booking)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# Guest Views
class GuestListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GuestSerializer

    def get_queryset(self):
        hotel_id = self.request.user.id
        return Guest.objects.filter(
            bookings__room__hotel_id=hotel_id
        ).distinct()

class GuestDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Guest.objects.all()
    serializer_class = GuestSerializer

# Booking Views
