from django.contrib import admin
from unfold.admin import ModelAdmin
import admin_thumbnails

from cart.models import Cart, Coupon

# Register your models here.
class CouponAdmin(ModelAdmin):
    list_display = ['id', 'coupon_code', 'coupon_discount', 'is_expired', 'minimum_amount']
    search_fields = ['coupon_code']
    list_filter = ['is_expired']
    list_editable = ['is_expired']
admin.site.register(Coupon, CouponAdmin)

class CartAdmin(ModelAdmin):
    pass
admin.site.register(Cart, CartAdmin)

