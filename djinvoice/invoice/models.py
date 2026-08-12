from django.db import models
from django.utils import timezone
from users.models import User

class Invoice(models.Model):
    invoice_number = models.CharField(max_length=20)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=[('paid', 'Paid'), ('unpaid', 'Unpaid')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.customer.email}"