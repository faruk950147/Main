from decimal import Decimal
from django.shortcuts import render,redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.views import generic
from django.utils import timezone
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.db.models import Min, Max, Sum
import json
from cart.forms import (
    CartItemForm
)
from stories.models import (
    Product, Variants
)
from cart.models import (
    Coupon, Cart, CartItem
)

# create your views here
@method_decorator(never_cache, name='dispatch')
class AddToCart(LoginRequiredMixin, generic.View):
    login_url = reverse_lazy('sign')

    def post(self, request):
        if request.method == "POST":
            try:
                # Request to JSON data
                data = json.loads(request.body)
                size_id = data.get("size_id")
                color_id = data.get("color_id")
                quantity = data.get("quantity")
                product_id = data.get("product_id")

                # Quantity validation
                if quantity is None or int(quantity) <= 0:
                    return JsonResponse({"status": 400, "messages": "Quantity must be greater than 0!"})
                quantity = int(quantity)

                # Product validation
                if not product_id:
                    return JsonResponse({"status": 400, "messages": "Product ID is required!"})
                product = get_object_or_404(Product, id=product_id)

                # Get variant if applicable (Optimized Query)
                variant_qs = Variants.objects.filter(
                    product=product,
                    size_id=size_id if size_id else None,
                    color_id=color_id if color_id else None
                )

                # Safe check for empty queryset
                variant = None
                if variant_qs.exists():  # Ensure queryset is not empty
                    variant = variant_qs[0]  # Get first item safely

                if (size_id or color_id) and not variant:
                    return JsonResponse({"status": 400, "messages": "Variant not found!"})

                # Stock validation
                max_stock = variant.quantity if variant else (product.in_stock_max or 0)
                if max_stock <= 0:
                    return JsonResponse({"status": 400, "messages": "Product out of stock!"})

                # Get or create cart (Optimized Query)
                cart_qs = Cart.objects.filter(user=request.user, paid=False).prefetch_related('items__product', 'items__variant')
                if cart_qs.exists():
                    cart = cart_qs[0]  # Use qs[0] instead of first()
                else:
                    cart = Cart.objects.create(user=request.user, paid=False)

                # Check if product already exists in cart
                cart_item_qs = cart.items.filter(product=product, variant=variant)

                if cart_item_qs.exists():
                    existing_cart_item = cart_item_qs[0]  # Use qs[0] instead of first()
                    new_quantity = existing_cart_item.quantity + quantity
                    if new_quantity <= max_stock:
                        existing_cart_item.quantity = new_quantity
                        existing_cart_item.save()
                        messages = "Quantity updated successfully!"
                    else:
                        return JsonResponse({"status": 400, "messages": f"You can't add more than {max_stock} units!"})
                else:
                    if quantity <= max_stock:
                        CartItem.objects.create(cart=cart, product=product, variant=variant, quantity=quantity)
                        messages = "Product added to cart successfully!"
                    else:
                        return JsonResponse({"status": 400, "messages": f"You can't add more than {max_stock} units!"})

                # Update cart count & total price (Optimized)
                cart_count = cart.items.count()
                cart_total = sum(item.quantity * (item.variant.price if item.variant else item.product.price) for item in cart.items.all())


                return JsonResponse({'status': 200, 'messages': messages, 'cart_count': cart_count, 'cart_total': cart_total})

            except (ValueError, TypeError, json.JSONDecodeError) as e:
                return JsonResponse({"status": 400, "messages": f"Invalid input: {str(e)}"})

        return JsonResponse({'status': 400, 'messages': 'Invalid request'})

@method_decorator(never_cache, name='dispatch')
class CartView(LoginRequiredMixin, generic.View):
    login_url = reverse_lazy('sign')

    def get(self, request):
        # Get the user's cart (or create a new one if not exists)
        cart, _ = Cart.objects.get_or_create(user=request.user, paid=False)
        
        # Get the cart items
        cart_items = CartItem.objects.filter(cart=cart)
        
        # Calculate the total number of products in the cart and the total price
        cart_count = cart_items.count()
        cart_total = sum(item.quantity * (item.product.price or 0) for item in cart_items)
        
        # Render the cart page with cart details
        return render(request, 'cart/cart.html', {
            'cart_items': cart_items,
            'cart_count': cart_count,
            'cart_total': cart_total
        })


@method_decorator(never_cache, name='dispatch')
class QuantityIncDec(LoginRequiredMixin, generic.View):
    login_url = reverse_lazy('sign')
    
    def post(self, request):
        if request.method == "POST":
            try:
                # Request থেকে JSON ডাটা নিন
                data = json.loads(request.body)
                cart_item_id = data.get("id")
                action = data.get("action")

                # cart_item_id বা action যদি না থাকে
                if not cart_item_id or not action:
                    return JsonResponse({"status": 400, "messages": "Cart item ID and action are required!"})

                # কার্ট আইটেমটি পাওয়া
                cart_item = get_object_or_404(CartItem, id=cart_item_id)

                # স্টক চেক করা
                product = cart_item.product
                variant = cart_item.variant
                
                # Variant থাকলে variant এর স্টক বাড়ানো
                if variant:
                    max_stock = variant.quantity
                else:  # Variant না থাকলে, product এর stock_max বাড়ানো
                    max_stock = product.in_stock_max

                # action অনুযায়ী পরিমাণ বাড়ানো বা কমানো
                if action == "increase":
                    if variant and cart_item.quantity < max_stock:
                        cart_item.quantity += 1
                        cart_item.save()
                        message = "Variant quantity increased successfully!"
                    elif not variant and cart_item.quantity < max_stock:
                        product.in_stock_max += 1  # Product এর stock_max বাড়ানো
                        product.save()
                        message = "Product stock_max increased successfully!"
                    else:
                        return JsonResponse({"status": 400, "messages": f"Cannot increase beyond {max_stock} units!"})
                elif action == "decrease":
                    if cart_item.quantity > 1:
                        cart_item.quantity -= 1
                        cart_item.save()
                        message = "Quantity decreased successfully!"
                    else:
                        return JsonResponse({"status": 400, "messages": "Quantity cannot be less than 1!"})
                else:
                    return JsonResponse({"status": 400, "messages": "Invalid action!"})

                # কার্টে পণ্যের সংখ্যা ও মোট মূল্য আপডেট করা
                cart = cart_item.cart

                # Prefetch all related data to optimize queries
                cart_items = CartItem.objects.prefetch_related('product', 'variant').filter(cart=cart)

                cart_count = cart_items.count()
                cart_total = sum(item.quantity * (item.variant.price if item.variant else item.product.price) for item in cart_items)

                return JsonResponse({'status': 200, 'messages': message, 'cart_count': cart_count, 'cart_total': cart_total})

            except Exception as e:
                return JsonResponse({"status": 400, "messages": str(e)})

        return JsonResponse({"status": 400, "messages": "Invalid request"})

   
@method_decorator(never_cache, name='dispatch')
class RemoveToCart(LoginRequiredMixin, generic.View):
    login_url = reverse_lazy('sign')

    def post(self, request):
        if request.method == "POST":
            try:
                data = json.loads(request.body)
                cart_item_id = data.get("id")

                if not cart_item_id:
                    return JsonResponse({"status": 400, "messages": "Missing cart item ID"})

                # Remove the cart item (optimized)
                cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user, cart__paid=False)
                if cart_item:
                    cart_item.delete()  
                    return JsonResponse({"status": 200, "messages": "Item removed from cart"})
                else:
                    return JsonResponse({"status": 404, "messages": "Cart item not found"})

            except (ValueError, TypeError, json.JSONDecodeError) as e:
                return JsonResponse({"status": 400, "messages": f"Invalid input: {str(e)}"})
        
        return JsonResponse({"status": 400, "messages": "Invalid request"})
