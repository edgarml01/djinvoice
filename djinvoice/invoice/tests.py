from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from invoice.models import Invoice
from datetime import date

User = get_user_model()

class InvoiceCRUDTests(APITestCase):
    def setUp(self):
        # Create test users
        self.user = User.objects.create_user(
            email='user@example.com',
            username='user',
            password='password123'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            username='other',
            password='password123'
        )
        
        # API URLs
        self.list_url = reverse('invoice-list')
        
        # Valid payload for creating invoices
        self.valid_payload = {
            'invoice_number': 'INV-001',
            'customer_id': self.user.id,
            'amount': '150.50',
            'due_date': '2026-12-31',
            'status': 'unpaid'
        }
        self.valid_payload_create = {
            'invoice_number': 'INV-001',
            'amount': '150.50',
            'due_date': '2026-12-31',
            'status': 'unpaid'
        }

    def test_unauthenticated_access_denied(self):
        """Verify that unauthenticated users cannot list or create invoices."""
        # Try to list
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Try to create
        response = self.client.post(self.list_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_invoice_success(self):
        """Verify that an authenticated user can successfully create an invoice."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.list_url, self.valid_payload_create, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['invoice_number'], 'INV-001')
        self.assertEqual(response.data['amount'], '150.50')
        self.assertEqual(response.data['status'], 'unpaid')
        self.assertEqual(response.data['due_date'], '2026-12-31')
        
        # Verify database record exists and customer is set automatically to authenticated user
        invoice = Invoice.objects.get(id=response.data['id'])
        self.assertEqual(invoice.customer, self.user)

    def test_create_invoice_invalid_data(self):
        """Verify that creating an invoice with invalid data returns a 400 Bad Request."""
        self.client.force_authenticate(user=self.user)
        invalid_payload = self.valid_payload.copy()
        invalid_payload['amount'] = 'invalid-decimal'
        invalid_payload['status'] = 'invalid-status'
        
        response = self.client.post(self.list_url, invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)
        self.assertIn('status', response.data)

    def test_list_invoices_only_returns_owners_invoices(self):
        """Verify that list endpoint only returns invoices belonging to the authenticated user."""
        # Create invoice for authenticated user
        invoice_user = Invoice.objects.create(
            invoice_number='INV-OWNER',
            customer=self.user,
            amount='100.00',
            due_date=date(2026, 12, 31),
            status='paid'
        )
        # Create invoice for other user
        invoice_other = Invoice.objects.create(
            invoice_number='INV-OTHER',
            customer=self.other_user,
            amount='200.00',
            due_date=date(2026, 12, 31),
            status='unpaid'
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['invoice_number'], 'INV-OWNER')
        self.assertEqual(response.data[0]['customer_email'], self.user.email)
        
        # Verify the structure matches InvoiceListSerializer
        self.assertIn('customer_email', response.data[0])
        self.assertNotIn('customer_id', response.data[0])

    def test_retrieve_invoice_detail_success(self):
        """Verify that an authenticated user can retrieve details of their own invoice."""
        invoice = Invoice.objects.create(
            invoice_number='INV-DETAIL',
            customer=self.user,
            amount='300.00',
            due_date=date(2026, 12, 31),
            status='unpaid'
        )
        url = reverse('invoice-detail', kwargs={'pk': invoice.id})
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['invoice_number'], 'INV-DETAIL')
        self.assertEqual(response.data['amount'], '300.00')
        self.assertEqual(response.data['customer']['email'], self.user.email)

    def test_retrieve_invoice_detail_other_user_not_found(self):
        """Verify that retrieving another user's invoice detail returns 404 Not Found."""
        invoice = Invoice.objects.create(
            invoice_number='INV-OTHER-DETAIL',
            customer=self.other_user,
            amount='300.00',
            due_date=date(2026, 12, 31),
            status='unpaid'
        )
        url = reverse('invoice-detail', kwargs={'pk': invoice.id})
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_invoice_success(self):
        """Verify that an authenticated user can update their own invoice."""
        invoice = Invoice.objects.create(
            invoice_number='INV-UPDATE',
            customer=self.user,
            amount='400.00',
            due_date=date(2026, 12, 31),
            status='unpaid'
        )
        url = reverse('invoice-detail', kwargs={'pk': invoice.id})
        update_payload = {
            'invoice_number': 'INV-UPDATE-UPDATED',
            'customer_id': self.user.id,
            'amount': '450.00',
            'due_date': '2027-01-01',
            'status': 'paid'
        }
        
        self.client.force_authenticate(user=self.user)
        response = self.client.put(url, update_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['invoice_number'], 'INV-UPDATE-UPDATED')
        self.assertEqual(response.data['amount'], '450.00')
        self.assertEqual(response.data['status'], 'paid')
        
        # Verify db values updated
        invoice.refresh_from_db()
        self.assertEqual(invoice.invoice_number, 'INV-UPDATE-UPDATED')
        self.assertEqual(float(invoice.amount), 450.00)
        self.assertEqual(invoice.status, 'paid')

    def test_update_invoice_other_user_not_found(self):
        """Verify that updating another user's invoice returns 404 Not Found."""
        invoice = Invoice.objects.create(
            invoice_number='INV-OTHER-UPDATE',
            customer=self.other_user,
            amount='400.00',
            due_date=date(2026, 12, 31),
            status='unpaid'
        )
        url = reverse('invoice-detail', kwargs={'pk': invoice.id})
        update_payload = {
            'invoice_number': 'INV-OTHER-UPDATE-UPDATED',
            'customer_id': self.other_user.id,
            'amount': '450.00',
            'due_date': '2027-01-01',
            'status': 'paid'
        }
        
        self.client.force_authenticate(user=self.user)
        response = self.client.put(url, update_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_invoice_success(self):
        """Verify that an authenticated user can delete their own invoice."""
        invoice = Invoice.objects.create(
            invoice_number='INV-DELETE',
            customer=self.user,
            amount='500.00',
            due_date=date(2026, 12, 31),
            status='unpaid'
        )
        url = reverse('invoice-detail', kwargs={'pk': invoice.id})
        
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Invoice.objects.filter(id=invoice.id).exists())

    def test_delete_invoice_other_user_not_found(self):
        """Verify that deleting another user's invoice returns 404 Not Found."""
        invoice = Invoice.objects.create(
            invoice_number='INV-OTHER-DELETE',
            customer=self.other_user,
            amount='500.00',
            due_date=date(2026, 12, 31),
            status='unpaid'
        )
        url = reverse('invoice-detail', kwargs={'pk': invoice.id})
        
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Invoice.objects.filter(id=invoice.id).exists())

    def test_list_invoices_search(self):
        """Verify searching invoices by invoice_number."""
        Invoice.objects.create(
            invoice_number='INV-ABC', customer=self.user, amount='100.00', due_date=date(2026, 12, 31), status='paid'
        )
        Invoice.objects.create(
            invoice_number='INV-XYZ', customer=self.user, amount='200.00', due_date=date(2026, 12, 31), status='unpaid'
        )
        
        self.client.force_authenticate(user=self.user)
        
        # Search for ABC
        response = self.client.get(f"{self.list_url}?search=ABC")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['invoice_number'], 'INV-ABC')

    def test_list_invoices_ordering(self):
        """Verify ordering invoices by amount."""
        Invoice.objects.create(
            invoice_number='INV-LOW', customer=self.user, amount='10.00', due_date=date(2026, 12, 31), status='paid'
        )
        Invoice.objects.create(
            invoice_number='INV-HIGH', customer=self.user, amount='1000.00', due_date=date(2026, 12, 31), status='unpaid'
        )
        
        self.client.force_authenticate(user=self.user)
        
        # Order by amount ascending
        response = self.client.get(f"{self.list_url}?ordering=amount")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['invoice_number'], 'INV-LOW')
        self.assertEqual(response.data[1]['invoice_number'], 'INV-HIGH')
        
        # Order by amount descending
        response = self.client.get(f"{self.list_url}?ordering=-amount")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['invoice_number'], 'INV-HIGH')
        self.assertEqual(response.data[1]['invoice_number'], 'INV-LOW')
