from django.shortcuts import redirect, get_object_or_404
from django.db.models import Min, Max
from django.utils import timezone
from cart.models import Cart, CartItem
from stories.models import (
    Category, Brand, Product, Images, Color, Size, Variants,
)

def get_filters(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user, paid=False)
        cart_items = CartItem.objects.filter(cart=cart)
        cart_count = cart_items.count()
        cart_totals = sum(item.quantity * (item.variant.price if item.variant else item.product.price) for item in cart_items)
        return {
            'cart_items': cart_items,
            'cart_count': cart_count,
            'cart_totals': cart_totals,
            'payable_price': cart_totals + 150
        }
    else:
        return {
            'cart_items': [],
            'cart_count': 0,
            'cart_totals': 0,
            'payable_price': 0
        }

