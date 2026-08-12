from rest_framework import serializers
from invoice.models import Invoice
from users.models import User

class UserInvoiceSerializer(serializers.ModelSerializer):
    """Serializer anidado para mostrar datos del usuario"""
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name']
        read_only_fields = ['id', 'email', 'username']

class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer para CRUD de invoices"""
    customer = UserInvoiceSerializer(read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source='customer'
    )
    
    class Meta:
        model = Invoice
        fields = ['id', 'invoice_number', 'customer', 'customer_id', 'amount', 'due_date', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class InvoiceListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar invoices"""
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    
    class Meta:
        model = Invoice
        fields = ['id', 'invoice_number', 'customer_email', 'amount', 'due_date', 'status']