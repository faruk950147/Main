from django.shortcuts import redirect, get_object_or_404
from django.db.models import Min, Max
from django.utils import timezone
from cart.models import Cart
from stories.models import (
    Category, Brand, Product, Images, Color, Size, Variants,
)

def get_filters(request):


    return {
  
    }

