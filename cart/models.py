from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.db.models import Sum
from stories.models import Product, Variants

# Custom User model import
User = get_user_model()

class Coupon(models.Model):
    coupon_code = models.CharField(max_length=10, unique=True)
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00')) 
    is_expired = models.BooleanField(default=False)
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        ordering = ['id']
        verbose_name_plural = '01. Coupons'

    def __str__(self):
        return self.coupon_code

    def is_valid(self, total_amount):
        """Check if the coupon is valid based on expiration and minimum amount."""
        return not self.is_expired and total_amount >= self.minimum_amount

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)


    class Meta:
        ordering = ['id']
        verbose_name_plural = '02. Carts'


