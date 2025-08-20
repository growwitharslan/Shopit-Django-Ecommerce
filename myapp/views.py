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
from django.db.models import Q
from .models import Product, Category, Order, OrderItem
from django.views.decorators.http import require_POST
from django.http import HttpResponse
stripe.api_key = settings.STRIPE_SECRET_KEY



# ------------------- Home -------------------
def home(request):
    categories = Category.objects.all()
    products = Product.objects.all().order_by('-id')  # latest first

    # Pagination: 12 products per page (you can change this)
    paginator = Paginator(products, 12)
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
            "stock": product.stock,
            "quantity": quantity,
            "subtotal": float(product.price) * quantity
        }

        request.session["cart"] = cart
        overall_subtotal = sum(item["subtotal"] for item in cart.values())
        cart_count = sum(item["quantity"] for item in cart.values())
        return JsonResponse({
            "status": "success",
            "quantity": cart[str(product_id)]["quantity"],  # ✅ always send real stored quantity
            "cart_count": cart_count,            
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
                "cart_count": sum(item["quantity"] for item in cart.values()),
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
            client_reference_id=request.user.id,  # ✅ attach user
     )
        return JsonResponse({"id": session.id})

def stripe_success(request):
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
    
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'myapp/products_by_category.html', {
        'category': category,
        'page_obj': page_obj,
        'categories': categories,
        'total_products': products.count()
    })

# ------------------- Refund Management -------------------
@require_POST
@login_required
def refund_order(request):
    order_id = request.POST.get("order_id")

    try:
        order = Order.objects.get(id=order_id, user=request.user)

        if order.status == "Completed":
            order.status = "Refunded"
            order.save()
            return JsonResponse({"status": "success", "message": "Refund process will be soon."})
        else:
            return JsonResponse({"status": "error", "message": "Only completed orders can be refunded"})

    except Order.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Order not found"})



def shop_products(request):
    categories = Category.objects.all()
    query = request.GET.get("q")  # search keyword
    products = Product.objects.all().order_by("-id")  # latest first

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by("-id")

    # Pagination: 12 products per page
    paginator = Paginator(products, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "myapp/shop_products.html", {
        "categories": categories,
        "page_obj": page_obj,
        "total_products": products.count(),
        "query": query,   # so you can keep the search box filled
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
    cancelable_statuses = ["Pending", "Paid"]
    refundable_statuses = ["Delivered", "Completed"]
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
        "categories": categories,
        "cancelable_statuses": cancelable_statuses,
        "refundable_statuses": refundable_statuses,
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



@require_POST
@csrf_exempt  # Stripe won't send CSRF tokens
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        # Optional: retrieve line items
        line_items = stripe.checkout.Session.list_line_items(session["id"], limit=100)

        # Get user (if logged in you can pass `client_reference_id` in create_checkout_session)
        user_id = session.get("client_reference_id")
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                pass

        # Calculate total from Stripe session
        total_amount = Decimal(session["amount_total"]) / 100

        # Create order
        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            status="Paid",
        )

        # Create items
        for item in line_items["data"]:
            name = item["description"]
            quantity = item["quantity"]
            unit_amount = Decimal(item["price"]["unit_amount"]) / 100

            # Find product by name (⚠️ better: pass product_id in metadata at checkout)
            try:
                product = Product.objects.get(name=name)
            except Product.DoesNotExist:
                continue

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=unit_amount
            )

            # Decrement stock
            product.stock -= quantity
            product.save()

    return HttpResponse(status=200)