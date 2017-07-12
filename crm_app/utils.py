from tixdo.crm.models import MsgReports
from django.conf import settings

from tixdo.third_party_apps import juspay as Juspay
from tixdo.booking.models import Order

Juspay.api_key = settings.JUSPAY_API_KEY


def actual_refund(unique_id, order_id_just_pay, amount):
    refund_order_id = Juspay.Orders.refund(
        unique_request_id=unique_id,
        order_id=order_id_just_pay,
        amount=amount)

    # refund_order_id = Juspay.Orders.refund(
    #     unique_request_id='9929',
    #     order_id='13059-BAY',
    #     amount=434.85)

    res = refund_order_id.__dict__
    res['refunds'] = res['refunds'][0].__dict__
    try:
        res['card'] = res['card'].__dict__
    except:
        res['card'] = {"card": "None"}
    try:
        res['payment_links'] = res['payment_links'].__dict__
    except:
        res['payment_links'] = {"payment_links": "None"}
    try:
        res['gateway_response'] = res['gateway_response'].__dict__
    except:
        res['gateway_response'] = {"gateway_response": "None"}
    return res


def refund_main(order_id):
    orddata = Order.objects.get(id=order_id)

    # ord_state = ["complete", "complete(offline)"]
    # if orddata.order_state.lower() in ord_state:
    if orddata.payment_gateway == "juspay":
        payment_id = orddata.payment_gateway_response['order_id']
        order_id_just_pay = payment_id
        unique_id = orddata.book_id
        amount = orddata.total_payment
        res = actual_refund(unique_id, order_id_just_pay, amount)
        return res
    else:
        res = {"error":"Order is complete so cannot be refunded!!"}
        return res


def create_msg91_report(data):
    msg_obj = MsgReports(request_id=data['requestId'], user_id=data['userId'], date=data['report'][0]['date'],
                         discription=data['report'][0]['desc'], number=data['report'][0]['number'],
                         sender_id=data['senderId'], campaign_name=data['campaignName'],
                         status=data['report'][0]['status'])
    msg_obj.save()
    return msg_obj


def get_date_fomatted(query):
    date_str = str(query).split("/")
    if len(date_str) > 1:
        year = date_str[2]
        day = date_str[0]
        month = date_str[1]
        print(len(month), month)
        if len(month) == 1:
            month = "0" + month
        main_date = str(day) + "-" + str(month) + "-" + str(year)
    else:
        main_date = query
    return main_date





# refund_order_id = Juspay.Orders.refund(
#     unique_request_id=unique_id,
#     order_id=order_id_just_pay,
#     amount=amount)
#
# # refund_order_id = Juspay.Orders.refund(
# #     unique_request_id='9929',
# #     order_id='13059-BAY',
# #     amount=434.85)
# res = refund_order_id.__dict__
# res['refunds'] = res['refunds'][0].__dict__
# try:
#     res['card'] = res['card'].__dict__
# except:
#     res['card'] = {"card": "None"}
# try:
#     res['payment_links'] = res['payment_links'].__dict__
# except:
#     res['payment_links'] = {"payment_links": "None"}
# try:
#     res['gateway_response'] = res['gateway_response'].__dict__
# except:
#     res['gateway_response'] = {"gateway_response": "None"}
