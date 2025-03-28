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
@method_decorator(never_cache, name='dispatch')
class AddToCart(LoginRequiredMixin, generic.View):
    login_url = reverse_lazy('sign') 

    def post(self, request):
        if request.method == "POST":
            try:
                # Parse JSON data from request
                data = json.loads(request.body)  
                size_id = data.get("size_id")
                color_id = data.get("color_id")
                product_id = data.get("product_id")
                quantity = data.get("quantity")
                

                product = get_object_or_404 (Product, id=product_id)
                variant = get_object_or_404(Variants, size_id=size_id, color_id=color_id)

                return JsonResponse({"status": 200, "messages": "Product added to cart successfully"})  
                
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                # Handle invalid input errors
                return JsonResponse({"status": 400, "messages": f"Invalid input: {str(e)}"})
        
        return JsonResponse({'status': 400, 'messages': 'Invalid request'})

@method_decorator(never_cache, name='dispatch')
class CartView(LoginRequiredMixin, generic.View):
    login_url = reverse_lazy('sign')

    def get(self, request):
        return render(request, 'cart/cart.html', {})

    def post(self, request):
        if request.method == "POST":
            try:
                data = json.loads(request.body)
                coupon_code = data.get("coupon_code", "").strip()

            except json.JSONDecodeError:
                return JsonResponse({'status': 400, 'messages': 'Invalid data format.'})

        return JsonResponse({'status': 400, 'messages': 'Invalid request'})

@method_decorator(never_cache, name='dispatch')
class QuantityIncDec(LoginRequiredMixin, generic.View):
    login_url = reverse_lazy('sign')
    
    def post(self, request):
        if request.method == "POST":
            try:
                data = json.loads(request.body)
                cart_item_id = data.get("id")
                action = data.get("action")

   

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

 

            except Exception as e:
                return JsonResponse({"status": 400, "messages": f"Error: {str(e)}"})
        return JsonResponse({"status": 400, "messages": "Invalid request"})
 
        
