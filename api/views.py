from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import authenticate, login as django_login
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db import connection
from decimal import Decimal
from .models import Vehicle


# -------------------- HELPERS -------------------- #
def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def dictfetchone(cursor):
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row else None


def calculate_emi(principal, rate_percent, months):
    """
    Calculate EMI using standard formula:
    EMI = [P × R × (1+R)^N] / [(1+R)^N - 1]
    Where P = principal, R = monthly rate, N = months
    """
    if not principal or not rate_percent or not months:
        return None, None, None
    
    try:
        principal = float(principal)
        rate_percent = float(rate_percent)
        months = int(months)
        
        if principal <= 0 or rate_percent < 0 or months <= 0:
            return None, None, None
        
        # Convert annual rate to monthly rate
        monthly_rate = rate_percent / (12 * 100)
        
        if monthly_rate == 0:
            # If rate is 0, simple division
            emi = principal / months
        else:
            # Standard EMI formula
            emi = (principal * monthly_rate * ((1 + monthly_rate) ** months)) / (
                ((1 + monthly_rate) ** months) - 1
            )
        
        total_amount = emi * months
        total_interest = total_amount - principal
        
        return round(emi, 2), round(total_amount, 2), round(total_interest, 2)
    except:
        return None, None, None


# -------------------- INDEX -------------------- #
def index(request):
    vehicles = Vehicle.objects.all().order_by('brand', 'name')
    
    brands = {}
    for v in vehicles:
        brands.setdefault(v.brand, []).append(v)

    return render(request, "index.html", {"brands": brands})


# -------------------- LOGIN -------------------- #
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        # Try admin login first (Django superuser)
        admin_user = authenticate(request, username=username, password=password)
        if admin_user is not None and (admin_user.is_staff or admin_user.is_superuser):
            django_login(request, admin_user)
            request.session["admin"] = True
            messages.success(request, "✅ Admin login successful!")
            return redirect("dashboard")

        # Try regular user login (custom users table) - lookup by email
        email = request.POST.get("username")  # User might enter email
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s", [email])
            user = dictfetchone(cursor)

        if user and check_password(password, user["password"]):
            request.session["user_id"] = user["id"]
            request.session["user_name"] = user["name"]
            messages.success(request, f"👋 Welcome {user['name']}!")
            return redirect("index")
        else:
            messages.error(request, "❌ Invalid credentials. Please check your username and password.")
            return redirect("login")

    return render(request, "login.html")


# -------------------- REGISTER -------------------- #
def register(request):
    if request.method == "POST":
        name = request.POST["name"]
        email = request.POST["email"]
        password = request.POST["password"]

        # check user exists
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s", [email])
            account = dictfetchone(cursor)

        if account:
            messages.warning(request, "⚠️ Email already exists.")
            return redirect("login")

        # insert user
        hashed_password = make_password(password)

        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                [name, email, hashed_password],
            )

        # email (safe - no crash)
        try:
            send_mail(
                subject="🎉 Welcome to CarBazzar!",
                message=f"Hi {name}, welcome to CarBazzar 🚗",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception as e:
            print("Email error:", e)

        messages.success(request, "✅ Registration successful!")
        return redirect("login")

    return render(request, "register.html")


# -------------------- LOGOUT -------------------- #
def logout_view(request):
    request.session.flush()
    return redirect("index")


# -------------------- PAGES -------------------- #
def findcar(request):
    return render(request, "findcar.html")


def comparecar(request):
    return render(request, "comparecar.html")


def sellcar(request):
    return render(request, "sellcar.html")


# -------------------- VEHICLE DETAILS -------------------- #
def vehicle_details(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    
    # Handle EMI calculation
    emi_monthly = None
    emi_total = None
    emi_interest = None
    
    if request.method == "POST":
        down_payment = request.POST.get("down_payment", 0)
        interest_rate = request.POST.get("interest_rate", 9)
        tenure = request.POST.get("tenure", 60)
        selected_variant = request.POST.get("variant", "base")
        
        # Get variant price
        if selected_variant == "base":
            price = vehicle.base_price or vehicle.price
        elif selected_variant == "mid":
            price = vehicle.mid_price or vehicle.base_price or vehicle.price
        else:  # top
            price = vehicle.top_price or vehicle.mid_price or vehicle.base_price or vehicle.price
        
        if price:
            try:
                price = float(price)
                down_payment = float(down_payment) if down_payment else 0
                
                # Calculate loan amount
                loan_amount = price - down_payment
                
                if loan_amount > 0:
                    emi_monthly, emi_total, emi_interest = calculate_emi(
                        loan_amount, interest_rate, tenure
                    )
            except:
                pass
    
    return render(request, "vehicle_detail.html", {
        "vehicle": vehicle,
        "emi_monthly": emi_monthly,
        "emi_total": emi_total,
        "emi_interest": emi_interest,
    })


# -------------------- ADMIN DASHBOARD -------------------- #
def dashboard(request):
    if not request.session.get("admin"):
        return redirect("login")

    vehicles = Vehicle.objects.all()
    return render(request, "dashboard.html", {"vehicles": vehicles})


# -------------------- ADD VEHICLE -------------------- #
def add_vehicle(request):
    if not request.session.get("admin"):
        return redirect("login")

    if request.method == "POST":
        vehicle_data = {
            'name': request.POST.get("name"),
            'brand': request.POST.get("brand"),
            'description': request.POST.get("description"),
            'price': request.POST.get("price", ""),
            'base_price': request.POST.get("base_price") or None,
            'mid_price': request.POST.get("mid_price") or None,
            'top_price': request.POST.get("top_price") or None,
            'fuel_type': request.POST.get("fuel_type"),
            'engine': request.POST.get("engine"),
            'power': request.POST.get("power"),
            'mileage': request.POST.get("mileage"),
            'transmission': request.POST.get("transmission"),
            'seating_capacity': request.POST.get("seating_capacity") or None,
            'safety_rating': request.POST.get("safety_rating"),
            'central_locking': request.POST.get("central_locking") == "on",
            'air_conditioner': request.POST.get("air_conditioner") == "on",
            'power_windows': request.POST.get("power_windows") == "on",
            'keyless_entry': request.POST.get("keyless_entry") == "on",
            'bluetooth': request.POST.get("bluetooth") == "on",
            'android_auto': request.POST.get("android_auto") == "on",
            'steering_controls': request.POST.get("steering_controls") == "on",
        }
        
        if request.FILES.get("image1"):
            vehicle_data['image1'] = request.FILES['image1']
        if request.FILES.get("image2"):
            vehicle_data['image2'] = request.FILES['image2']
        if request.FILES.get("image3"):
            vehicle_data['image3'] = request.FILES['image3']
        
        Vehicle.objects.create(**vehicle_data)
        messages.success(request, "✅ Vehicle added successfully!")
        return redirect("dashboard")

    return render(request, "add_vehicle.html")


# -------------------- UPDATE VEHICLE -------------------- #
def update_vehicle(request, vehicle_id):
    if not request.session.get("admin"):
        return redirect("login")

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == "POST":
        vehicle.name = request.POST.get("name")
        vehicle.brand = request.POST.get("brand")
        vehicle.description = request.POST.get("description")
        vehicle.price = request.POST.get("price", "")
        vehicle.base_price = request.POST.get("base_price") or None
        vehicle.mid_price = request.POST.get("mid_price") or None
        vehicle.top_price = request.POST.get("top_price") or None
        vehicle.fuel_type = request.POST.get("fuel_type")
        vehicle.engine = request.POST.get("engine")
        vehicle.power = request.POST.get("power")
        vehicle.mileage = request.POST.get("mileage")
        vehicle.transmission = request.POST.get("transmission")
        vehicle.seating_capacity = request.POST.get("seating_capacity") or None
        vehicle.safety_rating = request.POST.get("safety_rating")
        vehicle.central_locking = request.POST.get("central_locking") == "on"
        vehicle.air_conditioner = request.POST.get("air_conditioner") == "on"
        vehicle.power_windows = request.POST.get("power_windows") == "on"
        vehicle.keyless_entry = request.POST.get("keyless_entry") == "on"
        vehicle.bluetooth = request.POST.get("bluetooth") == "on"
        vehicle.android_auto = request.POST.get("android_auto") == "on"
        vehicle.steering_controls = request.POST.get("steering_controls") == "on"
        
        if request.FILES.get("image1"):
            vehicle.image1 = request.FILES['image1']
        if request.FILES.get("image2"):
            vehicle.image2 = request.FILES['image2']
        if request.FILES.get("image3"):
            vehicle.image3 = request.FILES['image3']

        vehicle.save()
        messages.success(request, "✅ Vehicle updated successfully!")
        return redirect("dashboard")

    return render(request, "update_vehicle.html", {"vehicle": vehicle})


# -------------------- DELETE VEHICLE -------------------- #
def delete_vehicle(request, vehicle_id):
    if not request.session.get("admin"):
        return redirect("login")

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == "POST":
        vehicle.delete()
        messages.success(request, "✅ Vehicle deleted successfully!")
        return redirect("dashboard")

    return render(request, "delete_vehicle.html", {"vehicle": vehicle})