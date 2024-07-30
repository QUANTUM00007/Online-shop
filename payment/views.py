from django.shortcuts import render, redirect, reverse, get_object_or_404
import stripe
from django.conf import settings
from orders.models import Order 
from decimal import Decimal
from django.http import HttpResponse
import logging

# Set up logging
logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = settings.STRIPE_API_VERSION

def payment_process(request):
    order_id = request.session.get('order_id', None)
    if not order_id:
        logger.error("Order ID not found in session.")
        return HttpResponse("Order ID not found in session.", status=400)

    try:
        order = get_object_or_404(Order, id=order_id)
    except Exception as e:
        logger.error(f"Error fetching order: {e}")
        return HttpResponse(f"Error fetching order: {e}", status=404)
    
    if request.method == 'POST':
        success_url = request.build_absolute_uri(reverse('payment:completed'))
        cancel_url = request.build_absolute_uri(reverse('payment:canceled'))
        
        session_data = {
            'mode': 'payment',
            'client_reference_id': order_id,
            'success_url': success_url,
            'cancel_url': cancel_url,
            'line_items': []
        }
        
        for item in order.items.all():
            session_data['line_items'].append({
                'price_data': {
                    'unit_amount': int(item.price * Decimal('100')),
                    'currency': 'usd',
                    'product_data': {
                        'name': item.product.name,
                    },
                },
                'quantity': item.quantity,
            })
        # stripe coupon
        if order.coupon:
            stripe_coupon = stripe.Coupon.create(
                name=order.coupon.code,
                percent_off=order.discount,
                duration='once')
        session_data['discounts'] = [{
            'coupon': stripe_coupon.id
        }]
        try:
            session = stripe.checkout.Session.create(**session_data)
            return redirect(session.url, code=303)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            return HttpResponse(f"Stripe error: {e}", status=500)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return HttpResponse(f"Unexpected error: {e}", status=500)
    else:
        return render(request, 'payment/process.html', locals())

def payment_completed(request):
    return render(request, 'payment/completed.html')

def payment_canceled(request):
    return render(request, 'payment/canceled.html')
