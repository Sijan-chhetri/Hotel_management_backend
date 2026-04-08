from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import SubUser
from .serializers import SubUserSerializer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import make_password, check_password

class SubUserManageView(APIView):
    permission_classes = [IsAuthenticated]  
    
    def get(self, request, *args, **kwargs):
        pk = kwargs.get('pk', None)
        hotel_id = request.user.id
        
        if pk:
            try:
                # Filter by hotel and subuser ID
                sub_user = SubUser.objects.get(pk=pk, user_id=hotel_id)
                serializer = SubUserSerializer(sub_user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except SubUser.DoesNotExist:
                return Response({"error": "SubUser not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Get all subusers for this hotel only
            sub_users = SubUser.objects.filter(user_id=hotel_id)
            serializer = SubUserSerializer(sub_users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        data['user'] = request.user.id

        # Hash the password before passing to serializer
        if 'password' in data:
            data['password'] = make_password(data['password'])

        serializer = SubUserSerializer(data=data)
        if serializer.is_valid():
            sub_user = serializer.save(user=request.user)
            return Response(SubUserSerializer(sub_user).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    
    def put(self, request, *args, **kwargs):
        hotel_id = request.user.id
        try:
            # Filter by hotel and subuser ID
            sub_user = SubUser.objects.get(pk=kwargs['pk'], user_id=hotel_id)  
        except SubUser.DoesNotExist:
            return Response({"error": "SubUser not found."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()

        # Handle password change
        if 'password' in data and data['password']:
            old_password = data.get('old_password', '')
            
            # Check if old password matches
            if not check_password(old_password, sub_user.password):
                return Response({"error": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

            # Hash the new password
            data['password'] = make_password(data['password'])
        else:
            data.pop('password', None)  # Prevent accidental overwrite

        # Update the sub-user fields
        serializer = SubUserSerializer(sub_user, data=data, partial=True)
        if serializer.is_valid():
            updated_sub_user = serializer.save()
            return Response(SubUserSerializer(updated_sub_user).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE - Delete SubUser
    def delete(self, request, *args, **kwargs):
        hotel_id = request.user.id
        try:
            # Filter by hotel and subuser ID
            sub_user = SubUser.objects.get(pk=kwargs['pk'], user_id=hotel_id)  
            sub_user.delete()  # Delete the sub-user
            return Response({"message": "SubUser deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)
        except SubUser.DoesNotExist:
            return Response({"error": "SubUser not found."}, status=status.HTTP_404_NOT_FOUND)
        
    def patch(self, request, *args, **kwargs):
        hotel_id = request.user.id
        try:
            # Filter by hotel and subuser ID
            sub_user = SubUser.objects.get(pk=kwargs['pk'], user_id=hotel_id)
        except SubUser.DoesNotExist:
            return Response({"error": "SubUser not found."}, status=status.HTTP_404_NOT_FOUND)

        # Expecting 'is_active' in the request data instead of 'status'
        is_active = request.data.get('is_active', None)
        if is_active is None:
            return Response({"error": "Missing 'is_active' field."}, status=status.HTTP_400_BAD_REQUEST)

        # Update the status field to the new value (active or inactive)
        sub_user.is_active = is_active
        sub_user.save()

        return Response({"message": f"SubUser status updated to '{'Active' if is_active else 'Inactive'}'."}, status=status.HTTP_200_OK)
