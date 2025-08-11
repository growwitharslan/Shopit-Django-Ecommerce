import stripe
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import Product, Category, Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY

# ------------------- Home -------------------
def home(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    return render(request, "myapp/index.html", {"products": products, "categories": categories})

# ------------------- Auth -------------------
def register_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("register")

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        messages.success(request, "Signed up successfully!")
        return redirect("home")

    return render(request, "auth/register.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid credentials")
            return redirect("login")

    return render(request, "auth/login.html")

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("login")

# ------------------- Profile -------------------
@login_required
def profile(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    categories = Category.objects.all()
    return render(request, "myapp/profile_details.html", {"user": user, "categories": categories})

# ------------------- Cart -------------------
def add_to_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        quantity = int(request.POST.get("quantity", 1))
        product = get_object_or_404(Product, id=product_id)

        product_price = float(product.price)
        product_subtotal = product_price * quantity
        cart = request.session.get("cart", {})

        if str(product_id) in cart:
            cart[str(product_id)]["quantity"] += quantity
            cart[str(product_id)]["subtotal"] = cart[str(product_id)]["price"] * cart[str(product_id)]["quantity"]
        else:
            cart[str(product_id)] = {
                "name": product.name,
                "price": product_price,
                "image": product.image.url,
                "quantity": quantity,
                "subtotal": product_subtotal
            }

        request.session["cart"] = cart
        overall_subtotal = sum(item["subtotal"] for item in cart.values())

        return JsonResponse({
            "status": "success",
            "cart_count": len(cart),
            "product_subtotal": round(cart[str(product_id)]["subtotal"], 2),
            "overall_subtotal": round(overall_subtotal, 2)
        })

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
    categories = Category.objects.all()
    products = Product.objects.all()
    overall_subtotal = sum(item["subtotal"] for item in cart.values())
    return render(request, "myapp/cart.html", {
        "cart": cart,
        "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY,
        "products": products,
        "categories": categories,
        "overall_subtotal": round(overall_subtotal, 2)
    })

# ------------------- Stripe -------------------
@csrf_exempt
def create_checkout_session(request):
    if request.method == "POST":
        cart = request.session.get("cart", {})
        line_items = []

        for item in cart.values():
            line_items.append({
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": item["name"],
                    },
                    "unit_amount": int(float(item["price"]) * 100),
                },
                "quantity": item["quantity"],
            })

        if not line_items:
            return JsonResponse({"error": "Cart is empty"}, status=400)

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url="http://127.0.0.1:8000/checkout-success/",
            cancel_url="http://127.0.0.1:8000/checkout-cancelled/",
        )
        return JsonResponse({"id": session.id})

@login_required
def stripe_success(request):
    cart = request.session.get("cart", {})

    if not cart:
        messages.error(request, "Cart is empty. Cannot create order.")
        return redirect("cart")

    total_amount = sum(Decimal(item["subtotal"]) for item in cart.values())
    order = Order.objects.create(user=request.user, total_amount=total_amount, status="Paid")

    for product_id, item in cart.items():
        product = Product.objects.get(id=product_id)
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=item["quantity"],
            price=Decimal(item["price"])
        )

    request.session["cart"] = {}
    messages.success(request, "Payment successful! Thank you for your order.")
    return redirect("cart")

def stripe_cancel(request):
    messages.error(request, "Payment was cancelled. Please try again.")
    return redirect("cart")

# ------------------- Products -------------------
def products_by_category(request, slug):
    categories = Category.objects.all()
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    return render(request, 'myapp/products_by_category.html', {
        'category': category,
        'products': products,
        'categories': categories,
    })

def shop_products(request):
    categories = Category.objects.all()
    products = Product.objects.all()
    return render(request, "myapp/shop_products.html", {"products": products, "categories": categories})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()
    products = Product.objects.all()
    return render(request, "myapp/product_detail.html", {
        "product": product,
        "products": products,
        "categories": categories
    })
