from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from myapp import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),

    path("product/<int:product_id>/", views.product_detail, name="product_detail"),  # view a post

    path('category/<slug:slug>/', views.products_by_category, name='products_by_category'),
    path('/add-to-cart', views.add_to_cart, name= "add_to_cart"),
    path('ajax/remove-from-cart/', views.remove_from_cart_ajax, name='remove_from_cart_ajax'),
    path('cart/', views.cart, name='cart'),

    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('checkout-success/', views.stripe_success, name='checkout_success'),
    path('checkout-cancelled/', views.stripe_cancel, name='checkout_cancel'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
