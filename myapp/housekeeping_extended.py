from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from .models import HousekeepingAssignment, LostAndFound, SpecialRequest, LinenRecord
from rest_framework import serializers


# ── Serializers ─────────────────────────────────────────────────────────────

class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = HousekeepingAssignment
        fields = '__all__'
        read_only_fields = ['hotel', 'created_at']


class LostFoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = LostAndFound
        fields = '__all__'
        read_only_fields = ['hotel', 'created_at']


class SpecialRequestSerializer(serializers.ModelSerializer):
    check_in_date = serializers.DateField(source='booking.check_in_date', read_only=True, default=None)

    class Meta:
        model = SpecialRequest
        fields = '__all__'
        read_only_fields = ['hotel', 'created_at']


class LinenSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinenRecord
        fields = '__all__'
        read_only_fields = ['hotel', 'created_at', 'updated_at']


# ── Staff Assignments ────────────────────────────────────────────────────────

class AssignmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = HousekeepingAssignment.objects.filter(hotel=request.user)
        date = request.query_params.get('date')
        if date:
            qs = qs.filter(date=date)
        return Response(AssignmentSerializer(qs, many=True).data)

    def post(self, request):
        s = AssignmentSerializer(data=request.data)
        if s.is_valid():
            s.save(hotel=request.user)
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, pk, user):
        try:
            obj = HousekeepingAssignment.objects.get(pk=pk, hotel=user)
            return obj, None
        except HousekeepingAssignment.DoesNotExist:
            return None, Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        obj, err = self._get(pk, request.user)
        if err: return err
        s = AssignmentSerializer(obj, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, err = self._get(pk, request.user)
        if err: return err
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Lost & Found ─────────────────────────────────────────────────────────────

class LostFoundView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = LostAndFound.objects.filter(hotel=request.user)
        return Response(LostFoundSerializer(qs, many=True).data)

    def post(self, request):
        s = LostFoundSerializer(data=request.data)
        if s.is_valid():
            s.save(hotel=request.user)
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class LostFoundDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, pk, user):
        try:
            return LostAndFound.objects.get(pk=pk, hotel=user), None
        except LostAndFound.DoesNotExist:
            return None, Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        obj, err = self._get(pk, request.user)
        if err: return err
        data = request.data.copy()
        if data.get('status') == 'claimed' and not obj.returned_at:
            data['returned_at'] = now().isoformat()
        s = LostFoundSerializer(obj, data=data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, err = self._get(pk, request.user)
        if err: return err
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Special Requests ─────────────────────────────────────────────────────────

class SpecialRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = SpecialRequest.objects.filter(hotel=request.user)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return Response(SpecialRequestSerializer(qs, many=True).data)

    def post(self, request):
        s = SpecialRequestSerializer(data=request.data)
        if s.is_valid():
            s.save(hotel=request.user)
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class SpecialRequestDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, pk, user):
        try:
            return SpecialRequest.objects.get(pk=pk, hotel=user), None
        except SpecialRequest.DoesNotExist:
            return None, Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        obj, err = self._get(pk, request.user)
        if err: return err
        data = request.data.copy()
        if data.get('status') == 'completed' and not obj.resolved_at:
            data['resolved_at'] = now().isoformat()
        s = SpecialRequestSerializer(obj, data=data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, err = self._get(pk, request.user)
        if err: return err
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Linen Records ─────────────────────────────────────────────────────────────

class LinenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = LinenRecord.objects.filter(hotel=request.user)
        return Response(LinenSerializer(qs, many=True).data)

    def post(self, request):
        s = LinenSerializer(data=request.data)
        if s.is_valid():
            s.save(hotel=request.user)
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class LinenDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, pk, user):
        try:
            return LinenRecord.objects.get(pk=pk, hotel=user), None
        except LinenRecord.DoesNotExist:
            return None, Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        obj, err = self._get(pk, request.user)
        if err: return err
        s = LinenSerializer(obj, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, err = self._get(pk, request.user)
        if err: return err
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Partial Linen Issue ───────────────────────────────────────────────────────

class LinenIssueView(APIView):
    """
    Issue a partial quantity of clean linen back to rooms.
    If qty < record.quantity: splits into issued (in_use) + remaining (washed).
    If qty == record.quantity: moves entire record to in_use.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            record = LinenRecord.objects.get(pk=pk, hotel=request.user, status='washed')
        except LinenRecord.DoesNotExist:
            return Response({'detail': 'Clean linen record not found.'}, status=status.HTTP_404_NOT_FOUND)

        qty = int(request.data.get('quantity', 0))
        if qty <= 0:
            return Response({'detail': 'Quantity must be greater than 0.'}, status=status.HTTP_400_BAD_REQUEST)
        if qty > record.quantity:
            return Response({'detail': f'Only {record.quantity} available.'}, status=status.HTTP_400_BAD_REQUEST)

        if qty == record.quantity:
            # Issue all — just update status
            record.status = 'in_use'
            record.save()
            return Response(LinenSerializer(record).data)
        else:
            # Partial issue — create new in_use record, reduce original
            from .models import LinenRecord as LR
            LR.objects.create(
                hotel=request.user,
                linen_type=record.linen_type,
                quantity=qty,
                status='in_use',
                room_id=record.room_id,
                notes=record.notes,
            )
            record.quantity -= qty
            record.save()
            return Response({'issued': qty, 'remaining': record.quantity}, status=status.HTTP_200_OK)


# ── Partial Linen Collection (in_use → dirty, with split) ────────────────────

class LinenCollectView(APIView):
    """
    Collect a quantity of in_use linen as dirty.
    If qty < record.quantity: splits — collected qty → dirty, remaining → stays in_use.
    If qty == record.quantity: moves entire record to dirty.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            record = LinenRecord.objects.get(pk=pk, hotel=request.user, status='in_use')
        except LinenRecord.DoesNotExist:
            return Response({'detail': 'In-use linen record not found.'}, status=status.HTTP_404_NOT_FOUND)

        qty = int(request.data.get('quantity', 0))
        if qty <= 0:
            return Response({'detail': 'Quantity must be greater than 0.'}, status=status.HTTP_400_BAD_REQUEST)
        if qty > record.quantity:
            return Response({'detail': f'Only {record.quantity} available.'}, status=status.HTTP_400_BAD_REQUEST)

        if qty == record.quantity:
            record.status = 'dirty'
            record.save()
            return Response(LinenSerializer(record).data)
        else:
            # Partial collect — create dirty record, reduce original
            LinenRecord.objects.create(
                hotel=request.user,
                linen_type=record.linen_type,
                quantity=qty,
                status='dirty',
                room_id=record.room_id,
                notes=record.notes,
            )
            record.quantity -= qty
            record.save()
            return Response({'collected': qty, 'remaining': record.quantity}, status=status.HTTP_200_OK)
