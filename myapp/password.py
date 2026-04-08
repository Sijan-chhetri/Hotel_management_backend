from django.contrib.auth import get_user_model, authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import check_password
from django.contrib.auth import update_session_auth_hash  

User = get_user_model()

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    """
    View to change user password.
    """

    def put(self, request, *args, **kwargs):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if new_password != confirm_password:
            return Response({"error": "New password and confirm password do not match."}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user  # Get the currently authenticated user

        # Check if the old password is correct
        if not check_password(old_password, user.password):
            return Response({"error": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        # Set the new password
        user.set_password(new_password)
        user.save()

       
        update_session_auth_hash(request, user)

        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)
