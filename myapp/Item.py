from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Item
from .serializers import ItemSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

class ItemListCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    """
    List all items or create a new item.
    """
    
    def get(self, request):
        # Filter items by authenticated hotel
        hotel_id = request.user.id
        items = Item.objects.filter(hotel_id=hotel_id)
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        # Add hotel to the data
        data = request.data.copy()
        data['hotel'] = request.user.id
        
        serializer = ItemSerializer(data=data)
        if serializer.is_valid():
            serializer.save()  
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ItemDetailView(APIView):
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    """
    Retrieve, update, or delete a specific item by ID.
    """
    
    def get(self, request, pk):
        # Filter by hotel and item ID
        hotel_id = request.user.id
        item = Item.objects.filter(id=pk, hotel_id=hotel_id).first()
        if item is None:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        # Filter by hotel and item ID
        hotel_id = request.user.id
        item = Item.objects.filter(id=pk, hotel_id=hotel_id).first()
        if item is None:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ItemSerializer(item, data=request.data, partial=True)  
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        # Filter by hotel and item ID
        hotel_id = request.user.id
        item = Item.objects.filter(id=pk, hotel_id=hotel_id).first()
        if item is None:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        item.delete()
        return Response({'message': 'Item deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
