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
