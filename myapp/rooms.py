from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Room
from .serializers import RoomSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db import IntegrityError







class AddRoomView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        room_data = request.data.copy()
        room_data["hotel"] = user.id  

        serializer = RoomSerializer(data=room_data)
        try:
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "Room added successfully!"},
                    status=status.HTTP_201_CREATED,
                )
            else:
                
                missing_fields = {
                    field: errors for field, errors in serializer.errors.items()
                }
                print("Validation errors:", missing_fields) 
                
                return Response(
                    {"error": "Validation failed", "details": missing_fields},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except IntegrityError:
            return Response(
                {"error": "A room with this ID already exists for this hotel."},
                status=status.HTTP_400_BAD_REQUEST,
            )


    

class RoomListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
       
        user = request.user
        print(f"Authenticated User ID: {user.id}")
        
        # Fetch only the rooms belonging to the authenticated user's hotel
        rooms = Room.objects.filter(hotel=user.id).select_related('hotel')
        
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)





class EditRoomView(APIView):
    def get_object(self, room_id):
        
        try:
            return Room.objects.get(room_id=room_id)
        except Room.DoesNotExist:
            return None

    def get(self, request, room_id):
        room = self.get_object(room_id)
        if room is None:
            return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = RoomSerializer(room)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, room_id):
        room = self.get_object(room_id)
        if room is None:
            return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = RoomSerializer(room, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Room updated successfully!"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, room_id):
        """
        Handle DELETE requests to remove a room by room_id.
        """
        room = self.get_object(room_id)
        if room is None:
            return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)

        room.delete()
        return Response({"message": "Room deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
