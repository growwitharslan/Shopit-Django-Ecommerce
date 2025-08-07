# SHOPit - Django E-commerce Platform

> **⚠️ Work in Progress** - This project is currently under development and not yet completed. Features may be incomplete or subject to change.

A modern, full-featured e-commerce web application built with Django, featuring user authentication, product management, shopping cart functionality, and Stripe payment integration.

## 🚀 Features

### Core Functionality
- **User Authentication**: Registration, login, logout, and user profiles
- **Product Management**: Categories, products with images, descriptions, and pricing
- **Shopping Cart**: Session-based cart with add/remove functionality
- **Payment Processing**: Stripe integration for secure online payments
- **Responsive Design**: Modern, mobile-friendly UI using Bootstrap and custom CSS

### Key Features
- **Product Categories**: Organized product browsing by categories
- **Product Details**: Detailed product pages with images and descriptions
- **Cart Management**: Add/remove items, quantity management
- **Checkout Process**: Secure payment flow with Stripe
- **User Profiles**: Personal user dashboard
- **Admin Panel**: Django admin for product and category management

## 🛠️ Technology Stack

- **Backend**: Django 5.2+
- **Database**: MySQL
- **Payment**: Stripe API
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Icons**: Font Awesome, Material Design Icons
- **Styling**: Custom CSS with responsive design

## 📋 Prerequisites

Before running this project, make sure you have the following installed:

- Python 3.8+
- MySQL Server
- pip (Python package installer)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SHOPit
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install django
   pip install mysqlclient
   pip install stripe
   pip install Pillow
   ```

4. **Set up the database**
   ```bash
   # Create MySQL database
   mysql -u root -p
   CREATE DATABASE shopit_db;
   ```

5. **Configure settings**
   - Update database credentials in `SHOPit/settings.py` if needed
   - Set your Stripe API keys in `SHOPit/settings.py`:
     ```python
     STRIPE_PUBLISHABLE_KEY = 'your_publishable_key'
     STRIPE_SECRET_KEY = 'your_secret_key'
     ```

6. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## 📁 Project Structure

```
SHOPit/
├── manage.py                 # Django management script
├── SHOPit/                   # Main project directory
│   ├── __init__.py
│   ├── settings.py          # Project settings
│   ├── urls.py              # Main URL configuration
│   ├── wsgi.py              # WSGI configuration
│   └── asgi.py              # ASGI configuration
├── myapp/                    # Main application
│   ├── __init__.py
│   ├── admin.py             # Admin panel configuration
│   ├── models.py            # Database models
│   ├── views.py             # View functions
│   ├── apps.py              # App configuration
│   ├── tests.py             # Test files
│   ├── templates/           # HTML templates
│   │   ├── myapp/           # Main app templates
│   │   └── auth/            # Authentication templates
│   ├── static/              # Static files (CSS, JS, images)
│   │   ├── css/
│   │   ├── js/
│   │   ├── images/
│   │   └── fonts/
│   └── templatetags/        # Custom template tags
├── media/                    # User-uploaded files
└── README.md                # This file
```

## 🗄️ Database Models

### Category
- `name`: Category name
- `image`: Category image
- `slug`: URL-friendly identifier
- `created_at`: Creation timestamp

### Product
- `name`: Product name
- `image`: Main product image
- `image2`: Secondary product image
- `description`: Product description
- `price`: Product price
- `stock`: Available stock quantity
- `category`: Foreign key to Category

### Order
- `user`: User who placed the order
- `total_amount`: Total order amount
- `created_at`: Order creation timestamp
- `status`: Order status (Pending, etc.)

### OrderItem
- `order`: Foreign key to Order
- `product`: Foreign key to Product
- `quantity`: Item quantity
- `price`: Item price at time of purchase

### ProductGallery
- `product`: Foreign key to Product
- `image`: Gallery image

## 🔧 Configuration

### Environment Variables
The following settings can be configured in `SHOPit/settings.py`:

- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode (set to False in production)
- `ALLOWED_HOSTS`: Allowed host names
- Database configuration
- Stripe API keys

### Stripe Configuration
To enable payments, you need to:

1. Create a Stripe account
2. Get your API keys from the Stripe dashboard
3. Update the keys in `settings.py`:
   ```python
   STRIPE_PUBLISHABLE_KEY = 'pk_test_your_key'
   STRIPE_SECRET_KEY = 'sk_test_your_key'
   ```

## 🎨 Customization

### Styling
The project uses a custom CSS framework with:
- Bootstrap for responsive layout
- Custom CSS for styling
- Font Awesome and Material Design Icons
- Slick carousel for image sliders

### Templates
Templates are organized in:
- `myapp/templates/myapp/`: Main application templates
- `myapp/templates/auth/`: Authentication templates

## 🔒 Security Features

- CSRF protection enabled
- Session-based authentication
- Secure password validation
- SQL injection protection (Django ORM)
- XSS protection

## 🧪 Testing

Run tests with:
```bash
python manage.py test
```

## 📦 Deployment

For production deployment:

1. Set `DEBUG = False` in settings
2. Configure production database
3. Set up static file serving
4. Configure media file storage
5. Set up HTTPS
6. Update `ALLOWED_HOSTS`
7. Use environment variables for sensitive data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 👨‍💻 Author

**devArsal** - [GitHub Profile]

## 🙏 Acknowledgments

- Django framework and community
- Stripe for payment processing
- Bootstrap for responsive design
- Font Awesome for icons

## 📞 Support

For support and questions, please open an issue in the repository or contact the development team.

---

**⚠️ Important Notes**: 
- This is a **work-in-progress** project and not yet production-ready
- Features may be incomplete or subject to change during development
- For production use, ensure all security measures are properly configured and tested
- The project is actively being developed and improved