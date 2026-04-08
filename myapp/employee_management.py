from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from .models import Attendance, ShiftSchedule, LeaveRequest, Employee


# ── Serializers ──────────────────────────────────────────────────────────────

class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.employee_name', read_only=True)
    department    = serializers.CharField(source='employee.department', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'employee', 'employee_name', 'department',
                  'date', 'check_in', 'check_out', 'status', 'overtime_hours', 'notes']
        read_only_fields = ['hotel']


class ShiftSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.employee_name', read_only=True)
    department    = serializers.CharField(source='employee.department', read_only=True)

    class Meta:
        model = ShiftSchedule
        fields = ['id', 'employee', 'employee_name', 'department', 'date', 'shift', 'notes']
        read_only_fields = ['hotel']


class LeaveSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.employee_name', read_only=True)
    department    = serializers.CharField(source='employee.department', read_only=True)
    days          = serializers.SerializerMethodField()

    def get_days(self, obj):
        return (obj.end_date - obj.start_date).days + 1

    class Meta:
        model = LeaveRequest
        fields = ['id', 'employee', 'employee_name', 'department',
                  'leave_type', 'start_date', 'end_date', 'days',
                  'reason', 'status', 'created_at']
        read_only_fields = ['hotel', 'created_at']


# ── Attendance ────────────────────────────────────────────────────────────────

class AttendanceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Attendance.objects.filter(hotel=request.user).select_related('employee')
        date = request.query_params.get('date')
        emp  = request.query_params.get('employee')
        if date: qs = qs.filter(date=date)
        if emp:  qs = qs.filter(employee_id=emp)
        return Response(AttendanceSerializer(qs, many=True).data)

    def post(self, request):
        s = AttendanceSerializer(data=request.data)
        if s.is_valid():
            # enforce employee belongs to this hotel
            emp_id = s.validated_data['employee'].employee_id
            if not Employee.objects.filter(employee_id=emp_id, user=request.user).exists():
                return Response({'detail': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)
            s.save(hotel=request.user)
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class AttendanceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, pk, user):
        try:
            return Attendance.objects.get(pk=pk, hotel=user), None
        except Attendance.DoesNotExist:
            return None, Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        obj, err = self._get(pk, request.user)
        if err: return err
        s = AttendanceSerializer(obj, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, err = self._get(pk, request.user)
        if err: return err
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Shift Schedule ────────────────────────────────────────────────────────────

class ShiftListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = ShiftSchedule.objects.filter(hotel=request.user).select_related('employee')
        date = request.query_params.get('date')
        emp  = request.query_params.get('employee')
        if date: qs = qs.filter(date=date)
        if emp:  qs = qs.filter(employee_id=emp)
        return Response(ShiftSerializer(qs, many=True).data)

    def post(self, request):
        s = ShiftSerializer(data=request.data)
        if s.is_valid():
            emp_id = s.validated_data['employee'].employee_id
            if not Employee.objects.filter(employee_id=emp_id, user=request.user).exists():
                return Response({'detail': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)
            s.save(hotel=request.user)
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class ShiftDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, pk, user):
        try:
            return ShiftSchedule.objects.get(pk=pk, hotel=user), None
        except ShiftSchedule.DoesNotExist:
            return None, Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        obj, err = self._get(pk, request.user)
        if err: return err
        s = ShiftSerializer(obj, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, err = self._get(pk, request.user)
        if err: return err
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Leave Requests ────────────────────────────────────────────────────────────

class LeaveListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = LeaveRequest.objects.filter(hotel=request.user).select_related('employee')
        st = request.query_params.get('status')
        emp = request.query_params.get('employee')
        if st:  qs = qs.filter(status=st)
        if emp: qs = qs.filter(employee_id=emp)
        return Response(LeaveSerializer(qs, many=True).data)

    def post(self, request):
        s = LeaveSerializer(data=request.data)
        if s.is_valid():
            emp_id = s.validated_data['employee'].employee_id
            if not Employee.objects.filter(employee_id=emp_id, user=request.user).exists():
                return Response({'detail': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)
            s.save(hotel=request.user)
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class LeaveDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, pk, user):
        try:
            return LeaveRequest.objects.get(pk=pk, hotel=user), None
        except LeaveRequest.DoesNotExist:
            return None, Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        obj, err = self._get(pk, request.user)
        if err: return err
        s = LeaveSerializer(obj, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, err = self._get(pk, request.user)
        if err: return err
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
