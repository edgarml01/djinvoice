from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from invoice.models import Invoice
from .serializers import InvoiceSerializer, InvoiceListSerializer

class InvoiceViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para invoices
    - GET /api/invoices/ - Listar todas las invoices del usuario
    - POST /api/invoices/ - Crear nueva invoice
    - GET /api/invoices/{id}/ - Obtener detalle de invoice
    - PUT /api/invoices/{id}/ - Actualizar invoice
    - DELETE /api/invoices/{id}/ - Eliminar invoice
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [ filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'customer']
    search_fields = ['invoice_number', 'customer__email']
    ordering_fields = ['due_date', 'amount', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Retorna las invoices del usuario autenticado"""
        return Invoice.objects.filter(customer=self.request.user)

    def get_serializer_class(self):
        """Usa serializer diferente para list vs detail"""
        if self.action == 'list':
            return InvoiceListSerializer
        return InvoiceSerializer

    def perform_create(self, serializer):
        """Al crear, asigna automáticamente el usuario autenticado"""
        serializer.save(customer=self.request.user)