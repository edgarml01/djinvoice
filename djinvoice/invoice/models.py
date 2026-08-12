from django.db import models
from users.models import User

# Create your models here.
class Invoice(models.Model):
    invoice_number = models.CharField(max_length=20)
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=[('paid', 'Paid'), ('unpaid', 'Unpaid')])

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.customer.email}"