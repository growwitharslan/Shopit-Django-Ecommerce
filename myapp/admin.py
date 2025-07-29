from django.contrib import admin
from .models import Product, Category, ProductGallery

class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 5

# Custom Product admin
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductGalleryInline]
    list_display = ['name', 'price', 'stock', 'category']
    search_fields = ['name', 'description']
    list_filter = ['category']

# Register models properly
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)  # Custom admin attached here
admin.site.register(ProductGallery)
