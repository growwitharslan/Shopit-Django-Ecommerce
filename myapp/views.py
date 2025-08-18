import stripe
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import Product, Category, Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY

# ------------------- Home -------------------
def home(request):
    categories = Category.objects.all()
    products = Product.objects.all().order_by('-id')  # latest first

    # Pagination: 6 products per page (you can change this)
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "myapp/index.html", {
        "categories": categories,
        "page_obj": page_obj,
        "total_products": products.count()
    })

# ------------------- Auth -------------------


def register_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        image = request.FILES.get("image")  # <-- now defined

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("register")

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)

        # Attach image to profile (created by signal)
        if image:
            user.profile.image = image
            user.profile.save()

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

        cart = request.session.get("cart", {})

        # ✅ store exactly this quantity
        cart[str(product_id)] = {
            "name": product.name,
            "price": float(product.price),
            "image": product.image.url,
            "quantity": quantity,
            "subtotal": float(product.price) * quantity
        }

        request.session["cart"] = cart
        overall_subtotal = sum(item["subtotal"] for item in cart.values())

        return JsonResponse({
            "status": "success",
            "quantity": cart[str(product_id)]["quantity"],  # ✅ always send real stored quantity
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
            overall_subtotal = sum(item["subtotal"] for item in cart.values())
            return JsonResponse({
                "status": "success",
                "cart_count": len(cart),
                "overall_subtotal": round(overall_subtotal, 2)
            })

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
@login_required
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
    return redirect("order_detail")

def stripe_cancel(request):
    messages.error(request, "Payment was cancelled. Please try again.")
    return redirect("cart")

# ------------------- Products by category-------------------
def products_by_category(request, slug):
    categories = Category.objects.all()
    category = get_object_or_404(Category, slug=slug)
    
    products = Product.objects.filter(category=category).order_by('-id')  # latest first
    
    paginator = Paginator(products, 9)  # 9 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'myapp/products_by_category.html', {
        'category': category,
        'page_obj': page_obj,
        'categories': categories,
        'total_products': products.count()
    })

def shop_products(request):
    categories = Category.objects.all()
    products = Product.objects.all().order_by('-id')  # latest first

    # Pagination: 6 products per page (you can adjust)
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "myapp/shop_products.html", {
        "categories": categories,
        "page_obj": page_obj,
        "total_products": products.count()
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.all()
    products = Product.objects.all()
    return render(request, "myapp/product_detail.html", {
        "product": product,
        "products": products,
        "categories": categories
    })

def order_detail(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    orders_with_items = []

    for order in orders:
        items = OrderItem.objects.filter(order=order)
        orders_with_items.append({
            "order": order,
            "items": items
        })

    categories = Category.objects.all()

    return render(request, "myapp/order_detail.html", {
        "orders_with_items": orders_with_items,
        "categories": categories
    })


def cancel_order(request):
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        order = get_object_or_404(Order, id=order_id, user=request.user)

        # Allow cancellation if order is Pending or Paid
        if order.status in ["Pending", "Paid"]:
            order.status = "Cancelled"
            order.save()
            return JsonResponse({"status": "success", "message": "Order cancelled successfully."})
        else:
            return JsonResponse({"status": "error", "message": "Order cannot be cancelled."}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=400)
