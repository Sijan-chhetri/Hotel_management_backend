from rest_framework import serializers
from .models import User, Room, Booking, Employee, Guest, InventoryItem, SubUser
from django.contrib.auth.hashers import make_password



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'hotel_name',
            'address',
            'city',
            'state',
            # 'country',
            'zipcode',
            'phone_number',
            'email',
            'description',
            'password',
            'is_active'
        ]
        

    def validate_password(self, value):
        """Ensure the password is hashed before saving."""
        return make_password(value)
    
class SubUserSerializer(serializers.ModelSerializer):
    class Meta:
        model= SubUser
        fields = "__all__" 


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = "__all__" 




class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
    
        fields = "__all__" 
        read_only_fields = ['employee_id']




class GuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    guest = GuestSerializer() 
    
    class Meta:
        model = Booking
        fields = ['booking_id', 'guest', 'room', 'check_in_date', 'check_out_date', 'status', 'notes', 'group_id']
        
        
class BookingRoom(serializers.ModelSerializer):
    room = RoomSerializer() 
    
    class Meta:
        model = Booking
        fields = ['booking_id', 'room', 'check_in_date', 'check_out_date', 'status']
        
        




class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'


class BookingStatusUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Booking
        fields = ['status']




class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = '__all__'




from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'


from rest_framework import serializers
from .models import Invoice, Item, OrderItem





class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'



from rest_framework import serializers
from .models import OrderItem


class BookingRoomOrder(serializers.ModelSerializer):
    guest = GuestSerializer() 
    room = RoomSerializer()
    class Meta:
        model = Booking
        fields = '__all__'

class OrderItemSerializers(serializers.ModelSerializer):
    item = ItemSerializer()
    booking=BookingRoomOrder()
    class Meta:
        model = OrderItem
        fields = ['id', 'booking', 'item','status','quantity', 'ordered_at']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'booking', 'item', 'quantity', 'ordered_at']
        
        
class RoomBookingSerializer(serializers.ModelSerializer):
    guest = GuestSerializer()
    room = RoomSerializer()
    orders = OrderItemSerializers(many=True, read_only=True)  # Related name from Booking model

    class Meta:
        model = Booking
        fields = ['booking_id', 'guest', 'room', 'check_in_date', 'check_out_date', 'status', 'orders', 'notes', 'group_id']


# serializers.py
from rest_framework import serializers
from .models import InventoryRequest

class InventoryRequestSerializer(serializers.ModelSerializer):
    inventory_item = InventorySerializer(read_only=True)  # Note: not many=True because it's a ForeignKey

    class Meta:
        model = InventoryRequest
        fields = '__all__'


from rest_framework import serializers
from .models import Housekeeping

class HousekeepingSerializer(serializers.ModelSerializer):
    booking = BookingRoom()

    class Meta:
        model = Housekeeping
        fields = [
            'id', 'booking', 'status', 'priority',
            'notes', 'toiletries_restocked', 'last_cleaned_at', 'assigned_to'
        ]

class InvoiceSerializer(serializers.ModelSerializer):
    room = RoomSerializer()  
    booking = BookingSerializer()  

    class Meta:
        model = Invoice
        fields = [
            'id',
            'booking',  
            'payment',
            'room',  
            'check_in_date',
            'check_out_date',
            'payment_type',
            'room_type',
            'total_amount',
            'generated_on',
            'invoice_pdf',
        ]




# serializers.py
from rest_framework import serializers
from .models import WebUser
from django.contrib.auth.hashers import make_password

class WebuserSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebUser
        fields = ['id','email', 'password', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)


# ── Payment Gateway Config Serializer ──────────────────────────────────────

from .models import PaymentGatewayConfig, OTAChannelConfig
from .encryption import encryption_service


class PaymentGatewayConfigSerializer(serializers.ModelSerializer):
    # merchant_id is plain text, not a secret — optional
    merchant_id = serializers.CharField(write_only=False, required=False, allow_blank=True)
    # Credentials are write-only — never returned in responses
    public_key  = serializers.CharField(write_only=True,  required=False, allow_blank=True)
    secret_key  = serializers.CharField(write_only=True,  required=False, allow_blank=True)

    class Meta:
        model  = PaymentGatewayConfig
        fields = [
            'id', 'gateway_type', 'is_enabled', 'mode',
            'merchant_id', 'public_key', 'secret_key',
            'last_webhook_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'last_webhook_at', 'created_at', 'updated_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Expose merchant_id (not a secret), mask credential fields
        data['merchant_id'] = instance.merchant_id
        data['has_public_key'] = bool(instance.public_key)
        data['has_secret_key'] = bool(instance.secret_key)
        return data

    def _encrypt_credentials(self, validated_data):
        for field in ('public_key', 'secret_key'):
            val = validated_data.get(field)
            if val:
                validated_data[field] = encryption_service.encrypt(val)
        return validated_data

    def create(self, validated_data):
        validated_data = self._encrypt_credentials(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Only overwrite credential fields if a new value was provided
        for field in ('public_key', 'secret_key'):
            val = validated_data.get(field)
            if val:
                validated_data[field] = encryption_service.encrypt(val)
            else:
                validated_data.pop(field, None)  # keep existing encrypted value
        return super().update(instance, validated_data)


# ── OTA Channel Config Serializer ──────────────────────────────────────────

class OTAChannelConfigSerializer(serializers.ModelSerializer):
    api_key      = serializers.CharField(write_only=True, required=True)
    api_secret   = serializers.CharField(write_only=True, required=False, allow_blank=True)
    extra_config = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model  = OTAChannelConfig
        fields = [
            'id', 'platform_name', 'platform_type', 'is_connected',
            'api_key', 'api_secret', 'extra_config',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['has_api_key']    = bool(instance.api_key)
        data['has_api_secret'] = bool(instance.api_secret)
        return data

    def _encrypt_credentials(self, validated_data):
        for field in ('api_key', 'api_secret', 'extra_config'):
            val = validated_data.get(field)
            if val:
                validated_data[field] = encryption_service.encrypt(val)
        return validated_data

    def create(self, validated_data):
        validated_data = self._encrypt_credentials(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        for field in ('api_key', 'api_secret', 'extra_config'):
            val = validated_data.get(field)
            if val:
                validated_data[field] = encryption_service.encrypt(val)
            else:
                validated_data.pop(field, None)
        return super().update(instance, validated_data)
