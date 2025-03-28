from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model

from cart.models import Coupon
from stories.models import Product, Variants



User = get_user_model()

# Create your models here.
class Checkout(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10,choices=(('Pending', 'Pending'),('Confirmed', 'Confirmed'),('Shipped', 'Shipped'),('Delivered', 'Delivered'),('Cancelled', 'Cancelled'),), default='Pending')
    payment_method = models.CharField(max_length=10,choices=(('Cash', 'Cash'),('Paypal', 'Paypal'),('SSLCommerz', 'SSLCommerz'),), default='Cash')
    total =models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    adminnote = models.CharField(max_length=100, null=False, blank=False)
    code = models.CharField(max_length=5, editable=False )
    full_name = models.CharField(max_length=10, null=False, blank=False)
    country = models.CharField(max_length=150, null=False, blank=False)
    city = models.CharField(max_length=150, null=False, blank=False)
    home_city = models.CharField(max_length=150, null=False, blank=False)
    zip_code = models.CharField(max_length=15, null=False, blank=False)
    phone = models.CharField(max_length=16, null=False, blank=False)
    address = models.TextField(max_length=500, null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.user.username


