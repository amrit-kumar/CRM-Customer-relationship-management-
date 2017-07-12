from functools import reduce

from django.db.models import Q
from django.conf import settings
import datetime

from django.contrib.contenttypes.models import ContentType

from tixdo.cities.models import City
from tixdo.movies.models import  Movies
# Third party imports
from rest_framework import viewsets
from rest_framework import status
from rest_framework import filters
from rest_framework.decorators import list_route
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import mixins
from rest_framework.authentication import TokenAuthentication
from tixdo.organizations.models import Oragnization
from tixdo.organizations.event_partner.models import EventPartner
from tixdo.third_party_apps import juspay as Juspay
from tixdo.booking.models import Order, EventOrderDetail, EventOrderTicketType, MovieOrderDetail
from tixdo.base import error_codes
from tixdo.log.logger import logger
from tixdo.crm.filters import OrderFilter, MsgReportFilter, CouponFilter, OrganizationDataFilter, CategoryFilter, \
    OrgMemberFilter, \
    VenueFilter, EventFilter, ShowsFilter, TicketTypeFilter, SeatsFilter, DiscountFilter, MovieShowFilter, \
    MovieTheaterFilter, \
    CampaignFilter, MovieOrderFilter, EventOrderFilter, TheatreSourcesFilter
from tixdo.theatres.serializers import TheatreFilterSerializer
from tixdo.theatres.models import Theatre, TheatreSources
from tixdo.shows.models import Show
from tixdo.coupons.serializers import CouponSerializer, CouponCampaignSerializer,CouponPutPostSerializer
from tixdo.coupons.models import Campaign, Coupon
from tixdo.crm.serializers import JusPaySerializer, CrmOrderSerializer, MsgReportsSerializer, OrganizationSerializer, \
    CategorySerializer, CampaignGetSerializer,CampaignPutPostSerializer,\
    OrgMemberSerializer, VenueSerializer, EventSerializer, ShowsSerializer, TicketTypeSerializer, SeatsSerializer, \
    DiscountSerializer, FormSerializer,CampaignListSerializer, \
    EventIndexPageSerializer, OrgMemberCustomSerializer, EventCustomeSerializer, CrmOrderCustomeSerializer, \
    EventMainCustomeSerializer, CrmOrderCustomeDetailSerializer, MainOrganizationSerializer,OrderSerializer,EventOrderSerializer, CrmOrderDetailDataSerializer, \
    EventFilterSerializer, CrmMovieOrderSerializer, CrmMoviewOrderDetailDataSerializer, CrmEventOrderSerializer, CrmEventOrderDetailDataSerializer, \
    MovieSerializer, EventIdTitleSlugSerializer, CitySerializer, AccountSerializer, TheatreDefaultSerializer, ShowSerializer, \
    AccountIdNameSerializer, EventOrderDetailSerializer, TheatreSourceSerializer, CityMovieSerializer, TheatreNameSerializer
from tixdo.crm.models import MsgReports
from tixdo.booking.utils import resend_sms_function, show_cancel_sms_email
from tixdo.users.models import User
from tixdo.users.serializers import UserDefaultSerializer, UserFIlterSerializer
from tixdo.tixdo_events.event_app.models import Organization, TicketType, Category, OrgMember, Venue, Event, Shows, \
    Seats, Discount, EventIndexPage
from tixdo.bookkeeper.models import Account
from tixdo.bookkeeper.serializers import AccountSerializer
from tixdo.third_party_apps.forms.models import Form
from tixdo.crm.utils import refund_main, actual_refund
from tixdo.tixdo_events.event_app.views import all_ord, single_org_order, single_event_order, admin_org_list_func
from tixdo.tixdo_events.event_app.serializers import OrganizationSerializer
from tixdo.base.permissions import IsCrmAdmin, IsEventAdmin

from tixdo.reporting.services import export
from tixdo.base.authentication import TokenAuthenticationByUrl
from tixdo.movies.models import CityMovie

Juspay.api_key = settings.JUSPAY_API_KEY


# Custom permission class

# def charges_transactions():
#     querysets = Juspay.Orders.list(count=100)['list']
#     newqueryset = []
#     # for i in querysets:
#     #     if i.status == "CHARGED":
#     #         newqueryset.append(i)
#     return querysets

def get_single_fields_details(model_name, fielddata):
    data = {
        "name": fielddata.name,
        "type": fielddata.get_internal_type(),
        "blank": fielddata.blank,
        "choices": fielddata.choices,
        "hidden": fielddata.hidden,
        "null": fielddata.null,
        "editable": fielddata.editable,
    }
    return data


class IsAnonCreate(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_staff or request.user.is_superuser:
            return True
        else:
            return False
        return False


class ListModelMixin(object):
    """
    List a queryset.
    """

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 100


# Tixdo all orders related viewset -----------
class CrmOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This view-set contains all APIs related to a booking.
    """

    queryset = Order.objects.all()
    serializer_class = CrmOrderSerializer
    permission_classes = (IsCrmAdmin, )
    # authentication_classes = (TokenAuthentication, )

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = OrderFilter
    pagination_class = StandardResultsSetPagination

    search_fields = (
        'book_id', 'user_mobile', 'user_email', 'user__username', 'payment_id', 'event_name', 'movie_name',
        'total_payment',
        'payment_state', 'order_type', 'order_state', 'tid', 'show_time', 'show_date', 'theatre__title',
    )

    @list_route(methods=["POST"])
    def get_order_by_id(self, request):
        try:
            order_id = request.data["order_id"]
            # order_id = request.query_params.get("order_id", None)
            order = Order.objects.get(id=int(order_id))
            serializer = CrmOrderDetailDataSerializer(order)
            return Response(serializer.data)
            # return Response({"results": serializer.data})

        except KeyError as e:
            logger.error(datetime.datetime.now(), '(%s)', e)
            return Response(error_codes.HTTP_ORDER_USER_KEY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)

    @list_route(methods=["GET"])
    def get_fields_detail(self, request):
        try:
            resulst_meta = []
            model_name = request.query_params.get("model_name", None)
            ct = ContentType.objects.get(model=model_name)
            model = ct.model_class()
            all_fields = model._meta.fields
            for fieldname in all_fields:
                metadata = get_single_fields_details(model_name, fieldname)
                resulst_meta.append(metadata)
            return Response({"results":resulst_meta})

        except KeyError as e:
            logger.error(datetime.datetime.now(), '(%s)', e)
            return Response(error_codes.HTTP_ORDER_USER_KEY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)

    @list_route(methods=["GET"])
    def by_user_phone(self, request):
        try:
            phone_number = request.query_params.get("phone_number", None)
            order_list = Order.objects.filter(user_mobile=phone_number)
            if not order_list:
                return Response(error_codes.HTTP_NO_ORDER_FOUND, status=status.HTTP_404_NOT_FOUND)
            serializer = CrmOrderSerializer(order_list, many=True)

            return Response(serializer.data)

        except KeyError as e:
            logger.error(datetime.datetime.now(), '(%s)', e)
            return Response(error_codes.HTTP_ORDER_USER_KEY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)

        except Exception as e:
            return Response(error_codes.exception(e.args[0]), status=status.HTTP_403_FORBIDDEN)


    @list_route(methods=["POST"])
    def show_cancle_inform(self, request):
        try:
            # order_id = request.query_params.get("order_id", None)
            order_id = request.data["order_id"]
            order = Order.objects.get(id=int(order_id))
            if not order:
                return Response(error_codes.HTTP_NO_ORDER_FOUND, status=status.HTTP_404_NOT_FOUND)
            show_cancel_sms_email([order], "show_cancel_email", "show_cancel_sms")
            serializer = CrmOrderSerializer(order)

            return Response(serializer.data)

        except KeyError as e:
            logger.error(datetime.datetime.now(), '(%s)', e)
            return Response(error_codes.HTTP_ORDER_USER_KEY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)

        except Exception as e:
            return Response(error_codes.exception(e.args[0]), status=status.HTTP_403_FORBIDDEN)

    @list_route(methods=["GET"])
    def show_cancle_inform_all_by_show(self, request):
        try:
            show_date = request.query_params.get("show_date", None)
            show_time = request.query_params.get("show_time", None)
            orders = Order.objects.filter(show_date__icontains=show_date, show_time__icontains=show_time)
            if not orders:
                return Response(error_codes.HTTP_NO_ORDER_FOUND, status=status.HTTP_404_NOT_FOUND)
            show_cancel_sms_email(orders, "show_cancel_email", "show_cancel_sms")
            serializer = CrmOrderSerializer(orders, many=True)

            return Response(serializer.data)

        except KeyError as e:
            logger.error(datetime.datetime.now(), '(%s)', e)
            return Response(error_codes.HTTP_ORDER_USER_KEY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)

        except Exception as e:
            return Response(error_codes.exception(e.args[0]), status=status.HTTP_403_FORBIDDEN)

    @list_route(methods=["POST"])
    def refund_by_order_id(self, request):
        order_id = request.data["order_id"]

        # unique_id = request.data["unique_id"]
        # amount = request.data['amount']
        res = refund_main(order_id)
        return Response(res)

    @list_route(methods=["POST"])
    def resend_sms_email(self, request):
        order_id = request.data["order_id"]
        # unique_id = request.data["unique_id"]
        # amount = request.data['amount']
        orddata = Order.objects.filter(id=order_id)
        if orddata:
            resend_sms_function(orddata)
            message = {"success": "Sms and email sent successfull"}
        else:
            message = {"error": "Order not found"}

        return Response(message)

    @list_route(methods=["GET"])
    def get_filtered_theaters(self, request):
        query = request.query_params.get("query", None)
        theaters = Theatre.objects.filter(Q(title__icontains=query)).distinct()
        serializer = TheatreFilterSerializer(theaters, many=True)
        return Response({"results": serializer.data, "count": theaters.count()})

    @list_route(methods=["GET"])
    def get_filtered_events(self, request):
        query = request.query_params.get("query", None)
        events = Event.objects.filter(Q(title__icontains=query)).distinct()
        serializer = EventFilterSerializer(events, many=True)
        return Response({"results": serializer.data, "count": events.count()})


# Tixdo all orders related viewset -----------
class CrmMovieOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This view-set contains all APIs related to a booking.
    """

    queryset = MovieOrderDetail.objects.all().order_by('-order__modified')
    serializer_class = CrmMovieOrderSerializer
    permission_classes = (IsCrmAdmin, )
    # authentication_classes = (TokenAuthentication,)

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = MovieOrderFilter
    pagination_class = StandardResultsSetPagination

    search_fields = (
        'order__book_id', 'order__user_mobile', 'order__user_email', 'order__user__username', 'movie_name',
        'total_payment_by_user',
        'order__order_type', 'order__order_state', 'order__tid', 'show_time', 'show_date', 'theatre__title',
        'theatre__city'
    )

    @list_route(methods=["POST"])
    def get_order_by_id(self, request):
        try:
            order_id = request.data["order_id"]
            # order_id = request.query_params.get("order_id", None)
            order = MovieOrderDetail.objects.get(order__id=int(order_id))
            serializer = CrmMoviewOrderDetailDataSerializer(order)
            return Response(serializer.data)
            # return Response({"results": serializer.data})

        except KeyError as e:
            logger.error(datetime.datetime.now(), '(%s)', e)
            return Response(error_codes.HTTP_ORDER_USER_KEY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)
        except Exception as e:
            return Response(error_codes.exception(e.args[0]), status=status.HTTP_417_EXPECTATION_FAILED)

    @list_route(methods=["GET"])
    def get_fields_detail(self, request):
        try:
            resulst_meta = []
            model_name = request.query_params.get("model_name", None)
            ct = ContentType.objects.get(model=model_name)
            model = ct.model_class()
            all_fields = model._meta.fields
            for fieldname in all_fields:
                metadata = get_single_fields_details(model_name, fieldname)
                resulst_meta.append(metadata)
            return Response({"results": resulst_meta})

        except KeyError as e:
            logger.error(datetime.datetime.now(), '(%s)', e)
            return Response(error_codes.HTTP_ORDER_USER_KEY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)

    @list_route(methods=["GET"])
    def by_user_phone(self, request):
        try:
            phone_number = request.query_params.get("phone_number", None)
            order_list = Order.objects.filter(user_mobile=phone_number)
            if not order_list:
                return Response(error_codes.HTTP_NO_ORDER_FOUND, status=status.HTTP_404_NOT_FOUND)
            serializer = CrmOrderSerializer(order_list, many=True)

            return Response(serializer.data)

        except KeyError as e:
            logger.error(datetime.datetime.now(), '(%s)', e)
            return Response(error_codes.HTTP_ORDER_USER_KEY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)

        except Exception as e:
            return Response(error_codes.exception(e.args[0]), status=status.HTTP_403_FORBIDDEN)

    @list_route(methods=["POST"])
    def show_cancle_inform(self, request):
        try:
            # order_id = request.query_params.get("order_id", None)
            order_id = request.data["order_id"]
            order = Order.objects.get(id=int(order_id))
            if not order:
                return Response(error_codes.HTTP_NO_ORDER_FOUND, status=status.HTTP_404_NOT_FOUND)
            show_cancel_sms_email([order], "show_cancel_email", "show_cancel_sms")
            # serializer = CrmMovieOrderSerializer(order.movie_order)

            return Response({"success": "Sent email and sms for show cancellation to user"}, status=status.HTTP_200_OK)

        except KeyError as e:
            logger.error(datetime.datetime.now(), '(%s)', e)
            return Response(error_codes.HTTP_ORDER_USER_KEY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)

        except Exception as e:
            return Response(error_codes.exception(e.args[0]), status=status.HTTP_403_FORBIDDEN)

    @list_route(methods=["GET"])
    def show_cancle_inform_all_by_show(self, request):
        try:
            show_date = request.query_params.get("show_date", None)
            show_time = request.query_params.get("show_time", None)
            all_orders = []
            orders = MovieOrderDetail.objects.filter(show_date__icontains=show_date, show_time__icontains=show_time)
            if not orders:
                return Response(error_codes.HTTP_NO_ORDER_FOUND, status=status.HTTP_404_NOT_FOUND)
            for i in orders:
                all_orders.append(i)
            show_cancel_sms_email(all_orders, "show_cancel_email", "show_cancel_sms")
            # serializer = CrmOrderSerializer(orders, many=True)

            return Response(Response({"success": "Sent email and sms for show cancellation to users"}, status=status.HTTP_200_OK))

        except KeyError as e:
            logger.error(datetime.datetime.now(), '(%s)', e)
            return Response(error_codes.HTTP_ORDER_USER_KEY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)

        except Exception as e:
            return Response(error_codes.exception(e.args[0]), status=status.HTTP_403_FORBIDDEN)

    @list_route(methods=["POST"])
    def refund_by_order_id(self, request):
        order_id = request.data["order_id"]

        # unique_id = request.data["unique_id"]
        # amount = request.data['amount']
        res = refund_main(order_id)
        return Response(res)

    @list_route(methods=["POST"])
    def resend_sms_email(self, request):
        order_id = request.data["order_id"]
        # unique_id = request.data["unique_id"]
        # amount = request.data['amount']
        orddata = Order.objects.filter(id=order_id)
        if orddata:
            resend_sms_function(orddata)
            message = {"success": "Sms and email sent successfull"}
        else:
            message = {"error": "Order not found"}

        return Response(message)

    @list_route(methods=["GET"])
    def get_filtered_theaters(self, request):
        query = request.query_params.get("query", None)
        theaters = Theatre.objects.filter(Q(title__icontains=query)).distinct()
        serializer = TheatreFilterSerializer(theaters, many=True)
        return Response({"results": serializer.data, "count": theaters.count()})

    @list_route(methods=["GET"])
    def get_filtered_events(self, request):
        query = request.query_params.get("query", None)
        events = Event.objects.filter(Q(title__icontains=query)).distinct()
        serializer = EventFilterSerializer(events, many=True)
        return Response({"results": serializer.data, "count": events.count()})



# Tixdo all orders related viewset -----------
class CrmEventOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This view-set contains all APIs related to a booking.
    """

    queryset = EventOrderDetail.objects.all().order_by('-order__modified')
    serializer_class = CrmEventOrderSerializer
    permission_classes = (IsCrmAdmin, )
    # authentication_classes = (TokenAuthentication,)

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = EventOrderFilter
    pagination_class = StandardResultsSetPagination

    search_fields = (
        'order__book_id', 'order__user_mobile', 'order__user_email', 'order__user__username', 'event_name',
        'total_payment_by_user',
        'order__order_type', 'order__order_state', 'order__tid', 'show_time', 'show_date', 'event__title'
    )

    @list_route(methods=["POST"])
    def get_order_by_id(self, request):
        try:
            order_id = request.data["order_id"]
            # order_id = request.query_params.get("order_id", None)
            order = EventOrderDetail.objects.get(order__id=int(order_id))
            serializer = CrmEventOrderDetailDataSerializer(order)
            return Response(serializer.data)

        except KeyError as e:
            logger.error(datetime.datetime.now(), '(%s)', e)
            return Response(error_codes.HTTP_ORDER_USER_KEY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)
        except Exception as e:
            return Response(error_codes.exception(e.args[0]), status=status.HTTP_417_EXPECTATION_FAILED)

    @list_route(methods=["GET"])
    def get_fields_detail(self, request):
        try:
            resulst_meta = []
            model_name = request.query_params.get("model_name", None)
            ct = ContentType.objects.get(model=model_name)
            model = ct.model_class()
            all_fields = model._meta.fields
            for fieldname in all_fields:
                metadata = get_single_fields_details(model_name, fieldname)
                resulst_meta.append(metadata)
            return Response({"results": resulst_meta})

        except KeyError as e:
            logger.error(datetime.datetime.now(), '(%s)', e)
            return Response(error_codes.HTTP_ORDER_USER_KEY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)

    @list_route(methods=["GET"])
    def by_user_phone(self, request):
        try:
            phone_number = request.query_params.get("phone_number", None)
            order_list = Order.objects.filter(user_mobile=phone_number)
            if not order_list:
                return Response(error_codes.HTTP_NO_ORDER_FOUND, status=status.HTTP_404_NOT_FOUND)
            serializer = CrmOrderSerializer(order_list, many=True)

            return Response(serializer.data)

        except KeyError as e:
            logger.error(datetime.datetime.now(), '(%s)', e)
            return Response(error_codes.HTTP_ORDER_USER_KEY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)

        except Exception as e:
            return Response(error_codes.exception(e.args[0]), status=status.HTTP_403_FORBIDDEN)

    @list_route(methods=["POST"])
    def show_cancle_inform(self, request):
        try:
            # order_id = request.query_params.get("order_id", None)
            order_id = request.data["order_id"]
            order = Order.objects.get(id=int(order_id))
            if not order:
                return Response(error_codes.HTTP_NO_ORDER_FOUND, status=status.HTTP_404_NOT_FOUND)
            show_cancel_sms_email([order], "show_cancel_email", "show_cancel_sms")
            # serializer = CrmOrderSerializer(order)

            return Response({"success": "Sent email and sms for show cancellation to user"}, status=status.HTTP_200_OK)

        except KeyError as e:
            logger.error(datetime.datetime.now(), '(%s)', e)
            return Response(error_codes.HTTP_ORDER_USER_KEY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)

        except Exception as e:
            return Response(error_codes.exception(e.args[0]), status=status.HTTP_403_FORBIDDEN)

    @list_route(methods=["GET"])
    def show_cancle_inform_all_by_show(self, request):
        try:
            show_date = request.query_params.get("show_date", None)
            show_time = request.query_params.get("show_time", None)
            orders = Order.objects.filter(show_date__icontains=show_date, show_time__icontains=show_time)
            if not orders:
                return Response(error_codes.HTTP_NO_ORDER_FOUND, status=status.HTTP_404_NOT_FOUND)
            show_cancel_sms_email(orders, "show_cancel_email", "show_cancel_sms")
            # serializer = CrmOrderSerializer(orders, many=True)

            return Response({"success": "Sent email and sms for show cancellation to user"}, status=status.HTTP_200_OK)

        except KeyError as e:
            logger.error(datetime.datetime.now(), '(%s)', e)
            return Response(error_codes.HTTP_ORDER_USER_KEY_ERROR, status=status.HTTP_406_NOT_ACCEPTABLE)

        except Exception as e:
            return Response(error_codes.exception(e.args[0]), status=status.HTTP_403_FORBIDDEN)

    @list_route(methods=["POST"])
    def refund_by_order_id(self, request):
        order_id = request.data["order_id"]

        # unique_id = request.data["unique_id"]
        # amount = request.data['amount']
        res = refund_main(order_id)
        return Response(res)

    @list_route(methods=["POST"])
    def resend_sms_email(self, request):
        order_id = request.data["order_id"]
        # unique_id = request.data["unique_id"]
        # amount = request.data['amount']
        orddata = Order.objects.filter(id=order_id)
        if orddata:
            resend_sms_function(orddata)
            message = {"success": "Sms and email sent successfull"}
        else:
            message = {"error": "Order not found"}

        return Response(message)

    @list_route(methods=["GET"])
    def get_filtered_theaters(self, request):
        query = request.query_params.get("query", None)
        theaters = Theatre.objects.filter(Q(title__icontains=query)).distinct()
        serializer = TheatreFilterSerializer(theaters, many=True)
        return Response({"results": serializer.data, "count": theaters.count()})

    @list_route(methods=["GET"])
    def get_filtered_events(self, request):
        query = request.query_params.get("query", None)
        events = Event.objects.filter(Q(title__icontains=query)).distinct()
        serializer = EventFilterSerializer(events, many=True)
        return Response({"results": serializer.data, "count": events.count()})

    @list_route(methods=["POST"])
    def showdate_by_event(self, request):
        try:
            event_id = request.data["event_id"]
            eventorderdetail = EventOrderDetail.objects.filter(event=event_id)
            serializer = EventOrderDetailSerializer(eventorderdetail, many=True)
            context = serializer.data
            return Response(context, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(error_codes.exception(e.args[0]), status=status.HTTP_417_EXPECTATION_FAILED)


# Juspay transaction related viewset --------------
class JusPayViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    A simple ViewSet for listing or retrieving users.
    """

    # queryset = Juspay.Orders.list(count=100)['list']
    serializer_class = JusPaySerializer
    permission_classes = (IsCrmAdmin,)
    # authentication_classes = (TokenAuthentication,)
    pagination_class = StandardResultsSetPagination

    # ----- Search fields not applicable -------
    # search_fields = (
    #     'order_id', 'merchant_id', 'amount', 'status', 'status_id', 'amount_refunded', 'refunded',
    #     'currency',
    # )

    def get_queryset(self):
        """
        This view should return a list of all the purchases
        for the currently authenticated user.
        """
        return Juspay.Orders.list(count=10)['list']

    @list_route(methods=["GET"])
    def by_order_id(self, request):
        context = {"count": 0, "next": None, "previous": None, "results": []}
        order_id_just_pay = request.query_params.get("order_id", None)
        if(len(order_id_just_pay.split("@")) >= 2):
            orders = Order.objects.filter(user_email=order_id_just_pay)
            if orders:
                transactions = []
                for ord in orders:
                    try:
                        order_id = Juspay.Orders.status(order_id=ord.payment_id)
                        transactions.append(order_id)
                    except:
                        pass
                if transactions:
                    serializer = JusPaySerializer(transactions, many=True)
                    data = serializer.data
                else:
                    data = {"message": "No transaction found "}
            else:
                data = {"message": "No transaction found "}
        elif (len(order_id_just_pay.split("-")) >= 2) or (len(order_id_just_pay.split("_")) >= 2):
            try:
                order_id = Juspay.Orders.status(order_id=order_id_just_pay)
                serializer = JusPaySerializer
                data = [serializer(order_id).data]
            except:
                data = {"message": "Enter valid payment id"}
        else:
            orders = Order.objects.filter(user_mobile=order_id_just_pay)
            if orders:
                transactions = []
                for ord in orders:
                    try:
                        order_id = Juspay.Orders.status(order_id=ord.payment_id)
                        transactions.append(order_id)
                    except:
                        pass
                if transactions:
                    serializer = JusPaySerializer(transactions, many=True)
                    data = serializer.data
                else:
                    data = {"message": "No transaction found "}
            else:
                return Response(context,status=status.HTTP_200_OK)
        return Response(data)

    @list_route(methods=["POST"])
    def refund_by_order_id(self, request):
        try:
            order_id_just_pay = request.data["order_id"]
            unique_id = request.data["unique_id"]
            amount = request.data['amount']
            res = actual_refund(unique_id, order_id_just_pay, amount)

            return Response({"success":'Refund has been initiated'})
        except Exception :
            return Response({"error_code": 9203,
                             "error_desc": "OOPS!! looks like invalid request. For details Contact Us"
                            },
            status=status.HTTP_417_EXPECTATION_FAILED)

# Theater related viewset -------------------
class TheatersViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving Theatre's.
    """

    queryset = Theatre.objects.all()
    serializer_class = TheatreDefaultSerializer
    # permission_classes = (IsAnonCreate,)
    permission_classes = (IsCrmAdmin,)
    # authentication_classes = (TokenAuthentication,)
    pagination_class = StandardResultsSetPagination
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = MovieTheaterFilter

    search_fields = (
        'id', 'title', 'booking_amount', 'city', 'movie_partner__title', 'movie_partner__parent__oragnization__legal_name','status'
    )

    @list_route(methods=["POST"])
    def disable_theatre(self, request):
        try:
            theatre_id = request.data["theatre_id"]
            theatre = Theatre.objects.get(id=theatre_id)
            theatre.status = "closed"
            theatre.save()
            serializer = TheatreDefaultSerializer(theatre)
            context = {"results": serializer.data}
            return Response(context, status=status.HTTP_200_OK)
            # return Response( context,{"success":'disabled'})
        except Exception as e:
            return Response( error_codes.exception(e.args[0]),status=status.HTTP_417_EXPECTATION_FAILED)



    @list_route(methods=["POST"])
    def enable_theatre(self, request):
        try:
            theatre_id = request.data["theatre_id"]
            theatre = Theatre.objects.get(id=theatre_id)
            theatre.status = "open"
            theatre.save()
            serializer = TheatreDefaultSerializer(theatre)
            context = {"results": serializer.data}
            return Response(context, status=status.HTTP_200_OK)
            # return Response(context,{ "success":'enabled'})
        except Exception as e:
            return Response( error_codes.exception(e.args[0]),status=status.HTTP_417_EXPECTATION_FAILED)

    @list_route(methods=["GET"])
    def get_filtered_cities(self, request):
        query = request.query_params.get("query", None)
        cities = City.objects.filter(Q(name__icontains=query)).distinct()
        serializer = CitySerializer(cities, many=True)
        return Response({"results": serializer.data, "count": cities.count()})

    @list_route(methods=["GET"])
    def get_filtered_theatres(self, request):
        query = request.query_params.get("query", None)
        theatres = Theatre.objects.filter(Q(title__icontains=query)).distinct()
        serializer = TheatreDefaultSerializer(theatres, many=True)
        return Response({"results": serializer.data, "count": theatres.count()})


# Show related viewset --------------
class ShowsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving Shows.
    """

    queryset = Show.objects.filter(date__gte=datetime.datetime.utcnow().date())
    # queryset = Show.objects.all()
    serializer_class = ShowSerializer
    permission_classes = (IsCrmAdmin,)
    # authentication_classes = (TokenAuthentication,)
    pagination_class = StandardResultsSetPagination
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = MovieShowFilter

    search_fields = (
        'id', 'movie__title', 'movie_detail', 'dimension', 'language', 'theatre_detail', 'price', 'date', 'start',
        'end',
        'theatre__title','enabled', 'theatre__city'
    )

    @list_route(methods=["POST"])
    def disable_show(self, request):
        try:
            show_id = request.data["show_id"]
            show = Show.objects.get(id=show_id)
            show.enabled = False
            show.save()
            serializer = ShowSerializer(show)
            context = {"results": serializer.data}
            return Response(context, status=status.HTTP_200_OK)
            # return Response(context, {"success":'disabled'})

        except Exception as e:
            return Response( error_codes.exception(e.args[0]), status=status.HTTP_417_EXPECTATION_FAILED)

    @list_route(methods=["POST"])
    def enable_show(self, request):
        try:
            show_id = request.data["show_id"]
            show = Show.objects.get(id=show_id)
            show.enabled = True
            show.save()
            serializer = ShowSerializer(show)
            context = {"results": serializer.data}
            return Response(context, status=status.HTTP_200_OK)
            # return Response(context,{"success": 'enabled'})

        except Exception as e:
            return Response( error_codes.exception(e.args[0]), status=status.HTTP_417_EXPECTATION_FAILED)


    @list_route(methods=["GET"])
    def get_filtered_cities(self, request):
        query = request.query_params.get("query", None)
        cities = City.objects.filter(Q(name__icontains=query)).distinct()
        serializer = CitySerializer(cities, many=True)
        return Response({"results": serializer.data, "count": cities.count()})

    @list_route(methods=["GET"])
    def get_filtered_moviename(self, request):
        query = request.query_params.get("query", None)
        citiemovies = CityMovie.objects.filter(Q(movie__title__icontains=query)).distinct()
        serializer = CityMovieSerializer(citiemovies, many=True)
        return Response({"results": serializer.data, "count": citiemovies.count()})

    @list_route(methods=["GET"])
    def get_filtered_theatre(self, request):
        query = request.query_params.get("query", None)
        city = request.query_params.get("city", None)
        if city:
            theatres = Theatre.objects.filter(Q(title__icontains=query) & Q(city__icontains=city)).distinct()
        else:
            theatres = Theatre.objects.filter(Q(title__icontains=query)).distinct()
        serializer = TheatreNameSerializer(theatres, many=True)
        return Response({"results": serializer.data, "count": theatres.count()})

    @list_route(methods=["GET"])
    def get_filtered_show_dates(self, request):
        query = request.query_params.get("query", None)
        date_str = str(query).split("/")
        if len(date_str)>1:
            year = date_str[2]
            month = date_str[1]
            day = date_str[0]
            main_date = str(year) + "-" + str(month) + "-" + str(day)
        else:
            main_date = query
        show_dates = Show.objects.filter(Q(date__icontains=main_date)).values_list('date').distinct().order_by()
        show_times = Show.objects.filter(Q(date__icontains=main_date)).values('start').distinct().order_by()
        context = {"show_dates":show_dates, "show_times":show_times}
        return Response({"results": context})



# Campaign related viewset ----------------
class CampaignDataViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for listing or retrieving Shows.
    """

    queryset = Campaign.objects.all().order_by('-modified')

    # permission_classes = (IsAnonCreate,)
    permission_classes = (IsCrmAdmin,)
    # authentication_classes = (TokenAuthentication,)
    pagination_class = StandardResultsSetPagination
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = CampaignFilter

    search_fields = (
        'id', 'name', 'description', 'value', 'campaign_type', 'type', 'discount_type', 'movie__title', 'event__title',
        'city__name',
        'theatre__title'
    )

    def get_serializer_class(self):
        if self.action =='list':
            return CampaignListSerializer
        elif self.action =='retrieve':
            return CampaignGetSerializer
        else:
            return CampaignPutPostSerializer


    @list_route(methods=["POST"])
    def delete_multiple(self, request):
        campaign_ids = request.data["campaign_ids"]
        # campaign_ids = request.query_params.get("campaign_ids", None)
        campaign_ids = list(campaign_ids)
        try:
            camp = Campaign.objects.filter(id__in=campaign_ids).delete()
        except Exception as e:
            return Response({"error": e}, status=status.HTTP_417_EXPECTATION_FAILED)
        return Response({"success": "Campaigns deleted successfully"}, status=status.HTTP_200_OK)

    @list_route(methods=["GET"])
    def get_filtered_movie(self, request):
        query = request.query_params.get("query", None)
        from tixdo.movies.models import Movies
        movies = Movies.objects.filter(Q(title__icontains=query) |
                                    Q(movie_code__icontains=query) |
                                    Q(status__icontains=query)).distinct()
        serializer = MovieSerializer(movies, many=True)
        return Response({"results": serializer.data, "count": movies.count()})

    @list_route(methods=["GET"])
    def get_filtered_event(self, request):
        query = request.query_params.get("query", None)
        events = Event.objects.filter(Q(title__icontains=query)).distinct()
        serializer = EventIdTitleSlugSerializer(events, many=True)
        return Response({"results": serializer.data, "count": events.count()})

    @list_route(methods=["GET"])
    def get_filtered_city(self, request):
        query = request.query_params.get("query", None)
        from tixdo.cities.models import City
        cities = City.objects.filter(Q(name__icontains=query) |
                                       Q(code__icontains=query)).distinct()
        serializer = CitySerializer(cities, many=True)
        return Response({"results": serializer.data, "count": cities.count()})

    @list_route(methods=["GET"])
    def get_filtered_theatre_chain(self, request):
        # query = request.query_params.get("query", None)
        from tixdo.bookkeeper.models import Account
        # accounts = Account.objects.filter(Q(name__icontains=query) |
        #                                   Q(contact_no__icontains=query) |
        #                                   Q(contact_person__icontains=query) |
        #                                   Q(legal_name__icontains=query)).distinct()
        accounts=Account.objects.all()
        serializer = AccountIdNameSerializer(accounts, many=True)
        return Response({"results": serializer.data, "count": accounts.count()})

    @list_route(methods=["GET"])
    def get_filtered_theaters(self, request):
        query = request.query_params.get("query", None)
        theaters = Theatre.objects.filter(Q(title__icontains=query)).distinct()
        serializer = TheatreFilterSerializer(theaters, many=True)
        return Response({"results": serializer.data, "count": theaters.count()})


    @list_route(methods=["GET"])
    def get_campaign_type(self, request):

        my_field = Campaign._meta.get_field('campaign_type')
        list=[]
        for k,v in my_field.choices._display_map.items():

            dict={}
            dict.update({"key":k})
            dict.update({"value":v})
            list.append(dict)

        return Response(list)


    @list_route(methods=["GET"])
    def get_coupon_type(self, request):

        my_field = Campaign._meta.get_field('type')
        list=[]
        for k,v in my_field.choices._display_map.items():

            dict={}
            dict.update({"key":k})
            dict.update({"value":v})
            list.append(dict)

        return Response(list)

    @list_route(methods=["GET"])
    def get_discount_type(self, request):

        my_field = Campaign._meta.get_field('discount_type')
        list=[]
        for k,v in my_field.choices._display_map.items():

            dict={}
            dict.update({"key":k})
            dict.update({"value":v})
            list.append(dict)

        return Response(list)


# Coupon related viewset ------------
class CouponDataViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for listing or retrieving Shows.
    """
    queryset = Coupon.objects.all().order_by('-modified')
    # permission_classes = (IsAnonCreate,)
    permission_classes = (IsCrmAdmin,)
    # authentication_classes = (TokenAuthentication,)
    pagination_class = StandardResultsSetPagination
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = CouponFilter
    search_fields = (
        'id', 'code', 'user_limit', 'valid_until', 'minimum_amount', 'min_buy_ticket', 'get_free_ticket', 'usage_limit',
        'time_span',
        'usage_limit', 'campaign__name'
    )

    def get_serializer_class(self):


        if self.action in ['list','retrieve','get',]:
            return CouponSerializer
        else:
            return CouponPutPostSerializer


    @list_route(methods=["POST"])
    def delete_multiple(self, request):
        coupon_ids = request.data["coupon_ids"]
        # campaign_ids = request.query_params.get("campaign_ids", None)
        coupon_ids = list(coupon_ids)
        try:
            camp = Coupon.objects.filter(id__in=coupon_ids).delete()
        except Exception as e:
            return Response({"error": e}, status=status.HTTP_417_EXPECTATION_FAILED)
        return Response({"success": "Coupons deleted successfully"}, status=status.HTTP_200_OK)

    @list_route(methods=["GET"])
    def get_filtered_users(self, request):
        query = request.query_params.get("query", None)
        users = User.objects.filter( Q(email__icontains=query) |
                                     Q(phone__icontains=query) ).distinct()[:30]
        serializer = UserFIlterSerializer(users, many=True)
        return Response({"results": serializer.data, "count": users.count()})

    @list_route(methods=["GET"])
    def get_filtered_campaigns(self, request):
        query = request.query_params.get("query", None)
        campaigns = Campaign.objects.filter(Q(name__icontains=query) |
                                            Q(description__icontains=query) |
                                            Q(city__name__icontains=query) |
                                            Q(event__title__icontains=query) |
                                            Q(movie__title__icontains=query)).distinct()
        serializer = CouponCampaignSerializer(campaigns, many=True)
        return Response({"results": serializer.data, "count": campaigns.count()})


# Msg91 related viewset -----------
class MsgReportViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    A simple ViewSet for listing or retrieving Shows.
    """

    queryset = MsgReports.objects.all()
    serializer_class = MsgReportsSerializer
    # permission_classes = (IsAnonCreate,)
    permission_classes = (IsCrmAdmin,)
    # authentication_classes = (TokenAuthentication,)
    pagination_class = StandardResultsSetPagination

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = MsgReportFilter
    search_fields = (
        'request_id', 'date', 'discription', 'number', 'status',
    )


# Organization related viewset -----------
class OrganizationViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for listing or retrieving Shows.
    """

    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    # permission_classes = (IsAnonCreate,)
    authentication_classes = (TokenAuthentication,)
    pagination_class = StandardResultsSetPagination

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = OrganizationDataFilter

    # search_fields = (
    #     'request_id', 'date', 'discription', 'number', 'status',
    # )


    @list_route(methods=["GET"])
    def get_filtered_users(self, request):
        query = request.query_params.get("query", None)
        users = User.objects.filter(Q(username__icontains=query) |
                                    Q(first_name__icontains=query) |
                                    Q(last_name__icontains=query)).distinct()
        serializer = UserDefaultSerializer(users, many=True)
        return Response({"results": serializer.data, "count": users.count()})

    @list_route(methods=["GET"])
    def get_filtered_accounts(self, request):
        query = request.query_params.get("query", None)
        accounts = Account.objects.filter(Q(name__icontains=query) |
                                          Q(legal_name__icontains=query) |
                                          Q(contact_no__icontains=query)).distinct()
        serializer = AccountSerializer(accounts, many=True)
        return Response({"results": serializer.data, "count": accounts.count()})


# Category related viewset -----------
class CategoryViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for listing or retrieving Shows.
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # permission_classes = (IsAnonCreate,)
    authentication_classes = (TokenAuthentication,)
    pagination_class = StandardResultsSetPagination

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = CategoryFilter
    # search_fields = (
    #     'request_id', 'date', 'discription', 'number', 'status',
    # )


# OrgMember related viewset -----------
class OrgMemberViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for listing or retrieving Shows.
    """

    queryset = OrgMember.objects.all()
    serializer_class = OrgMemberSerializer
    # permission_classes = (IsAnonCreate,)
    authentication_classes = (TokenAuthentication,)
    pagination_class = StandardResultsSetPagination

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = OrgMemberFilter

    # search_fields = (
    #     'request_id', 'date', 'discription', 'number', 'status',
    # )

    @list_route(methods=["GET"])
    def get_filtered_members(self, request):
        query = request.query_params.get("query", None)
        users = User.objects.filter(Q(username__icontains=query) |
                                    Q(first_name__icontains=query) |
                                    Q(last_name__icontains=query)).distinct()
        serializer = UserDefaultSerializer(users, many=True)
        return Response({"results": serializer.data, "count": users.count()})

    @list_route(methods=["GET"])
    def get_filtered_organizations(self, request):
        query = request.query_params.get("query", None)
        organizations = Organization.objects.filter(Q(title__icontains=query)).distinct()
        serializer = OrganizationSerializer(organizations, many=True)
        return Response({"results": serializer.data, "count": organizations.count()})


# Venue related viewset -----------
class VenueViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for listing or retrieving Shows.
    """

    queryset = Venue.objects.all()
    serializer_class = VenueSerializer
    # permission_classes = (IsAnonCreate,)
    authentication_classes = (TokenAuthentication,)
    pagination_class = StandardResultsSetPagination

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = VenueFilter
    # search_fields = (
    #     'request_id', 'date', 'discription', 'number', 'status',
    # )


# Event related viewset -----------
class EventViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for listing or retrieving Shows.
    """

    queryset = Event.objects.all()
    serializer_class = EventSerializer
    # permission_classes = (IsAnonCreate,)
    authentication_classes = (TokenAuthentication,)
    pagination_class = StandardResultsSetPagination

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = EventFilter

    # search_fields = (
    #     'request_id', 'date', 'discription', 'number', 'status',
    # )

    @list_route(methods=["GET"])
    def get_filtered_organizers(self, request):
        query = request.query_params.get("query", None)
        organizations = Organization.objects.filter(Q(title__icontains=query)).distinct()
        serializer = OrganizationSerializer(organizations, many=True)
        return Response({"results": serializer.data, "count": organizations.count()})

    @list_route(methods=["GET"])
    def get_filtered_attendies(self, request):
        query = request.query_params.get("query", None)
        users = User.objects.filter(Q(username__icontains=query) |
                                    Q(first_name__icontains=query) |
                                    Q(last_name__icontains=query)).distinct()
        serializer = UserDefaultSerializer(users, many=True)
        return Response({"results": serializer.data, "count": users.count()})

    @list_route(methods=["GET"])
    def get_filtered_categories(self, request):
        query = request.query_params.get("query", None)
        categories = Category.objects.filter(Q(title__icontains=query)).distinct()
        serializer = CategorySerializer(categories, many=True)
        return Response({"results": serializer.data, "count": categories.count()})

    @list_route(methods=["GET"])
    def get_filtered_forms(self, request):
        query = request.query_params.get("query", None)
        categories = Form.objects.filter(Q(title__icontains=query)).distinct()
        serializer = FormSerializer(categories, many=True)
        return Response({"results": serializer.data, "count": categories.count()})

    @list_route(methods=["GET"])
    def get_filtered_showonpage(self, request):
        query = request.query_params.get("query", None)
        objects = EventIndexPage.objects.filter(Q(title__icontains=query)).distinct()
        serializer = EventIndexPageSerializer(objects, many=True)
        return Response({"results": serializer.data, "count": objects.count()})


# Shows related viewset -----------
class EventShowsViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for listing or retrieving Shows.
    """

    queryset = Shows.objects.all()
    serializer_class = ShowsSerializer
    # permission_classes = (IsAnonCreate,)
    authentication_classes = (TokenAuthentication,)
    pagination_class = StandardResultsSetPagination
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = ShowsFilter

    # search_fields = (
    #     'request_id', 'date', 'discription', 'number', 'status',
    # )

    @list_route(methods=["GET"])
    def get_filtered_events(self, request):
        query = request.query_params.get("query", None)
        events = Event.objects.filter(Q(title__icontains=query)).distinct()
        serializer = EventSerializer(events, many=True)
        return Response({"results": serializer.data, "count": events.count()})

    @list_route(methods=["GET"])
    def get_filtered_venues(self, request):
        query = request.query_params.get("query", None)
        venues = Venue.objects.filter(Q(title__icontains=query)).distinct()
        serializer = VenueSerializer(venues, many=True)
        return Response({"results": serializer.data, "count": venues.count()})


# TicketType related viewset -----------
class TicketTypeViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for listing or retrieving Shows.
    """

    queryset = TicketType.objects.all()
    serializer_class = TicketTypeSerializer
    # permission_classes = (IsAnonCreate,)
    authentication_classes = (TokenAuthentication,)
    pagination_class = StandardResultsSetPagination
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = TicketTypeFilter

    # search_fields = (
    #     'request_id', 'date', 'discription', 'number', 'status',
    # )

    @list_route(methods=["GET"])
    def get_filtered_sows(self, request):
        query = request.query_params.get("query", None)
        eventshows = Shows.objects.filter(Q(title__icontains=query)).distinct()
        serializer = ShowsSerializer(eventshows, many=True)
        return Response({"results": serializer.data, "count": eventshows.count()})


# Seats related viewset -----------
class SeatsViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for listing or retrieving Shows.
    """

    queryset = Seats.objects.all()
    serializer_class = SeatsSerializer
    # permission_classes = (IsAnonCreate,)
    authentication_classes = (TokenAuthentication,)
    pagination_class = StandardResultsSetPagination
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = SeatsFilter

    # search_fields = (
    #     'request_id', 'date', 'discription', 'number', 'status',
    # )

    @list_route(methods=["GET"])
    def get_filtered_tickettypes(self, request):
        query = request.query_params.get("query", None)
        tickettypes = TicketType.objects.filter(Q(title__icontains=query)).distinct()
        serializer = TicketTypeSerializer(tickettypes, many=True)
        return Response({"results": serializer.data, "count": tickettypes.count()})


# Discount related viewset -----------
class DiscountViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for listing or retrieving Shows.
    """

    queryset = Discount.objects.all()
    serializer_class = DiscountSerializer
    # permission_classes = (IsAnonCreate,)
    authentication_classes = (TokenAuthentication,)
    pagination_class = StandardResultsSetPagination
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = DiscountFilter

    # search_fields = (
    #     'request_id', 'date', 'discription', 'number', 'status',
    # )

    @list_route(methods=["GET"])
    def get_filtered_tickettypes(self, request):
        query = request.query_params.get("query", None)
        tickettypes = TicketType.objects.filter(Q(title__icontains=query)).distinct()
        serializer = TicketTypeSerializer(tickettypes, many=True)
        return Response({"results": serializer.data, "count": tickettypes.count()})


# # Coupon related viewset ------------
# class CouponNestedViewSet(viewsets.ViewSet):
#     """
#     A simple ViewSet for listing or retrieving Shows.
#     """
#     model = Coupon
#
#     def list(self, request, nested_1_pk=None):
#         camp = Campaign.objects.get(pk=nested_1_pk)
#         coups = Coupon.objects.filter(campaign=camp)
#         serializer = CouponSerializer(coups, many=True)
#         return Response(serializer.data)
#
#     # queryset = Coupon.objects.all()
#     # serializer_class = CouponSerializer
#     # permission_classes = (IsAnonCreate,)
#     # pagination_class = StandardResultsSetPagination
#     # filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
#     # filter_class = CouponFilter
#     # search_fields = (
#     #     'id', 'code', 'user_limit', 'valid_until', 'minimum_amount', 'min_buy_ticket', 'get_free_ticket', 'usage_limit',
#     #     'time_span',
#     #     'usage_limit', 'campaign__name', 'multi_user'
#     # )


# Organization Dashboard related:----0----------


# Organization dashboard related viewset -----------
class OrganizationDashboardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving Shows.
    """

    # queryset = Discount.objects.all()
    serializer_class = OrgMemberCustomSerializer
    # authentication_classes = (TokenAuthentication, TokenAuthenticationByUrl)
    pagination_class = StandardResultsSetPagination
    permission_classes = (IsEventAdmin,)
    detail_serializer = CrmOrderSerializer()
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    # filter_class = DiscountFilter

    def get_queryset(self):
        """
        This view should return a list of all the purchases
        for the currently authenticated user.
        """
        all_orddata = all_ord(self.request.user)
        organizations = all_orddata["org"]
        return organizations

    @list_route(methods=["GET"])
    def main(self, request):
        all_orddata = all_ord(self.request.user)
        organizations = all_orddata["org"]
        organization_ser = OrgMemberCustomSerializer(organizations, many=True)
        events_data = all_orddata["events_data"]
        events_data_ser = EventCustomeSerializer(events_data, many=True)
        context = {"organization": organization_ser.data, "events_data": events_data_ser.data}
        return Response(context)

    @list_route(methods=['GET'])
    def get_events_by_org_id(self, request):
        '''

        :param request:
        :return:
        get events by organization id
        '''
        id = request.query_params.get("id", None)
        org = Oragnization.objects.get(id=id)
        organization_ser = MainOrganizationSerializer(org)
        event_partner = EventPartner.objects.get(oragnization=org)
        events = Event.objects.filter(event_partner=event_partner)
        events_data_ser=EventCustomeSerializer(events,many=True)
        context = {"organization": organization_ser.data, "events_data": events_data_ser.data}
        return Response(context)

    @list_route(methods=['GET'])
    def get_events_by_org(self,request):
        '''

        :param request:
        :return:
        get events and orders by organization id
        '''
        id=request.query_params.get("id", None)
        org=Oragnization.objects.get(id=id)
        organization_ser = MainOrganizationSerializer(org)
        event_partner = EventPartner.objects.get(oragnization=org)
        events = Event.objects.filter(event_partner=event_partner)
        if events.count() > 1:
            events_data_ser=EventSerializer(events,many=True)
            context = {"organization": organization_ser.data, "events_data": events_data_ser.data}

        elif events.count() == 1:
            events_data_ser=EventOrderSerializer(events,many=True)
            order=Order.objects.filter(event=events[0])
            order_data_ser = OrderSerializer(order, many=True)
            context = {"organization": organization_ser.data, "events_data": events_data_ser.data[0],"orders_data": order_data_ser.data}

        else:
            events_data_ser=[]
            context = {"organization": organization_ser.data, "events_data": events_data_ser}

        return Response(context)

    @list_route(methods=['GET'])
    def get_orders_by_event(self,request):
        '''

        :param request:
        :return:
        get event orders by event id
        '''
        id = request.query_params.get("id", None)
        event=Event.objects.get(id=id)
        events_data_ser=EventSerializer(event)
        order=Order.objects.filter(event=event)
        order_data_ser=OrderSerializer(order,many=True)
        context = {"events_data": events_data_ser.data, "orders_data": order_data_ser.data}
        return Response(context)

    @list_route(methods=["GET"])
    def get_event_by_slug(self, request):
        slug = request.query_params.get("slug", None)
        org_obj = Organization.objects.get(slug=slug)
        all_orddata = single_org_order(org_obj)
        organization_ser = OrganizationSerializer(org_obj)
        events_data = all_orddata["events_data"]
        events_data_ser = EventCustomeSerializer(events_data, many=True)
        context = {"organization": organization_ser.data, "events_data": events_data_ser.data}
        return Response(context)

    @list_route(methods=["GET"])
    def get_eventorders_by_event(self, request):
        event_id = request.query_params.get("event_id", None)
        date = request.GET.get('date', None)
        time = request.GET.get('time', None)
        date_str = str(date).split("/")
        if len(date_str) > 1:
            year = date_str[2]
            day = date_str[0]
            month = date_str[1]
            if len(month) == 1:
                month = "0" + month
            main_date = str(day) + "-" + str(month) + "-" + str(year)
        else:
            main_date = date
        event_obj = Event.objects.get(id=int(event_id))
        event_obj_serb = EventSerializer(event_obj)
        all_orddata = single_event_order(event_obj, date=main_date, time=time)
        all_orders = all_orddata["all_ord"]
        all_orders_ser = CrmOrderCustomeSerializer(all_orders, many=True)
        total_price = all_orddata["total_price"]
        total_discounted_price = all_orddata["total_discounted_price"]
        context = {"event_obj": event_obj_serb.data, "all_orders": all_orders_ser.data, "total_price": total_price,
                   "total_discounted_price": total_discounted_price}
        return Response(context)

    @list_route(methods=["GET"])
    def export_excel_org(self, request):
        event_id = request.query_params.get("event_id", None)
        date = request.GET.get('date', None)
        time = request.GET.get('time', None)
        event_obj = Event.objects.get(id=int(event_id))
        event_obj_serb = EventSerializer(event_obj)
        all_orddata = single_event_order(event_obj, date=date, time=time)
        all_orders = all_orddata["all_ord"]
        all_orders_ser = CrmOrderCustomeSerializer(all_orders, many=True)
        total_price = all_orddata["total_price"]
        total_discounted_price = all_orddata["total_discounted_price"]
        context = {"event_obj": event_obj_serb.data, "total_price": total_price,
                   "total_discounted_price": total_discounted_price}
        response = export(queryset=all_orders_ser.data, filename='Dashboard Orders', context=context)
        return response

    @list_route(methods=["GET"])
    def export_excel_org_detail(self, request):
        event_id = request.query_params.get("event_id", None)
        date = request.GET.get('date', None)
        time = request.GET.get('time', None)
        event_ord_tt = []
        event_obj = Event.objects.get(id=int(event_id))
        event_obj_serb = EventSerializer(event_obj)
        all_orddata = single_event_order(event_obj, date=date, time=time)
        all_orders = all_orddata["all_ord"]
        for ordd in all_orders:
            eventorderdetaildata = ordd.event_order
            eventorderticketyypesdata = EventOrderTicketType.objects.filter(eventorderdetail=eventorderdetaildata)
            for evtt in eventorderticketyypesdata:
                event_ord_tt.append(evtt)
        all_orders_ser = CrmOrderCustomeDetailSerializer(event_ord_tt, many=True)
        total_price = all_orddata["total_price"]
        total_discounted_price = all_orddata["total_discounted_price"]
        context = {"event_obj": event_obj_serb.data, "total_price": total_price,
                   "total_discounted_price": total_discounted_price}
        response = export(queryset=all_orders_ser.data, filename='Dashboard Detail Orders', context=context)
        return response

    # ---------- http://192.168.21.179:8000/api/admin-organizations-list/tvk-cultural-academy/ ----------- data
    @list_route(methods=["GET"])
    def organizationsdata(self, request):
        slug = request.query_params.get("org_name", None)
        context = admin_org_list_func(slug)
        orga = context['organization']
        org_ser = OrganizationSerializer(orga)
        events = context['events']
        events_ser = EventMainCustomeSerializer(events, many=True)
        context['organization'] = org_ser.data
        context['events'] = events_ser.data
        return Response(context)

    @list_route(methods=["GET"])
    def get_event_orders_by_event(self, request):

        search = request.query_params.get("search", None)
        event_id = request.query_params.get("event_id", None)
        event_obj = Event.objects.get(id=int(event_id))

        obj=Order.objects.filter(event=event_obj).filter( Q(user_email__iexact=search) | Q(user_mobile=search) |Q(book_id=search )|Q(order_state=search)).order_by('-created')
        all_orders_ser = OrderSerializer(obj,many=True)
        return Response(all_orders_ser.data)

    @list_route(methods=["GET"])
    def export_all_org_orders_excel(self, request):
        all_orddata = all_ord(self.request.user)
        all_orders = all_orddata["all_ord"]
        all_orders_ser = CrmOrderCustomeSerializer(all_orders, many=True)
        response = export(queryset=all_orders_ser.data, filename='Dashboard Orders')
        return response

    @list_route(methods=["GET"])
    def export_single_org_orders_excel(self, request):
        org_id = request.query_params.get("organisation_id", None)
        org_obj = Oragnization.objects.get(id=int(org_id))
        all_orddata = single_org_order(org_obj)
        all_orders = all_orddata["all_ord"]
        all_orders_ser = CrmOrderCustomeSerializer(all_orders, many=True)
        response = export(queryset=all_orders_ser.data, filename='Dashboard Orders')
        return response

class TheatreSourcesViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving Shows.
    """

    queryset = TheatreSources.objects.all()
    serializer_class = TheatreSourceSerializer
    authentication_classes = (TokenAuthentication,)
    # permission_classes = (IsAnonCreate,)
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_class = TheatreSourcesFilter
    search_fields = ('source','enabled')
    pagination_class = StandardResultsSetPagination


    @list_route(methods=["POST"])
    def disable_theatre_chain(self, request):
        try:
            source_id = request.data["source_id"]
            theatre = TheatreSources.objects.get(id=source_id)
            theatre.enabled=False
            theatre.save()
            serializer = TheatreSourceSerializer(theatre)
            context = {"results": serializer.data}
            return Response(context, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(error_codes.exception(e.args[0]), status=status.HTTP_417_EXPECTATION_FAILED)

    @list_route(methods=["POST"])
    def enable_theatre_chain(self, request):
        try:
            source_id = request.data["source_id"]
            theatre = TheatreSources.objects.get(id=source_id)
            theatre.enabled=True
            theatre.save()
            serializer = TheatreSourceSerializer(theatre)
            context = {"results": serializer.data}
            return Response(context, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(error_codes.exception(e.args[0]), status=status.HTTP_417_EXPECTATION_FAILED)

