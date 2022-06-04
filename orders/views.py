from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from carts.models import CartItem
from store.models import Product
from .forms import OrderForm
import datetime
from .models import Order, Payment, OrderProduct
import json

from django.core.mail import EmailMessage
from django.template.loader import render_to_string


# Create your views here.
def payments(request):
    body = json.loads(request.body)  # {'orderID': '2022053138', 'transID': '22T68230E3011415N', 'payment_method':
    # 'Paypal', 'status': 'COMPLETED'}
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

    # Store transaction details in payment model
    payment = Payment(
        user=request.user,
        payment_id=body['transID'],
        payment_method=body['payment_method'],
        amount_paid=order.order_total,
        status=body['status'],
    )
    payment.save()

    order.payment = payment  # Updating the 'payment' field of Order model which is a foreign key.
    order.is_ordered = True
    order.save()

    # Move the cart items to ORDER-PRODUCT table
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id  # <---- IMP : order_id = accessing autogenerated Order(Model) ID
        orderproduct.payment = payment    # ^---- IMP : order.id = accessing other model relation via Foreign Key
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id  # <---- IMP : order_id = accessing autogenerated Product(Model) ID
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        # variations is Many-to-Many field so first we have to save object and then we can access product variation
        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct_object = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct_object.variations.set(product_variation)
        orderproduct_object.save()

        # Reduce the quantity of sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Clear Cart
    CartItem.objects.filter(user=request.user).delete()

    # Send order receive to customer
    mail_subject = "Thank You for your Order"
    message = render_to_string('orders/order_received_email.html', {
        'user': request.user,
        'order': order,
    })
    to_email = request.user.email

    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    # Send order_no and transaction id back to sendData() javascript function for json response.
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    return JsonResponse(data)


def place_order(request, total=0, quantity=0):
    current_user = request.user

    # If cart count is <= 0 then redirect back to SHOPPING page
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = int((2 * total) / 100)
    grand_total = total + tax

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            # Store all data in Order Table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Generate Order Number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")  # 20210305
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            return render(request, 'orders/payments.html', context)
    else:
        return redirect('checkout')


def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        sub_total = 0
        for i in ordered_products:
            sub_total += i.product_price * i.quantity

        payment = Payment.objects.get(payment_id=transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            # 'transID': transID,  # transID using from GET request ... BAD HABIT
            'transID': payment.payment_id,  # Fetch from Database ... GOOD HABIT
            'payment': payment,
            'sub_total': sub_total,
        }

        return render(request, 'orders/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')

