from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from datetime import datetime
from .models import customer, Booking, ContactQuery
from django.contrib import messages
import qrcode
from io import BytesIO
import base64
from django.core.mail import send_mail
from django.conf import settings
import pyotp
import random
from django.http import JsonResponse
import json
from django.utils import timezone
import asyncio
import re
from urllib.parse import quote_plus
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# ─────────────────────────────────────────────
# Public Pages
# ─────────────────────────────────────────────

def home(request):
    return render(request, "index.html")

def about(request):
    return render(request, "about.html")

def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject", "")
        message = request.POST.get("message")
        
        ContactQuery.objects.create(name=name, email=email, subject=subject, message=message)
        messages.success(request, "Your message has been sent successfully. We will get back to you soon!")
        return redirect('/contact')
        
    return render(request, "contact.html")


def book(request):
    current_time = datetime.now()
    return render(request, "book.html", {'current_time': current_time})


def register(request):
    return render(request, "register.html")


def login(request):
    return render(request, "login.html")


# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────

def save(request):
    if request.method == "POST":
        nm = request.POST["name"]
        em = request.POST["email"]
        nmb = request.POST["number"]
        add = request.POST["address"]
        ct = request.POST["city"]
        st = request.POST["state"]
        pin = request.POST["pincode"]
        ps = request.POST["password"]
        cps = request.POST["confpassword"]

        if ps == cps:
            data = customer(name=nm, email=em, number=nmb, address=add, city=ct, state=st, pincode=pin, password=ps)
            data.save()
            return redirect("/login")
        else:
            return HttpResponse("Password Not Matching")
    else:
        return HttpResponse("Fails...")


def check(request):
    if request.method == "POST":
        em = request.POST["email"]
        ps = request.POST["password"]

        data = customer.objects.filter(email=em, password=ps)
        if data:
            request.session["username"] = em
            request.session["password"] = ps
            return redirect("/dashboard")
        else:
            return HttpResponse("Fails")
    else:
        return redirect("/login")


def logout(request):
    del request.session['username']
    del request.session['password']
    return redirect('/')


# ─────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────

def dashboard(request):
    if request.session.get('username') is not None:
        user_email = request.session["username"]
        password = request.session["password"]

        data = customer.objects.filter(email=user_email, password=password)
        if data:
            customer_instance = customer.objects.get(email=user_email)
            bookings = Booking.objects.filter(user=customer_instance).order_by('-id')

            latest_booking = bookings.first()
            amount = latest_booking.amount if latest_booking else 0

            # Stats
            total_bookings = bookings.count()
            paid_bookings = bookings.filter(payment_status='paid').count()
            in_transit = bookings.filter(booking_status='in_transit').count()
            delivered = bookings.filter(booking_status='delivered').count()

            return render(request, "dashboard.html", {
                'data': data,
                'bookings': bookings,
                'amount': amount,
                'total_bookings': total_bookings,
                'paid_bookings': paid_bookings,
                'in_transit': in_transit,
                'delivered': delivered,
            })
        else:
            return HttpResponse("User Not Found")
    else:
        return redirect('/')


# ─────────────────────────────────────────────
# Distance & Amount
# ─────────────────────────────────────────────

async def _get_driving_distance(from_place: str, to_place: str):
    """
    Use Playwright to fetch driving distance (in km) from distance.to.
    Returns a float distance in km, or None if not found.
    """
    from_encoded = quote_plus(from_place)
    to_encoded = quote_plus(to_place)
    url = f"https://www.distance.to/{from_encoded}/{to_encoded}"

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="playwright_profile",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = await browser.new_page()

        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """)

        try:
            await page.goto(url, timeout=60000)
        except PlaywrightTimeoutError:
            await browser.close()
            return None

        await page.mouse.move(200, 200)
        await page.wait_for_timeout(6000)

        driving_text = None

        try:
            locator = page.locator("text=Driving route")
            await locator.first.wait_for(timeout=15000)

            elements = await locator.all()

            for el in elements:
                full = await el.text_content()
                if full and "Driving route" in full:
                    driving_text = full.strip()
                    break

        except PlaywrightTimeoutError:
            pass

        await browser.close()

        if not driving_text:
            return None

        match = re.search(r"\(([\d\.]+ km)\)", driving_text)
        if not match:
            return None

        km_value_str = match.group(1)

        try:
            return float(km_value_str.split()[0])
        except (ValueError, IndexError):
            return None


def get_driving_distance(from_place: str, to_place: str):
    try:
        loop = asyncio.get_event_loop()

        if loop.is_running():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            result = new_loop.run_until_complete(
                _get_driving_distance(from_place, to_place)
            )
            new_loop.close()
            return result
        else:
            return loop.run_until_complete(
                _get_driving_distance(from_place, to_place)
            )

    except RuntimeError:
        return asyncio.run(
            _get_driving_distance(from_place, to_place)
        )


def calculate_amount(goods_type: str, distance_km: float) -> int:
    goods_type = (goods_type or "").lower()
    rates = {
        "furniture": 40,
        "electronics": 50,
        "perishable": 60,
        "construction": 45,
        "general": 25,
    }
    rate_per_km = rates.get(goods_type, 40)
    return int(distance_km * rate_per_km)


# ─────────────────────────────────────────────
# Booking
# ─────────────────────────────────────────────

def savebook(request):
    if request.method == 'POST':
        pk = request.POST['pickup']
        de = request.POST['delivery']
        gt = request.POST['goodtype']
        vt = request.POST['vehicletype']
        pd = request.POST['date']
        dt_str = request.POST.get('distance')
        am_str = request.POST.get('amount')
        notes = request.POST.get('special_notes', '')

        user_email = request.session.get("username")
        if not user_email:
            return redirect('/login')

        customer_instance = customer.objects.get(email=user_email)

        distance_km = None
        amount = None

        if dt_str and am_str:
            try:
                distance_km = float(dt_str)
                amount = int(float(am_str))
            except ValueError:
                distance_km = None
                amount = None

        if distance_km is None or amount is None:
            distance_km = get_driving_distance(pk, de)
            if distance_km is None:
                return HttpResponse(
                    "<script>alert('Could not calculate driving distance. Please try again.');"
                    "window.location.href='/book';</script>"
                )
            amount = calculate_amount(gt, distance_km)

        data = Booking(
            pickup=pk,
            delivery=de,
            goodtype=gt,
            vehicletype=vt,
            pickupdate=pd,
            distance=round(distance_km, 2),
            amount=amount,
            user=customer_instance,
            booking_status='confirmed',
            special_notes=notes,
        )
        data.save()

        # Confirmation email
        subject = "Booking Confirmation - AgroTransport"
        message = (
            f"Dear {customer_instance.name},\n\n"
            f"Your booking has been confirmed successfully! Here are the details:\n"
            f"Booking ID: #{data.id}\n"
            f"Pickup Location: {pk}\n"
            f"Delivery Location: {de}\n"
            f"Good Type: {gt}\n"
            f"Vehicle Type: {vt}\n"
            f"Pickup Date: {pd}\n"
            f"Distance: {round(distance_km, 2)} km\n"
            f"Amount: ₹{amount}\n\n"
            f"You can track your delivery from your Dashboard.\n\n"
            f"Thank you for choosing AgroTransport!"
        )
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [user_email]
        send_mail(subject, message, from_email, recipient_list)

        return redirect('/dashboard')
    else:
        return HttpResponse("Request method not allowed.")


def calculate_distance(request):
    if request.method != 'POST':
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=405)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON data"}, status=400)

    pk = (payload.get('pickup') or "").strip()
    de = (payload.get('delivery') or "").strip()
    gt = (payload.get('goodtype') or "").strip()

    if not pk or not de:
        return JsonResponse({"success": False, "error": "Pickup and Delivery are required"}, status=400)

    distance_km = get_driving_distance(pk, de)
    if distance_km is None:
        return JsonResponse({"success": False, "error": "Could not calculate driving distance"}, status=500)

    amount = calculate_amount(gt, distance_km)

    return JsonResponse({
        "success": True,
        "distance_km": round(distance_km, 2),
        "amount": amount,
    })


# ─────────────────────────────────────────────
# DELIVERY TRACKING
# ─────────────────────────────────────────────

def track_delivery(request, booking_id):
    """Customer-facing delivery tracking page."""
    # Verify the booking belongs to logged-in user
    user_email = request.session.get("username")
    if not user_email:
        return redirect('/login')

    customer_instance = get_object_or_404(customer, email=user_email)
    booking = get_object_or_404(Booking, id=booking_id, user=customer_instance)

    return render(request, 'track_delivery.html', {'booking': booking})


def get_tracking_data(request, booking_id):
    """AJAX endpoint — returns current driver location + booking status."""
    user_email = request.session.get("username")
    if not user_email:
        return JsonResponse({'error': 'Not logged in'}, status=401)

    try:
        customer_instance = customer.objects.get(email=user_email)
        booking = Booking.objects.get(id=booking_id, user=customer_instance)
    except (customer.DoesNotExist, Booking.DoesNotExist):
        return JsonResponse({'error': 'Booking not found'}, status=404)

    data = {
        'booking_id': booking.id,
        'booking_status': booking.booking_status,
        'payment_status': booking.payment_status,
        'pickup': booking.pickup,
        'delivery': booking.delivery,
        'driver_name': booking.driver_name or '',
        'driver_phone': booking.driver_phone or '',
        'driver_lat': booking.driver_lat,
        'driver_lng': booking.driver_lng,
        'last_update': booking.last_location_update.strftime('%d-%m-%Y %H:%M') if booking.last_location_update else None,
        'estimated_delivery': booking.estimated_delivery.strftime('%d-%m-%Y') if booking.estimated_delivery else None,
    }
    return JsonResponse(data)


def update_driver_location(request, booking_id):
    """
    API endpoint for admin/driver to update live GPS location.
    POST: { lat, lng, status (optional) }
    Protected by a simple secret key header.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    # Simple auth: admin session OR secret header
    secret = request.headers.get('X-Driver-Secret', '')
    is_admin = request.session.get('is_admin_driver', False)

    if secret != 'TRANSPORT_DRIVER_2024' and not is_admin:
        # Allow if admin Django session is active
        from django.contrib.auth import get_user
        user = get_user(request)
        if not user.is_authenticated:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)

    lat = payload.get('lat')
    lng = payload.get('lng')
    status = payload.get('status')
    driver_name = payload.get('driver_name')
    driver_phone = payload.get('driver_phone')

    if lat is not None:
        booking.driver_lat = float(lat)
    if lng is not None:
        booking.driver_lng = float(lng)
    if status and status in dict(Booking.BOOKING_STATUS_CHOICES):
        booking.booking_status = status
    if driver_name:
        booking.driver_name = driver_name
    if driver_phone:
        booking.driver_phone = driver_phone

    booking.last_location_update = timezone.now()
    booking.save()

    return JsonResponse({'success': True, 'message': 'Location updated'})


def driver_tracking_page(request, booking_id, share_key):
    """
    Driver opens this page on their phone browser.
    It asks for GPS permission → auto-sends lat/lng to server every 30s.
    No app needed. Secured by unique share_key per booking.
    """
    try:
        booking = Booking.objects.get(id=booking_id, driver_share_key=share_key)
    except Booking.DoesNotExist:
        return HttpResponse(
            "<h2 style='color:red;text-align:center;margin-top:40vh;font-family:sans-serif;'>"
            "❌ Invalid or expired tracking link.</h2>"
        )
    return render(request, 'driver_tracking.html', {'booking': booking, 'share_key': share_key})


def driver_update_gps(request, booking_id, share_key):
    """
    AJAX endpoint called by driver's phone (from driver_tracking.html) every 30 seconds.
    Validates share_key and updates driver_lat, driver_lng in DB.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        booking = Booking.objects.get(id=booking_id, driver_share_key=share_key)
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Invalid link'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    lat = payload.get('lat')
    lng = payload.get('lng')

    if lat is None or lng is None:
        return JsonResponse({'error': 'lat and lng required'}, status=400)

    booking.driver_lat = float(lat)
    booking.driver_lng = float(lng)
    booking.last_location_update = timezone.now()
    # Auto set to in_transit when driver starts sharing
    if booking.booking_status == 'confirmed':
        booking.booking_status = 'in_transit'
    booking.save()

    return JsonResponse({
        'success': True,
        'lat': booking.driver_lat,
        'lng': booking.driver_lng,
    })




# ─────────────────────────────────────────────
# Payment
# ─────────────────────────────────────────────

def payment(request):
    qr_code = None
    upi_id = "9607218397@ibl"

    booking_id = request.GET.get('booking_id')
    booking = None
    amount = 0
    if booking_id:
        try:
            booking = Booking.objects.get(id=booking_id)
            amount = booking.amount
        except Booking.DoesNotExist:
            amount = request.GET.get('amount', 0)
    else:
        amount = request.GET.get('amount', 0)

    if request.method == 'POST':
        payment_mode = request.POST.get('payment_mode')

        payment_urls = {
            'google_pay': f'upi://pay?pa={upi_id}&pn=Recipient%20Name&mc=1234&am={amount}',
            'phonepe': f'upi://pay?pa={upi_id}&pn=Recipient%20Name&mc=1234&am={amount}',
            'paytm': f'upi://pay?pa={upi_id}&pn=Recipient%20Name&mc=1234&am={amount}',
        }

        payment_url = payment_urls.get(payment_mode)
        if payment_url:
            qr = qrcode.make(payment_url)
            buffer = BytesIO()
            qr.save(buffer)
            buffer.seek(0)
            image_png = buffer.getvalue()
            qr_code = base64.b64encode(image_png).decode('utf-8')
            buffer.close()

    return render(request, 'payment.html', {'qr_code': qr_code, 'amount': amount, 'booking': booking})


# ─────────────────────────────────────────────
# Profile
# ─────────────────────────────────────────────

def editprofile(request):
    x = request.GET["id"]
    data = customer.objects.filter(id=x)
    return render(request, "editprofile.html", {'data': data})


def saveeditprofile(request):
    if request.method == "POST":
        id = request.POST["id"]
        nm = request.POST["name"]
        em = request.POST["email"]
        nmb = request.POST["number"]
        add = request.POST["address"]
        ct = request.POST["city"]
        st = request.POST["state"]
        pin = request.POST["pincode"]
        ps = request.POST["password"]

        customer.objects.filter(id=id).update(
            name=nm, email=em, number=nmb, address=add,
            city=ct, state=st, pincode=pin, password=ps
        )
        return redirect("/dashboard")
    else:
        return redirect("/editprofile")


# ─────────────────────────────────────────────
# Forgot Password / OTP
# ─────────────────────────────────────────────

def forget(request):
    return render(request, "forget.html")


def send_otp(request):
    if request.method == "POST":
        email = request.POST["email"]
        user = customer.objects.filter(email=email).first()

        if user:
            otp = random.randint(100000, 999999)
            request.session['reset_email'] = email
            request.session['otp'] = otp

            subject = "Password Reset OTP - AgroTransport"
            message = f"Your OTP for password reset is: {otp}\n\nThis OTP is valid for 10 minutes."
            from_email = settings.EMAIL_HOST_USER
            send_mail(subject, message, from_email, [email])

            return HttpResponse(
                "<script>alert('OTP sent! Check your email.'); window.location.href='/verify_otp';</script>")
        else:
            return HttpResponse("<script>alert('Email not found!'); window.location.href='/forget';</script>")

    return render(request, 'forget_password.html')


def verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST["otp"]
        saved_otp = request.session.get('otp')

        if str(entered_otp) == str(saved_otp):
            request.session['otp_verified'] = True
            return redirect('/reset_password')
        else:
            return HttpResponse(
                "<script>alert('Invalid OTP! Try again.'); window.location.href='/verify_otp';</script>")

    return render(request, 'verify_otp.html')


def reset_password(request):
    if request.method == "POST":
        if not request.session.get('otp_verified'):
            return HttpResponse("<script>alert('OTP not verified!'); window.location.href='/forget';</script>")

        email = request.session.get('reset_email')
        new_password = request.POST["new_password"]

        user = customer.objects.filter(email=email).first()
        if user:
            user.password = new_password
            user.save()

            request.session.flush()

            return HttpResponse(
                "<script>alert('Password Reset Successfully! Redirecting to login...'); window.location.href='/login';</script>")
        else:
            return HttpResponse("<script>alert('User not found!'); window.location.href='/forget';</script>")

    return render(request, 'reset_password.html')
