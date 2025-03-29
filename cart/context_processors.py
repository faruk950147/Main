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
        cart_total = sum(item.quantity * (item.product.price if item.product.price else 0) for item in cart_items)
    else:
        cart_items = []
        cart_count = 0
        cart_total = 0

    return {
        'cart_items': cart_items,
        'cart_count': cart_count,
        'cart_total': cart_total
    }

