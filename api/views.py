from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from django.db import connection
from django.http import HttpResponse
from .models import Vehicle


# -------------------- HELPER FUNCTIONS -------------------- #
def dictfetchall(cursor):
    """Return all rows from a cursor as a list of dicts"""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def dictfetchone(cursor):
    """Return one row from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row else None


# -------------------- INDEX -------------------- #
def index(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM api_vehicle ORDER BY brand, name")
        vehicles = dictfetchall(cursor)

    brands = {}
    for v in vehicles:
        brand = v["brand"]
        brands.setdefault(brand, []).append(v)

    return render(request, "index.html", {"brands": brands})


# -------------------- LOGIN -------------------- #
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # --- Admin Login ---
        if email == settings.ADMIN_EMAIL and password == settings.ADMIN_PASSWORD:
            request.session["admin"] = True
            messages.success(request, "✅ Admin login successful!")
            return redirect("dashboard")

        # --- User Login ---
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s", [email])
            user = dictfetchone(cursor)

        if user and check_password(password, user["password"]):
            request.session["user_id"] = user["id"]
            request.session["user_name"] = user["name"]
            messages.success(request, f"👋 Welcome back, {user['name']}!")
            return redirect("index")
        else:
            messages.error(request, "❌ Invalid email or password.")
            return redirect("login")

    return render(request, "login.html")


# -------------------- REGISTER -------------------- #
def register(request):
    if request.method == "POST":
        name = request.POST["name"]
        email = request.POST["email"]
        password = request.POST["password"]

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s", [email])
            account = dictfetchone(cursor)

        if account:
            messages.warning(request, "⚠️ Email already exists. Please login instead.")
            return redirect("login")

        # --- Try to send email first ---
        try:
            send_mail(
                subject="🎉 Welcome to CarBazzar!",
                message=f"Hi {name},\n\nWelcome to CarBazzar! 🚗\nWe’re excited to have you join our community of car lovers. At Car Bazzar, finding your dream car is easier than ever — explore a wide range of vehicles, compare features, check prices, and discover the perfect match for your needs. Whether you’re looking for comfort, style, or performance, we’re here to help you make the right choice..\n\n– The CarBazzar Team",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            # ✅ Only insert user after successful email
            hashed_password = make_password(password)
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                    [name, email, hashed_password],
                )

            messages.success(request, "✅ Registration successful! Email sent.")
            return redirect("login")

        except BadHeaderError:
            messages.error(request, "❌ Invalid email header.")
        except Exception as e:
            print("Email send error:", e)
            messages.error(request, "❌ Could not send email. Try again later.")
            return redirect("register")

    return render(request, "register.html")


# -------------------- LOGOUT -------------------- #
def logout_view(request):
    request.session.flush()
    messages.info(request, "You have been logged out.")
    return redirect("index")


# -------------------- USER ROUTES -------------------- #
def findcar(request):
    return render(request, "findcar.html")


def comparecar(request):
    return render(request, "comparecar.html")


def sellcar(request):
    return render(request, "sellcar.html")


# -------------------- VEHICLE DETAILS -------------------- #
def vehicle_details(request, vehicle_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM api_vehicle WHERE id = %s", [vehicle_id])
        vehicle = dictfetchone(cursor)

    if not vehicle:
        messages.error(request, "Vehicle not found.")
        return redirect("index")

    return render(request, "vehicle_detail.html", {"v": vehicle})


# -------------------- ADMIN DASHBOARD -------------------- #
def dashboard(request):
    if not request.session.get("admin"):
        messages.error(request, "Access denied! Admins only.")
        return redirect("login")

    vehicles = Vehicle.objects.all()
    return render(request, "dashboard.html", {"vehicles": vehicles})


# -------------------- ADD VEHICLE -------------------- #
def add_vehicle(request):
    if not request.session.get("admin"):
        messages.error(request, "Access denied! Admins only.")
        return redirect("login")

    if request.method == "POST":
        name = request.POST.get("name")
        brand = request.POST.get("brand")
        price = request.POST.get("price")
        fuel_type = request.POST.get("fuel_type")
        description = request.POST.get("description")
        image = request.FILES.get("image")

        Vehicle.objects.create(
            name=name,
            brand=brand,
            price=price,
            fuel_type=fuel_type,
            description=description,
            image=image,
        )
        messages.success(request, f"✅ Vehicle '{name}' added successfully!")
        return redirect("dashboard")

    return render(request, "add_vehicle.html")


# -------------------- UPDATE VEHICLE -------------------- #
def update_vehicle(request, vehicle_id):
    if not request.session.get("admin"):
        messages.error(request, "Access denied! Admins only.")
        return redirect("login")

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == "POST":
        vehicle.name = request.POST.get("name")
        vehicle.brand = request.POST.get("brand")
        vehicle.price = request.POST.get("price")
        vehicle.fuel_type = request.POST.get("fuel_type")
        vehicle.description = request.POST.get("description")

        if request.FILES.get("image"):
            vehicle.image_path = request.FILES.get("image")

        vehicle.save()
        messages.success(request, f"✅ Vehicle '{vehicle.name}' updated successfully!")
        return redirect("dashboard")

    return render(request, "update_vehicle.html", {"vehicle": vehicle})


# -------------------- DELETE VEHICLE -------------------- #
def delete_vehicle(request, vehicle_id):
    if not request.session.get("admin"):
        messages.error(request, "Access denied! Admins only.")
        return redirect("login")

    vehicle = get_object_or_404(Vehicle, id=vehicle_id)

    if request.method == "POST":
        vehicle.delete()
        messages.success(request, "🚗 Vehicle deleted successfully.")
        return redirect("dashboard")

    return render(request, "delete_vehicle.html", {"vehicle": vehicle})
# -------------------- VEHICLE DETAILS -------------------- #
from django.shortcuts import render, get_object_or_404
from .models import Vehicle

def vehicle_details(request, vehicle_id):
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    return render(request, "vehicle_details.html", {"vehicle": vehicle})
