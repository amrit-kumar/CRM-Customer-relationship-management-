__author__ = 'gaurav'
import django_filters
from django_filters import Filter
from django_filters.fields import Lookup
import datetime
from django_filters import rest_framework as filters
from django.db.models import Q

from tixdo.booking.models import Order, MovieOrderDetail, EventOrderDetail
from tixdo.crm.models import MsgReports
from tixdo.coupons.models import Coupon
from tixdo.shows.models import Show
from tixdo.theatres.models import Theatre, TheatreSources
from tixdo.coupons.models import Campaign
from tixdo.crm.utils import get_date_fomatted
from tixdo.tixdo_events.event_app.models import Organization, TicketType, Seats, Category, Venue, Discount, OrgMember, Event, \
    Shows


class ListFilter(Filter):
    def filter(self, qs, value):
        value_list = value.split(u',')
        return super(ListFilter, self).filter(qs, Lookup(value_list, 'in'))


def filter_unix_dt(queryset, value):
    if not value:
        return queryset

    try:
        unix_time = int(value)
        t = datetime.date.fromtimestamp(unix_time)
        result = queryset.filter(created__gte=t)
        return result
    except ValueError:
        return queryset


def filter_show_date_custom(self, qs, value):
    dt = value.split("T")[0]
    act_date = datetime.datetime.strptime(dt, '%Y-%m-%d')
    main_date = act_date.strftime("%A %d %B %Y")
    main_date_mov = act_date.strftime("%d %b, %Y")
    # show_date = obj.show_date
    # # Saturday 04 February 2017 ---> %A %d %B %Y
    # # 17 Jan, 2017 ---> %d %b, %Y
    # if show_date:
    #     if not len(show_date.split("-")) > 1:
    #         if len(show_date.split(" ")) == 3:
    #             show_date = datetime.datetime.strptime(show_date, '%d %b, %Y')
    #         else:
    #             show_date = datetime.datetime.strptime(show_date, '%A %d %B %Y')
    return Order.objects.filter(Q(show_date__icontains=main_date) | Q(show_date__icontains=main_date_mov) | Q(show_date__icontains=dt))

class OrderFilter(django_filters.FilterSet):
    theatre = django_filters.CharFilter(name="theatre__title", lookup_expr='icontains')

    book_id = django_filters.CharFilter(name='book_id', lookup_expr='icontains')
    user_mobile = django_filters.CharFilter(name='user_mobile', lookup_expr='icontains')
    user_email = django_filters.CharFilter(name='user_email', lookup_expr='icontains')
    user = django_filters.CharFilter(name='user__username', lookup_expr='icontains')
    payment_id = django_filters.CharFilter(name='payment_id', lookup_expr='icontains')

    event_name = django_filters.CharFilter(name='event_name', lookup_expr='icontains')
    movie_name = django_filters.CharFilter(name='movie_name', lookup_expr='icontains')
    total_payment = django_filters.CharFilter(name='total_payment', lookup_expr='icontains')
    payment_state = django_filters.CharFilter(name='payment_state', lookup_expr='icontains')
    order_type = django_filters.CharFilter(name='order_type', lookup_expr='icontains')
    order_state = django_filters.CharFilter(name='order_state', lookup_expr='icontains')
    tid = django_filters.CharFilter(name='tid', lookup_expr='icontains')
    show_time = django_filters.CharFilter(name='show_time', lookup_expr='icontains')
    show_date = django_filters.CharFilter(name='show_date', lookup_expr='icontains')
    show_date_custom = filters.CharFilter(method='filter_show_datedata')



    class Meta:
        """
        Use multiple fields to enable multiple filtering.....
        """
        model = Order

        fields = ['theatre', 'book_id', 'user_mobile', 'user_email', 'user', 'payment_id', 'event_name', 'movie_name', 'total_payment', 'order_type', 'order_state', 'tid', 'show_time', 'show_date', 'show_date_custom']

        # fields = {
        #                 'book_id': ['exact', 'icontains'],
        #                 'user_mobile': ['exact', 'icontains'],
        #                 'user_email': ['exact', 'icontains'],
        #                 'user__username': ['exact', 'icontains'],
        #                 'payment_id': ['exact', 'icontains'],
        #                 'event_name': ['exact', 'icontains'],
        #                 'movie_name': ['exact', 'icontains'],
        #                 'total_payment': ['exact', 'icontains'],
        #                 'payment_state': ['exact', 'icontains'],
        #                 'order_type': ['exact', 'icontains'],
        #                 'order_state': ['exact', 'icontains'],
        #                 'tid': ['exact', 'icontains'],
        #                 'show_time': ['exact', 'icontains'],
        #                 'show_date': ['exact', 'icontains'],
        #                 'theatre__title': ['exact', 'icontains']
        #             }

        # exclude = ['confirmation_code', 'show_detail', 'user_detail', 'form_data', 'taxes', 'device_details',
        #            'payment_gateway_response']


    def filter_show_datedata(self, qs, name, value):
        dt = value.split("T")[0]
        try:
            act_date = datetime.datetime.strptime(dt, '%d/%m/%Y')
        except:
            act_date= datetime.datetime.strptime(dt, '%d-%m-%Y')
        main_date = act_date.strftime("%A %d %B %Y")
        main_date_mov = act_date.strftime("%d %b, %Y")
        # show_date = obj.show_date
        # # Saturday 04 February 2017 ---> %A %d %B %Y
        # # 17 Jan, 2017 ---> %d %b, %Y

        return qs.filter(Q(show_date__icontains=main_date) | Q(show_date__icontains=main_date_mov) | Q(show_date__icontains=dt))



class MovieOrderFilter(django_filters.FilterSet):
    theatre = django_filters.CharFilter(name="theatre__title", lookup_expr='icontains')

    book_id = django_filters.CharFilter(name='order__book_id', lookup_expr='icontains')
    user_mobile = django_filters.CharFilter(name='order__user_mobile', lookup_expr='icontains')
    user_email = django_filters.CharFilter(name='order__user_email', lookup_expr='icontains')
    user = django_filters.CharFilter(name='order__user__username', lookup_expr='icontains')
    # payment_id = django_filters.CharFilter(name='payment_id', lookup_expr='icontains')

    # event_name = django_filters.CharFilter(name='event_name', lookup_expr='icontains')
    movie_name = django_filters.CharFilter(name='movie_name', lookup_expr='icontains')
    total_payment_by_user = django_filters.CharFilter(name='total_payment_by_user', lookup_expr='icontains')
    order_type = django_filters.CharFilter(name='order__order_type', lookup_expr='icontains')
    order_state = django_filters.CharFilter(name='order__order_state', lookup_expr='icontains')
    tid = django_filters.CharFilter(name='order__tid', lookup_expr='icontains')
    show_time = django_filters.CharFilter(name='show_time', lookup_expr='icontains')
    show_date = django_filters.CharFilter(name='show_date', lookup_expr='icontains')
    show_date_custom = filters.CharFilter(method='filter_show_datedata')
    city = django_filters.CharFilter(name='theatre__city', lookup_expr='icontains')



    class Meta:
        """
        Use multiple fields to enable multiple filtering.....
        """
        model = MovieOrderDetail

        fields = ['theatre', 'book_id', 'user_mobile', 'user_email', 'user', 'movie_name', 'total_payment_by_user', 'order_type', 'order_state', 'tid', 'show_time', 'show_date', 'show_date_custom']

    def filter_show_datedata(self, qs, name, value):
        dt = value.split("T")[0]
        try:
            act_date = datetime.datetime.strptime(dt, '%d/%m/%Y')
            dt=datetime.datetime.strptime(dt, '%d/%m/%Y').strftime('%d-%m-%Y')
        except:
            act_date= datetime.datetime.strptime(dt, '%d-%m-%Y')
        main_date = act_date.strftime("%A %d %B %Y")
        main_date_mov = act_date.strftime("%d %b, %Y")
        # show_date = obj.show_date
        # # Saturday 04 February 2017 ---> %A %d %B %Y
        # # 17 Jan, 2017 ---> %d %b, %Y

        return qs.filter(Q(show_date__icontains=main_date) | Q(show_date__icontains=main_date_mov) | Q(show_date__icontains=dt))



class EventOrderFilter(django_filters.FilterSet):
    theatre = django_filters.CharFilter(name="theatre__title", lookup_expr='icontains')

    book_id = django_filters.CharFilter(name='order__book_id', lookup_expr='icontains')
    user_mobile = django_filters.CharFilter(name='order__user_mobile', lookup_expr='icontains')
    user_email = django_filters.CharFilter(name='order__user_email', lookup_expr='icontains')
    user = django_filters.CharFilter(name='order__user__username', lookup_expr='icontains')
    # payment_id = django_filters.CharFilter(name='payment_id', lookup_expr='icontains')

    event_name = django_filters.CharFilter(name='event_name', lookup_expr='icontains')
    # movie_name = django_filters.CharFilter(name='movie_name', lookup_expr='icontains')
    total_payment_by_user = django_filters.CharFilter(name='total_payment_by_user', lookup_expr='icontains')
    order_type = django_filters.CharFilter(name='order__order_type', lookup_expr='icontains')
    order_state = django_filters.CharFilter(name='order__order_state', lookup_expr='icontains')
    tid = django_filters.CharFilter(name='order__tid', lookup_expr='icontains')
    show_time = django_filters.CharFilter(name='show_time', lookup_expr='icontains')
    show_date = django_filters.CharFilter(name='show_date', lookup_expr='icontains')
    show_date_custom = filters.CharFilter(method='filter_show_datedata')



    class Meta:
        """
        Use multiple fields to enable multiple filtering.....
        """
        model = EventOrderDetail

        fields = ['theatre', 'book_id', 'user_mobile', 'user_email', 'user', 'event_name', 'total_payment_by_user', 'order_type', 'order_state', 'tid', 'show_time', 'show_date', 'show_date_custom']

    def filter_show_datedata(self, qs, name, value):
        dt = value.split("T")[0]
        try:
            act_date = datetime.datetime.strptime(dt, '%d/%m/%Y')
            dt=datetime.datetime.strptime(dt, '%d/%m/%Y').strftime('%d-%m-%Y')
        except:
            act_date= datetime.datetime.strptime(dt, '%d-%m-%Y')
        main_date = act_date.strftime("%A %d %B %Y")
        main_date_mov = act_date.strftime("%d %b, %Y")
        # show_date = obj.show_date
        # # Saturday 04 February 2017 ---> %A %d %B %Y
        # # 17 Jan, 2017 ---> %d %b, %Y

        return qs.filter(Q(show_date__icontains=main_date) | Q(show_date__icontains=main_date_mov) | Q(show_date__icontains=dt))




class MovieShowFilter(django_filters.FilterSet):
    city = django_filters.CharFilter(name='theatre__city', lookup_expr='icontains')
    theatre = django_filters.CharFilter(name='theatre__title', lookup_expr='icontains')
    movie = django_filters.CharFilter(name='movie__title', lookup_expr='icontains')
    date = filters.CharFilter(method='filter_show_datedata')
    class Meta:
        """
        Use multiple fields to enable multiple filtering.....
        """
        model = Show
        exclude = ['movie_detail', 'theatre_detail', 'price', 'show_remote_info']

    def filter_show_datedata(self, qs, name, value):
        query = value.split("T")[0]
        main_date = get_date_fomatted(query)
        try:
            dateobj = datetime.datetime.strptime(main_date, '%d-%m-%Y')
        except:
            dateobj = datetime.datetime.strptime(main_date, '%Y-%m-%d')
        return qs.filter(Q(date=dateobj))



class CampaignFilter(django_filters.FilterSet):
    class Meta:
        """
        Use multiple fields to enable multiple filtering.....
        """
        model = Campaign
        exclude = ['updated']


class MovieTheaterFilter(django_filters.FilterSet):
    class Meta:
        """
        Use multiple fields to enable multiple filtering.....
        """
        model = Theatre
        exclude = ['amenities', 'theatre_remote_info']


class MsgReportFilter(django_filters.FilterSet):
    class Meta:
        """
        Use multiple fields to enable multiple filtering.....
        """
        model = MsgReports
        exclude = ['id', 'user_id', 'sender_id', 'campaign_name']


class CouponFilter(django_filters.FilterSet):
    class Meta:
        """
        Use multiple fields to enable multiple filtering.....
        """
        model = Coupon
        exclude = ['created', 'modified']


class OrganizationDataFilter(django_filters.FilterSet):
    account_name = django_filters.CharFilter(name='account_id__name', lookup_expr='icontains')
    account_legal_name = django_filters.CharFilter(name='account_id__name', lookup_expr='icontains')
    member = django_filters.CharFilter(name='member__username', lookup_expr='icontains')

    class Meta:
        """
        Use multiple fields to enable multiple filtering.....
        """
        model = Organization
        # fields = {'account_id__name': ['icontains'], 'title': ['icontains'], 'member__username': ['icontains'],
        #           'member__email': ['icontains'], 'member__phone': ['icontains'], 'member__first_name': ['icontains'],
        #           'member__last_name': ['icontains']}
        exclude = ['logo']


class CategoryFilter(django_filters.FilterSet):

    class Meta:
        """
        Use multiple fields to enable multiple filtering.....
        """
        model = Category
        exclude = []

class VenueFilter(django_filters.FilterSet):

    class Meta:
        """
        Use multiple fields to enable multiple filtering.....
        """
        model = Venue
        exclude = []


class OrgMemberFilter(django_filters.FilterSet):
    member = django_filters.CharFilter(name='member__username', lookup_expr='icontains')
    member_email = django_filters.CharFilter(name='member__email', lookup_expr='icontains')
    member_phone = django_filters.CharFilter(name='member__phpne', lookup_expr='icontains')
    class Meta:
        """
        Use multiple fields to enable multiple filtering.....
        """
        model = OrgMember
        exclude = []


class EventFilter(django_filters.FilterSet):
    attendees = django_filters.CharFilter(name='member__username', lookup_expr='icontains')
    attendees_email = django_filters.CharFilter(name='member__email', lookup_expr='icontains')
    attendees_phone = django_filters.CharFilter(name='member__phpne', lookup_expr='icontains')
    organizer = django_filters.CharFilter(name='organizer__title', lookup_expr='icontains')
    class Meta:
        """
        Use multiple fields to enable multiple filtering.....
        """
        model = Event
        exclude = ['banner', 'logo', 'seat_layout_img', 'search_keywords', 'bcc_emails']

class ShowsFilter(django_filters.FilterSet):
    event = django_filters.CharFilter(name='event__title', lookup_expr='icontains')
    venue = django_filters.CharFilter(name='venue__title', lookup_expr='icontains')
    class Meta:
        """
        Use multiple fields to enable multiple filtering.....
        """
        model = Shows
        exclude = []


class TicketTypeFilter(django_filters.FilterSet):
    show = django_filters.CharFilter(name='show__title', lookup_expr='icontains')
    class Meta:
        """
        Use multiple fields to enable multiple filtering.....
        """
        model = TicketType
        exclude = []


class SeatsFilter(django_filters.FilterSet):
    ticket_type = django_filters.CharFilter(name='ticket_type__title', lookup_expr='icontains')
    class Meta:
        """
        Use multiple fields to enable multiple filtering.....
        """
        model = Seats
        exclude = ['code_img',]

class DiscountFilter(django_filters.FilterSet):
    ticket_type = django_filters.CharFilter(name='ticket_type__title', lookup_expr='icontains')
    class Meta:
        """
        Use multiple fields to enable multiple filtering.....
        """
        model = Discount
        exclude = []

class TheatreSourcesFilter(django_filters.FilterSet):
    source = django_filters.CharFilter(name='source', lookup_expr='icontains')
    class Meta:
        """
        Use multiple fields to enable multiple filtering.....
        """
        model = TheatreSources
        exclude = []
