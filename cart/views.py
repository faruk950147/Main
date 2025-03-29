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
                size_id = data.get("size_id")  # optional
                color_id = data.get("color_id")  # optional
                quantity = data.get("quantity")  # ensure quantity is an integer and it is required
                product_id = data.get("product_id")  # ensure product_id is an integer and it is required

                # ensure quantity is not None and it is greater than 0
                if quantity is None or int(quantity) <= 0:
                    return JsonResponse({"status": 400, "messages": "Quantity must be greater than 0!"})

                # convert quantity to an integer
                quantity = int(quantity)

                # ensure product_id is not None
                if not product_id:
                    return JsonResponse({"status": 400, "messages": "Product ID is required!"})

                # get the product
                product = get_object_or_404(Product, id=product_id)

                # get the variant
                variant = None
                if size_id or color_id:
                    variant_qs = Variants.objects.filter(product=product)
                    if size_id:
                        variant_qs = variant_qs.filter(size_id=size_id)
                    if color_id:
                        variant_qs = variant_qs.filter(color_id=color_id)

                    if variant_qs.exists():
                        variant = variant_qs[0]  # get the first variant
                    else:
                        return JsonResponse({"status": 400, "messages": "Variant not found!"})

                # ensure the stock is not 0
                max_stock = variant.quantity if variant else product.in_stock_max
                if max_stock <= 0:
                    return JsonResponse({"status": 400, "messages": "Product out of stock!"})

                # get the cart or create a new one
                cart, _ = Cart.objects.get_or_create(user=request.user, paid=False)

                # check if the product already exists in the cart
                cart_item_qs = CartItem.objects.filter(cart=cart, product=product, variant=variant)

                if cart_item_qs.exists():
                    existing_cart_item = cart_item_qs[0]
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

                # update the cart product count and total price
                cart_products = CartItem.objects.filter(cart=cart)
                cart_count = cart_products.count()
                cart_total = sum(item.quantity * (item.product.price or 0) for item in cart_products)

                return JsonResponse({'status': 200, 'messages': messages, 'cart_count': cart_count, 'cart_total': cart_total})

            except (ValueError, TypeError, json.JSONDecodeError, IndexError) as e:
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
                cart_products = CartItem.objects.filter(cart=cart)
                cart_count = cart_products.count()
                cart_total = sum(item.quantity * (item.product.price or 0) for item in cart_products)

                return JsonResponse({'status': 200, 'messages': message, 'cart_count': cart_count, 'cart_total': cart_total})

            except Exception as e:
                return JsonResponse({"status": 400, "messages": str(e)})

        return JsonResponse({"status": 400, "messages": "Invalid request"})


@method_decorator(never_cache, name='dispatch')
class RemoveToCart(LoginRequiredMixin, generic.View):
    login_url = reverse_lazy('sign')

    def post(self, request):
        try:
            data = json.loads(request.body)
            cart_item_id = data.get("id")

            if not cart_item_id:
                return JsonResponse({"status": 400, "messages": "Missing cart item ID"})

            # Remove the cart item
            try:
                cart_item = CartItem.objects.get(id=cart_item_id, cart__user=request.user, cart__paid=False)
                cart_item.delete()
                return JsonResponse({"status": 200, "messages": "Item removed from cart"})
            except CartItem.DoesNotExist:
                return JsonResponse({"status": 404, "messages": "Cart item not found"})

        except json.JSONDecodeError:
            return JsonResponse({"status": 400, "messages": "Invalid JSON data"})
        except Exception as e:
            return JsonResponse({"status": 400, "messages": f"Error: {str(e)}"})

 
        
