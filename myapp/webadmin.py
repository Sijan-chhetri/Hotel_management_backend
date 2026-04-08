# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import check_password
from .models import WebUser
from .serializers import WebuserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

class WebuserRegisterView(APIView):
    def post(self, request):
        serializer = WebuserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Webuser registered successfully.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WebuserLoginView(APIView):
     def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = WebUser.objects.get(email=email)
        except WebUser.DoesNotExist:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if not check_password(password, user.password):
            return Response({"message": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({"message": "Your account is inactive."}, status=status.HTTP_403_FORBIDDEN)


        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        access_token.set_exp(lifetime=timedelta(days=5))  # ⏰ Set access token to expire in 5 hours

        return Response({
            "token": str(access_token),
            "refresh": str(refresh),
            "email": user.email
        })




from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import User
from .serializers import UserSerializer  # Ensure this serializer is created

class UserListView(APIView):
  
    permission_classes = [IsAuthenticated]  

    def get(self, request, *args, **kwargs):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



from django.shortcuts import get_object_or_404

class UpdateUserStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, user_id, *args, **kwargs):
        """
        Toggle or set the 'is_active' status of a user.
        """
        user = get_object_or_404(User, id=user_id)
        new_status = request.data.get("is_active")

        if new_status not in [0, 1, '0', '1', True, False, 'true', 'false']:
            return Response({"error": "Invalid status value. Use 0 or 1."}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = bool(int(new_status))
        user.save()

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)



class AdminListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        admins = WebUser.objects.filter(is_admin=True)
        serializer = WebuserSerializer(admins, many=True)
        return Response(serializer.data)



class  AdminStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, user_id):
        try:
            user = WebUser.objects.get(id=user_id, is_admin=True)
        except WebUser.DoesNotExist:
            return Response({'error': 'Admin not found'}, status=status.HTTP_404_NOT_FOUND)

        is_active = request.data.get('is_active')
        if is_active is not None:
            user.is_active = bool(is_active)
            user.save()
            return Response({'message': 'Admin status updated'})
        return Response({'error': 'is_active not provided'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_id):
        try:
            user = WebUser.objects.get(id=user_id, is_admin=True)
        except WebUser.DoesNotExist:
            return Response({'error': 'Admin not found'}, status=status.HTTP_404_NOT_FOUND)

        user.delete()
        return Response({'message': 'Admin deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
