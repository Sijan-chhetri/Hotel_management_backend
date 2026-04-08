from django.contrib.auth import authenticate, get_user_model
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

@api_view(['POST'])
def admin_register(request):
    email = request.data.get('email')
    phone_number = request.data.get('phone_number')
    password = request.data.get('password')

    if not email or not password or not phone_number:
        return Response({'message': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'message': 'Email already registered.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(email=email, phone_number=phone_number, password=password)
    user.is_staff = True  
    user.save()

    return Response({'message': 'Admin registered successfully.'}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def admin_login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = authenticate(request, email=email, password=password)

    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Login successful.',
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user_id': user.id,
            'email': user.email
        }, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)
    
    








