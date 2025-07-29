import stripe
from .models import Product, Category
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.models import User
from decimal import Decimal
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
stripe.api_key = settings.STRIPE_SECRET_KEY
# Create your views here.


def home(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    return render(request, "myapp/index.html", {"products": products, "categories": categories})


def register_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("register")

        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        login(request, user)
        return redirect("home")  # or dashboard
    return render(request, "auth/register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")  # or dashboard
        else:
            messages.error(request, "Invalid credentials")
            return redirect("login")

    return render(request, "auth/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def add_to_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        quantity = int(request.POST.get("quantity", 1))

        product = get_object_or_404(Product, id=product_id)
        cart = request.session.get("cart", {})

        if str(product_id) in cart:
            cart[str(product_id)]["quantity"] += quantity
        else:
            cart[str(product_id)] = {
                "name": product.name,
                "price": str(product.price),
                "image": product.image.url,
                "quantity": quantity,
            }
        request.session["cart"] = cart
        return JsonResponse({"status": "success", "cart_count": len(cart)})

    return JsonResponse({"status": "failed"}, status=400)

def remove_from_cart_ajax(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        cart = request.session.get("cart", {})

        if product_id in cart:
            del cart[product_id]
            request.session["cart"] = cart
            return JsonResponse({"status": "success", "cart_count": len(cart)})

    return JsonResponse({"status": "failed"}, status=400)

    
def cart(request):
    cart = request.session.get("cart", {})
    message = request.session.pop("message", None)
    categories = Category.objects.all()
    products = Product.objects.all()
    return render(
        request,
        "myapp/cart.html",
        {
            "cart": cart,
            "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY,
            "message": message,
            "products": products,
            "categories": categories
        },
    )


def remove_from_cart_ajax(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        cart = request.session.get("cart", {})

        if product_id in cart:
            del cart[product_id]
            request.session["cart"] = cart
            return JsonResponse({"status": "success", "cart_count": len(cart)})

    return JsonResponse({"status": "failed"}, status=400)


@csrf_exempt
def create_checkout_session(request):
    if request.method == "POST":
        cart = request.session.get("cart", [])

        line_items = []
        for item in cart.values():
            line_items.append(
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": item["name"],
                        },
                        "unit_amount": int(float(item["price"]) * 100),
                    },
                    "quantity": item["quantity"],
                }
            )

        if not line_items:
            return JsonResponse({"error", "cart is empty"}, status=400)

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url="http://127.0.0.1:8000/checkout-success/",
            cancel_url="http://127.0.0.1:8000/checkout-cancelled/",
        )
        return JsonResponse({"id": session.id})


def stripe_success(request):
    request.session["message"] = {
        "type": "success",
        "text": "Payment successful! Thank you for your order.",
    }
    # Optionally clear cart after successful payment
    request.session["cart"] = {}
    return redirect("cart")


def stripe_cancel(request):
    request.session["message"] = {
        "type": "danger",
        "text": "Payment was cancelled. Please try again.",
    }
    return redirect("cart")
    ...

    
def products_by_category(request, slug):
    categories = Category.objects.all()
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    
    return render(request, 'myapp/products_by_category.html', {
        'category': category,
        'products': products,
        'categories': categories,
    })




def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()
    products = Product.objects.all()
    return render(request, "myapp/product_detail.html", {"product": product, "products": products, "categories": categories})