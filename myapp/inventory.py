from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import InventoryItem
from .serializers import InventorySerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import InventoryItem
from .serializers import InventorySerializer
from rest_framework.exceptions import ValidationError

class InventoryListCreateAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve inventory items for the authenticated hotel only"""
        hotel_id = request.user.id
        inventory = InventoryItem.objects.filter(user_id=hotel_id)
        serializer = InventorySerializer(inventory, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    def post(self, request):
            """Create a new inventory item or handle bulk creation"""
            try:
                
                user_id = request.user.id  # Get the authenticated user's ID
                print("Authenticated user ID:", user_id)  # Log the authenticated user ID

                
                print("Received data:", request.data)  

                if isinstance(request.data, list):
             
                    for item in request.data:
                        if 'user' not in item:  # Check if the user field is already present
                            item['user'] = user_id  # Ensure each item is linked to the authenticated user

                    # Serialize the bulk data
                    serializer = InventorySerializer(data=request.data, many=True)

                    if serializer.is_valid():
                        # Log the serialized data (after validation)
                        print("Serialized bulk data:", serializer.validated_data)

                        # Save all inventory items
                        serializer.save()
                        return Response({"message": "Inventory items added successfully!"}, status=status.HTTP_201_CREATED)
                    return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

                # Handle single inventory item creation (if the data is not a list)
                if 'user' not in request.data:
                    # If user ID is not provided, automatically assign the logged-in user's ID
                    request.data['user'] = user_id

                serializer = InventorySerializer(data=request.data)
                if serializer.is_valid():
                    # Log the serialized data (after validation)
                    print("Serialized single data:", serializer.validated_data)

                    # Save the single inventory item
                    serializer.save(user=request.user)  # Ensure the item is linked to the current user
                    return Response({"message": "Inventory item added successfully!"}, status=status.HTTP_201_CREATED)

                # If the serializer is not valid, return specific validation errors
                return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            except ValidationError as e:
                # Handle validation errors in a specific way
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                # Catch any unexpected errors
                return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class InventoryDetailAPIView(APIView):
    """Handles GET (retrieve), PUT (update), and DELETE (remove) operations for a single item"""

    def get_object(self, id):
        """Retrieve an inventory item by primary key"""
        return get_object_or_404(InventoryItem, pk=id)

    def get(self, request, id):
        """Retrieve a single inventory item for the authenticated hotel only"""
        hotel_id = request.user.id
        item = get_object_or_404(InventoryItem, pk=id, user_id=hotel_id)
        serializer = InventorySerializer(item)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        """Update an inventory item for the authenticated hotel only"""
        hotel_id = request.user.id
        item = get_object_or_404(InventoryItem, pk=id, user_id=hotel_id)
        serializer = InventorySerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Inventory item updated successfully!"}, status=status.HTTP_200_OK)
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        """Delete an inventory item for the authenticated hotel only"""
        hotel_id = request.user.id
        item = get_object_or_404(InventoryItem, pk=id, user_id=hotel_id)
        item.delete()
        return Response({"message": "Inventory item deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import InventoryItem, InventoryRequest
from django.contrib.auth import get_user_model

User = get_user_model()

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import InventoryItem, InventoryRequest
from .serializers import InventoryRequestSerializer
from datetime import timedelta
from django.utils import timezone

class InventoryRequestCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        inventory_id = request.data.get("inventory_id")
        quantity = request.data.get("quantity")
        hotel_id = request.user.id

        if not inventory_id or not quantity:
            return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Ensure the inventory item belongs to the authenticated hotel
            inventory_item = InventoryItem.objects.get(id=inventory_id, user_id=hotel_id)
        except InventoryItem.DoesNotExist:
            return Response({"error": "Inventory item not found."}, status=status.HTTP_404_NOT_FOUND)

        if int(quantity) > inventory_item.quantity:
            return Response({"error": "Requested quantity exceeds available stock."}, status=status.HTTP_400_BAD_REQUEST)

        request_data = {
            "user": request.user.id,
            "quantity": quantity,
            "status": "requested"
        }

        # Pass object instead of ID
        serializer = InventoryRequestSerializer(data=request_data)
        if serializer.is_valid():
            serializer.save(inventory_item=inventory_item) 
            return Response({
                "message": "Inventory request submitted successfully.",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
   
    def get(self, request, *args, **kwargs):
        try:
            # Get the current time (timezone-aware datetime)
            time_limit = timezone.now() - timedelta(days=1)
            hotel_id = request.user.id

            # Query the database for requests within the last 24 hours for this hotel only
            requests = InventoryRequest.objects.filter(
                created_at__gte=time_limit,
                user_id=hotel_id  # Filter by hotel
            )

            # Serialize and return the requests
            serializer = InventoryRequestSerializer(requests, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            # Log the exception and return an error response
            print(f"Error: {str(e)}")
            return Response({"error": "Something went wrong while fetching requests."}, status=500)


    def patch(self, request, pk):
        try:
            inventory_request = InventoryRequest.objects.get(pk=pk)
        except InventoryRequest.DoesNotExist:
            return Response({"error": "Request not found"}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get("status")
        if new_status not in dict(InventoryRequest.STATUS_CHOICES):
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

        # Only update inventory if the request is being accepted
        if new_status == "accepted" and inventory_request.status != "accepted":
            inventory_item = inventory_request.inventory_item
            if inventory_request.quantity > inventory_item.quantity:
                return Response({"error": "Not enough inventory to accept this request."}, status=status.HTTP_400_BAD_REQUEST)

            # Subtract the requested quantity
            inventory_item.quantity -= inventory_request.quantity
            inventory_item.save()

        inventory_request.status = new_status
        inventory_request.save()
        return Response({"message": "Status updated successfully"}, status=status.HTTP_200_OK)

