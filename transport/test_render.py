import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transport.settings')
django.setup()

from django.template.loader import render_to_string

class FakeCustomer:
    name = "Test"

class FakeBooking:
    id = 57
    booking_status = 'in_transit'
    pickup = 'Latur'
    delivery = 'Nanded'
    driver_lat = 18.5204
    driver_lng = 73.8567
    driver_name = 'Test Driver'
    last_location_update = None
    user = FakeCustomer()
    
html = render_to_string('track_delivery.html', {'booking': FakeBooking()})
with open('debug_output.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Done")
