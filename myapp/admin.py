from django.contrib import admin
from .models import Product, Category, ProductGallery, Order, OrderItem

class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 5

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductGalleryInline]
    list_display = ['name', 'price', 'stock', 'category']
    search_fields = ['name', 'description']
    list_filter = ['category']

# Simple Order admin
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']

# Simple OrderItem admin
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']

# Register models properly
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductGallery)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
