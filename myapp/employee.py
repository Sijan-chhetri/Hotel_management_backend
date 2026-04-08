from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import EmployeeSerializer
from .models import Employee
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication



class EmployeeListCreateAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user  
        employees = Employee.objects.filter(user=user)  
        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data)


    def post(self, request):
        print("Incoming data:", request.data)

        
        data = request.data.copy()

        # Remove 'employee_id' from the data since it's auto-generated
        if 'employee_id' in data:
            del data['employee_id']
        
        # Add the logged-in user to the data
        data['user'] = request.user.id  

        serializer = EmployeeSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        print("Serializer errors:", serializer.errors)  
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class EmployeeDetailAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, employee_id):
        
        try:
            employee = Employee.objects.get(employee_id=employee_id)
            print(f"Employee with ID {employee_id} retrieved successfully.")
            return employee
        except Employee.DoesNotExist:
            print(f"Employee with ID {employee_id} not found.")
            return None

    def get(self, request, employee_id):
        
        employee = self.get_object(employee_id)
        if employee is None:
            print(f"GET request: Employee with ID {employee_id} not found.")
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)
        
        print(f"GET request: Employee with ID {employee_id} retrieved successfully.")
        serializer = EmployeeSerializer(employee)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, employee_id):
        
        employee = self.get_object(employee_id)
        if employee is None:
            print(f"PUT request: Employee with ID {employee_id} not found.")
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = EmployeeSerializer(employee, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            print(f"PUT request: Employee with ID {employee_id} updated successfully.")
            return Response({"message": "Employee updated successfully!"}, status=status.HTTP_200_OK)
        else:
            print(f"PUT request: Failed to update Employee with ID {employee_id}. Errors: {serializer.errors}")
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, employee_id):
        
        employee = self.get_object(employee_id)
        if employee is None:
            print(f"DELETE request: Employee with ID {employee_id} not found.")
            return Response({"error": "Employee not found"}, status=status.HTTP_404_NOT_FOUND)

        employee.delete()
        print(f"DELETE request: Employee with ID {employee_id} deleted successfully.")
        return Response({"message": "Employee deleted successfully!"}, status=status.HTTP_204_NO_CONTENT)



