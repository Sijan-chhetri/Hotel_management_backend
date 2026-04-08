from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now

from .models import PaymentGatewayConfig, OTAChannelConfig, CredentialAuditLog
from .serializers import PaymentGatewayConfigSerializer, OTAChannelConfigSerializer


def _log(hotel, model_name, record_id, action):
    CredentialAuditLog.objects.create(
        hotel=hotel, model_name=model_name, record_id=record_id, action=action
    )


# ── Payment Gateway Config ──────────────────────────────────────────────────

class PaymentGatewayConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        configs = PaymentGatewayConfig.objects.filter(hotel=request.user)
        serializer = PaymentGatewayConfigSerializer(configs, many=True)
        return Response(serializer.data)

    def post(self, request):
        gateway_type = request.data.get("gateway_type")
        if not gateway_type:
            return Response({"gateway_type": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

        instance, created = PaymentGatewayConfig.objects.get_or_create(
            hotel=request.user, gateway_type=gateway_type
        )
        serializer = PaymentGatewayConfigSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            data = serializer.validated_data
            # Auto-enable if a secret key is being saved
            if data.get('secret_key'):
                data['is_enabled'] = True
            obj = serializer.save(hotel=request.user)
            _log(request.user, "PaymentGatewayConfig", obj.id, "create" if created else "update")
            return Response(PaymentGatewayConfigSerializer(obj).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentGatewayConfigDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_owned(self, pk, user):
        try:
            obj = PaymentGatewayConfig.objects.get(pk=pk)
        except PaymentGatewayConfig.DoesNotExist:
            return None, Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        if obj.hotel != user:
            return None, Response({"detail": "You do not have permission."}, status=status.HTTP_403_FORBIDDEN)
        return obj, None

    def patch(self, request, pk):
        obj, err = self._get_owned(pk, request.user)
        if err:
            return err
        serializer = PaymentGatewayConfigSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            _log(request.user, "PaymentGatewayConfig", updated.id, "update")
            return Response(PaymentGatewayConfigSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, err = self._get_owned(pk, request.user)
        if err:
            return err
        _log(request.user, "PaymentGatewayConfig", obj.id, "delete")
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── OTA Channel Config ──────────────────────────────────────────────────────

class OTAChannelConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        configs = OTAChannelConfig.objects.filter(hotel=request.user)
        serializer = OTAChannelConfigSerializer(configs, many=True)
        return Response(serializer.data)

    def post(self, request):
        platform_name = request.data.get("platform_name")
        if not platform_name:
            return Response({"platform_name": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

        instance, created = OTAChannelConfig.objects.get_or_create(
            hotel=request.user, platform_name=platform_name,
            defaults={"platform_type": request.data.get("platform_type", "ota"), "api_key": ""}
        )
        serializer = OTAChannelConfigSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            obj = serializer.save(hotel=request.user)
            _log(request.user, "OTAChannelConfig", obj.id, "create" if created else "update")
            return Response(OTAChannelConfigSerializer(obj).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTAChannelConfigDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            obj = OTAChannelConfig.objects.get(pk=pk)
        except OTAChannelConfig.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        if obj.hotel != request.user:
            return Response({"detail": "You do not have permission."}, status=status.HTTP_403_FORBIDDEN)
        _log(request.user, "OTAChannelConfig", obj.id, "delete")
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Webhook receiver — updates last_webhook_at ─────────────────────────────

class PaymentWebhookView(APIView):
    """
    Called by the payment gateway to confirm a callback was received.
    Updates last_webhook_at on the matching config.
    No auth required (gateway calls this directly).
    """
    def post(self, request, gateway_type):
        hotel_id = request.data.get("hotel_id") or request.query_params.get("hotel_id")
        if hotel_id:
            PaymentGatewayConfig.objects.filter(
                hotel_id=hotel_id, gateway_type=gateway_type
            ).update(last_webhook_at=now())
        return Response({"status": "ok"})
