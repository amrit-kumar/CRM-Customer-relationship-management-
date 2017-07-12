# Third party imports
import datetime
from rest_framework import serializers
from django.apps import apps

# Import from apps

from tixdo.crm.models import MsgReports
from tixdo.booking.models import Order, EventOrderDetail, EventOrderTicketType, EventOrderDiscountApplied, MovieOrderDetail, Payment
from tixdo.tixdo_events.event_app.models import TicketType, Category, OrgMember, Venue, Event, Shows, Seats, Discount, EventIndexPage
from tixdo.third_party_apps.forms.models import Form
from tixdo.tixdo_events.event_app.templatetags.event_tags import ticket_price_without_discount_temp, ticket_price_with_discount_minus_internetHandlingFee_temp, \
    ticket_type_wise_price
from tixdo.organizations.models import Oragnization
from tixdo.organizations.event_partner.models import EventPartner, EventPartnerMember
from tixdo.wallet.serializers import WalletTransaction
from tixdo.movies.models import Movies
from tixdo.cities.models import City
from tixdo.bookkeeper.models import Account
from tixdo.theatres.models import Theatre
from tixdo.shows.models import Show
from tixdo.coupons.models import Campaign
from tixdo.theatres.models import TheatreSources
from tixdo.movies.models import CityMovie


class CityMovieSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField('get_movie_name')
    class Meta:
        model = CityMovie
        fields = ['id', 'name']

    def get_movie_name(self, obj):
        return obj.movie.title


class JusPaySerializer(serializers.Serializer):
    order_id = serializers.CharField(max_length=240)
    merchant_id = serializers.CharField(max_length=240)
    amount = serializers.CharField(max_length=240)
    status = serializers.CharField(max_length=240)
    status_id = serializers.CharField(max_length=240)
    amount_refunded = serializers.CharField(max_length=240)
    refunded = serializers.CharField(max_length=240)
    currency = serializers.CharField(max_length=240)


class PaymentSerializers(serializers.ModelSerializer):
    class Meta:
        model = Payment
        # exclude = ['updated']


class CrmOrderDetailDataSerializer(serializers.ModelSerializer):

    """ Returns serialized data of Order's instance. """

    show_date_custom = serializers.SerializerMethodField('get_show_date_all')
    # show_date = serializers.SerializerMethodField('get_show_detail')
    show_detail = serializers.SerializerMethodField('get_show_detail_data')
    wallettransaction = WalletTransaction()

    def get_show_date_all(self, obj):
        show_date = obj.show_date
        # Saturday 04 February 2017 ---> %A %d %B %Y
        # 17 Jan, 2017 ---> %d %b, %Y
        if show_date:
            if not len(show_date.split("-")) > 1:
                if len(show_date.split(" ")) == 3:
                    show_date = datetime.datetime.strptime(show_date, '%d %b, %Y')
                else:
                    show_date = datetime.datetime.strptime(show_date, '%A %d %B %Y')

        return show_date

    def get_show_detail_data(self, obj):
        if obj.order_type == "movie":
            show_detail = [obj.show_detail]

        else:
            show_detail = obj.show_detail

        return show_detail

    class Meta:
        model = Order
        exclude = ['payment_gateway_response', 'modified', 'theatre', 'event', 'user']


class CrmOrderSerializer(serializers.ModelSerializer):

    """ Returns serialized data of Order's instance. """

    show_date_custom = serializers.SerializerMethodField('get_show_date_all')
    # show_date = serializers.SerializerMethodField('get_show_detail')
    # show_detail = serializers.SerializerMethodField('get_show_detail_data')
    theatre = serializers.SerializerMethodField('get_theatre_name')

    def get_theatre_name(self, obj):
        try:
            theatre_name = obj.theatre.title
        except:
            theatre_name = None
        return theatre_name

    def get_show_date_all(self, obj):
        show_date = obj.show_date
        # Saturday 04 February 2017 ---> %A %d %B %Y
        # 17 Jan, 2017 ---> %d %b, %Y
        if show_date:
            if not len(show_date.split("-")) > 1:
                if len(show_date.split(" ")) == 3:
                    show_date = datetime.datetime.strptime(show_date, '%d %b, %Y')
                else:
                    show_date = datetime.datetime.strptime(show_date, '%A %d %B %Y')

        return show_date

    def get_show_detail_data(self, obj):
        if obj.order_type == "movie":
            show_detail = [obj.show_detail]

        else:
            show_detail = obj.show_detail

        return show_detail

    class Meta:
        model = Order
        fields = ['id', 'book_id', 'user_mobile', 'user_email', 'order_type', 'order_state', 'event_name', 'theatre', 'show_date_custom']


class CrmMovieOrderSerializer(serializers.ModelSerializer):

    """ Returns serialized data of Order's instance. """

    show_date_custom = serializers.SerializerMethodField('get_show_date_all')
    id = serializers.SerializerMethodField('get_order_id')
    book_id = serializers.SerializerMethodField()
    user_mobile = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    order_type = serializers.SerializerMethodField()
    order_state = serializers.SerializerMethodField()
    payment_gateway = serializers.SerializerMethodField()
    theatre = serializers.SerializerMethodField('get_theatre_name')
    payment_state = serializers.SerializerMethodField()

    def get_order_id(self, obj):
        try:
            order_id = obj.order.id
        except:
            order_id = obj.id
        return order_id

    def get_book_id(self, obj):
        try:
            book_id = obj.order.book_id
        except:
            book_id = obj.book_id
        return book_id

    def get_user_mobile(self, obj):
        try:
            user_mobile = obj.order.user_mobile
        except:
            user_mobile = obj.user_mobile
        return user_mobile

    def get_user_email(self, obj):
        try:
            user_email = obj.order.user_email
        except:
            user_email = obj.user_email
        return user_email

    def get_order_type(self, obj):
        try:
            order_type = obj.order.order_type
        except:
            order_type = obj.order_type
        return order_type

    def get_order_state(self, obj):
        try:
            order_state = obj.order.order_state
        except:
            order_state = obj.order_state
        return order_state

    def get_payment_gateway(self, obj):
        try:
            payment_gateway = obj.order.payment_gateway
        except:
            payment_gateway = obj.payment_gateway
        return payment_gateway


    def get_theatre_name(self, obj):
        try:
            theatre_name = obj.theatre.title
        except:
            theatre_name = None
        return theatre_name

    def get_show_date_all(self, obj):

        show_date = obj.show_date
        # Saturday 04 February 2017 ---> %A %d %B %Y
        # 17 Jan, 2017 ---> %d %b, %Y
        if show_date:
            if not len(show_date.split("-")) > 1:
                if len(show_date.split(" ")) == 3:
                    show_date = datetime.datetime.strptime(show_date, '%d %b, %Y')
                else:
                    show_date = datetime.datetime.strptime(show_date, '%A %d %B %Y')

        return show_date

    def get_show_detail_data(self, obj):
        if obj.order_type == "movie":
            show_detail = [obj.show_detail]

        else:
            show_detail = obj.show_detail

        return show_detail
    def get_payment_state(self,obj):
        try:
            return obj.order.payment_state
        except:
            return None

    class Meta:
        model = MovieOrderDetail
        fields = ['id', 'book_id','show_time','show_date', 'user_mobile', 'user_email', 'order_type', 'order_state', 'theatre', 'show_date_custom', 'payment_gateway','payment_state']


class EventOrderDiscountAppliedSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventOrderDiscountApplied


class EventOrderTicketTypeSerializer(serializers.ModelSerializer):
    discount_applied = serializers.SerializerMethodField('get_discount_applied_data')


    def get_discount_applied_data(self, obj):
        try:
            dicountapplieddataquery = EventOrderDiscountApplied.objects.filter(eventordertickettype=obj)
            dicountapplieddataraw = EventOrderDiscountAppliedSerializer(dicountapplieddataquery, many=True)
            dicountapplieddata = dicountapplieddataraw.data
        except:
            dicountapplieddata = None
        return dicountapplieddata

    class Meta:
        model = EventOrderTicketType


class CrmEventOrderSerializer(serializers.ModelSerializer):

    """ Returns serialized data of Order's instance. """

    show_date_custom = serializers.SerializerMethodField('get_show_date_all')

    id = serializers.SerializerMethodField('get_order_id')
    book_id = serializers.SerializerMethodField()
    user_mobile = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    order_type = serializers.SerializerMethodField()
    order_state = serializers.SerializerMethodField()
    payment_gateway = serializers.SerializerMethodField()
    payment_state = serializers.SerializerMethodField()
    # event_name = serializers.SerializerMethodField('get_theatre_name')


    def get_order_id(self, obj):
        try:
            order_id = obj.order.id
        except:
            order_id = obj.id
        return order_id

    def get_book_id(self, obj):
        try:
            book_id = obj.order.book_id
        except:
            book_id = obj.book_id
        return book_id

    def get_user_mobile(self, obj):
        try:
            user_mobile = obj.order.user_mobile
        except:
            user_mobile = obj.user_mobile
        return user_mobile

    def get_user_email(self, obj):
        try:
            user_email = obj.order.user_email
        except:
            user_email = obj.user_email
        return user_email

    def get_order_type(self, obj):
        try:
            order_type = obj.order.order_type
        except:
            order_type = obj.order_type
        return order_type

    def get_order_state(self, obj):
        try:
            order_state = obj.order.order_state
        except:
            order_state = obj.order_state
        return order_state

    def get_payment_gateway(self, obj):
        try:
            payment_gateway = obj.order.payment_gateway
        except:
            payment_gateway = obj.payment_gateway
        return payment_gateway


    def get_theatre_name(self, obj):
        try:
            theatre_name = obj.theatre.title
        except:
            theatre_name = None
        return theatre_name

    def get_show_date_all(self, obj):
        show_date = obj.show_date
        # Saturday 04 February 2017 ---> %A %d %B %Y
        # 17 Jan, 2017 ---> %d %b, %Y
        if show_date:
            if not len(show_date.split("-")) > 1:
                if len(show_date.split(" ")) == 3:
                    show_date = datetime.datetime.strptime(show_date, '%d %b, %Y')
                else:
                    show_date = datetime.datetime.strptime(show_date, '%A %d %B %Y')

        return show_date

    def get_show_detail_data(self, obj):
        if obj.order_type == "movie":
            show_detail = [obj.show_detail]

        else:
            show_detail = obj.show_detail

        return show_detail

    def get_payment_state(self,obj):
        try:
            return obj.order.payment_state
        except:
            return None

    class Meta:
        model = EventOrderDetail
        fields = ['id', 'book_id', 'user_mobile', 'user_email', 'order_type', 'order_state', 'event_name', 'show_date_custom', 'payment_gateway','payment_state', 'show_time']


class CrmMoviewOrderDetailDataSerializer(serializers.ModelSerializer):

    """ Returns serialized data of Order's instance. """

    show_date_custom = serializers.SerializerMethodField('get_show_date_all')
    # show_date = serializers.SerializerMethodField('get_show_detail')
    # show_detail = serializers.SerializerMethodField('get_show_detail_data')
    # wallettransaction = WalletTransaction()
    order = CrmMovieOrderSerializer()
    payment = serializers.SerializerMethodField('get_payment_data')
    payment_state = serializers.SerializerMethodField()
    transaction_id=serializers.SerializerMethodField()

    def get_payment_data(self, obj):
        payments = Payment.objects.filter(order=obj.order)
        payment_ser = PaymentSerializers(payments, many=True)
        return payment_ser.data

    def get_show_date_all(self, obj):
        show_date = obj.show_date

        # Saturday 04 February 2017 ---> %A %d %B %Y
        # 17 Jan, 2017 ---> %d %b, %Y
        if show_date:
            if not len(show_date.split("-")) > 1:
                if len(show_date.split(" ")) == 3:
                    show_date = datetime.datetime.strptime(show_date, '%d %b, %Y')
                else:
                    show_date = datetime.datetime.strptime(show_date, '%A %d %B %Y')

        return show_date
    def get_payment_state(self,obj):
        try:
            return obj.order.payment_state
        except:
            return None
    def get_transaction_id(self,obj):
        try:
            return obj.order.transaction_id
        except:
            return None


    class Meta:
        model = MovieOrderDetail
        exclude = ['modified', 'theatre']


class CrmEventOrderDetailDataSerializer(serializers.ModelSerializer):

    """ Returns serialized data of Order's instance. """

    show_date_custom = serializers.SerializerMethodField('get_show_date_all')
    order = CrmEventOrderSerializer()
    payment = serializers.SerializerMethodField('get_payment_data')
    event_order_ticket_type = serializers.SerializerMethodField('get_event_order_ticket_type_data')
    payment_state = serializers.SerializerMethodField()
    transaction_id=serializers.SerializerMethodField()

    def get_event_order_ticket_type_data(self, obj):
        eveordtt = EventOrderTicketType.objects.filter(eventorderdetail=obj)
        eveordtt_ser = EventOrderTicketTypeSerializer(eveordtt, many=True)
        return eveordtt_ser.data

    def get_payment_data(self, obj):
        payments = Payment.objects.filter(order=obj.order)
        payment_ser = PaymentSerializers(payments, many=True)
        return payment_ser.data

    def get_show_date_all(self, obj):
        show_date = obj.show_date
        # Saturday 04 February 2017 ---> %A %d %B %Y
        # 17 Jan, 2017 ---> %d %b, %Y
        if show_date:
            if not len(show_date.split("-")) > 1:
                if len(show_date.split(" ")) == 3:
                    show_date = datetime.datetime.strptime(show_date, '%d %b, %Y')
                else:
                    show_date = datetime.datetime.strptime(show_date, '%A %d %B %Y')

        return show_date

    def get_payment_state(self,obj):
        try:
            return obj.order.payment_state
        except:
            return None

    def get_transaction_id(self, obj):
        try:
            return obj.order.transaction_id
        except:
            return None


    class Meta:
        model = EventOrderDetail
        exclude = ['modified']


class CrmOrderCustomeSerializer(serializers.ModelSerializer):

    """ Returns serialized data of Order's instance. """

    show_date = serializers.SerializerMethodField('get_show_detail')
    ticket_price_without_discount = serializers.SerializerMethodField('get_ticket_price_without_discount_data')
    ticket_price_with_discount = serializers.SerializerMethodField('get_ticket_price_with_discount_data')

    def get_show_detail(self, obj):
        show_date = obj.show_detail[0]['show_date'] + ", " + obj.show_detail[0]['show_start_time']
        return show_date

    def get_ticket_price_without_discount_data(self, obj):
        data = ticket_price_without_discount_temp(obj)
        return data

    def get_ticket_price_with_discount_data(self, obj):
        data = ticket_price_with_discount_minus_internetHandlingFee_temp(obj)
        return data

    class Meta:
        model = Order
        fields = ['id', 'user_email', 'user_mobile', 'book_id', 'number_of_tickets', 'total_payment', 'order_type', 'created', 'show_date', 'ticket_price_without_discount',
                  'ticket_price_with_discount']


class CrmOrderCustomeDetailSerializer(serializers.ModelSerializer):

    """ Returns serialized data of Order's instance. """

    id = serializers.SerializerMethodField('get_id_data')
    user_email = serializers.SerializerMethodField('get_user_email_data')
    user_mobile = serializers.SerializerMethodField('get_user_mobile_data')
    book_id = serializers.SerializerMethodField('get_book_id_data')
    ticket_type = serializers.SerializerMethodField('get_ticket_type_data')
    number_of_tickets = serializers.SerializerMethodField('get_number_of_tickets_data')
    order_type = serializers.SerializerMethodField('get_order_type_data')
    created = serializers.SerializerMethodField('get_created_data')

    show_date = serializers.SerializerMethodField('get_show_detail')
    ticket_price_without_discount = serializers.SerializerMethodField('get_ticket_price_without_discount_data')
    ticket_price_with_discount = serializers.SerializerMethodField('get_ticket_price_with_discount_data')


    def get_id_data(self, obj):

        return obj.eventorderdetail.order.id

    def get_user_email_data(self, obj):
        return obj.eventorderdetail.order.user_email

    def get_user_mobile_data(self, obj):
        return obj.eventorderdetail.order.user_mobile

    def get_book_id_data(self, obj):
        return obj.eventorderdetail.order.book_id

    def get_number_of_tickets_data(self, obj):
        return obj.eventorderdetail.number_of_tickets

    def get_order_type_data(self, obj):
        return obj.eventorderdetail.order.order_type

    def get_created_data(self, obj):
        return obj.eventorderdetail.order.created.strftime("%d %B %Y %I:%M:%S %p")

    def get_show_detail(self, obj):
        show_date = obj.eventorderdetail.order.show_detail[0]['show_date'] + ", " + obj.eventorderdetail.order.show_detail[0]['show_start_time']
        return show_date

    def get_ticket_price_without_discount_data(self, obj):
        data = ticket_type_wise_price(obj.eventorderdetail.order)
        return data['price']

    def get_ticket_price_with_discount_data(self, obj):
        data = ticket_type_wise_price(obj.eventorderdetail.order)
        return data['total_discounted_price_individual']

    def get_ticket_type_data(self, obj):
        data = obj.ticket_type_name
        return data

    class Meta:
        model = EventOrderTicketType
        fields = ['id', 'user_email', 'user_mobile', 'book_id', 'number_of_tickets', 'order_type', 'created', 'show_date', 'ticket_price_without_discount',
                  'ticket_price_with_discount', 'ticket_type']



class MsgReportsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MsgReports

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Oragnization


class MainOrganizationSerializer(serializers.ModelSerializer):
    # events=serializers.SerializerMethodField()
    #
    # def get_events(self,obj):
    #     event_partner = EventPartner.objects.get(oragnization=obj)
    #     events = Event.objects.filter(event_partner=event_partner)
    #     serializers=EventSerializer(events,many=True)
    #     return serializers.data

    class Meta:
        model = Oragnization


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category


class OrgMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrgMember


class EventPartnerSerializer(serializers.ModelSerializer):
    # oragnization = OrganizationSerializer()
    class Meta:
        model = EventPartner


# class OrgMemberCustomSerializer(serializers.ModelSerializer):
#     count = serializers.CharField(max_length=240)
#     organization = OrganizationSerializer()
#     class Meta:
#         model = OrgMember


class OrgMemberCustomSerializer(serializers.ModelSerializer):
    count = serializers.CharField(max_length=240)
    # organization = OrganizationSerializer()
    event_partner = EventPartnerSerializer()
    class Meta:
        model = EventPartnerMember


class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event

class EventFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'title', 'slug']

class EventOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Event


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order

class EventMainCustomeSerializer(serializers.ModelSerializer):
    number_of_tickets = serializers.CharField(max_length=240)
    total_sail = serializers.CharField(max_length=240)
    total_booking_fee = serializers.CharField(max_length=240)
    total_discount = serializers.CharField(max_length=240)
    total_orders = serializers.CharField(max_length=240)
    actual_sale = serializers.CharField(max_length=240)
    ticket_type = serializers.CharField(max_length=240)
    class Meta:
        model = Event
        fields = ['start','end','status', 'ownership', 'seating', 'number_of_tickets', 'page_view_count', 'page_share_count',
                  'event_url', 'registration_page_url', 'is_online_event', 'is_public', 'attendees', 'organizer', 'tx_time_limit',
                  'category', 'shareable', 'terms_conditions', 'form', 'booking_amount', 'booking_percentage',
                  'show_on_page', 'bcc_emails', 'number_of_tickets', 'total_sail',
                  'total_booking_fee', 'total_discount', 'total_orders', 'actual_sale', 'ticket_type']

class EventCustomeSerializer(serializers.ModelSerializer):
    event_partner = EventPartnerSerializer()
    class Meta:
        model = Event

class ShowsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shows

class EventOrderDetailSerializer(serializers.ModelSerializer):
    show_date=serializers.SerializerMethodField('get_modified_date')
    def get_modified_date(self,obj):
        dt_obj = datetime.datetime.strptime(obj.show_date, '%d-%m-%Y')
        return datetime.datetime.strftime(dt_obj,'%d/%m/%Y')
    class Meta:
        model = EventOrderDetail
        fields=['show_date','show_time']


class TicketTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketType


class SeatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seats


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount

class FormSerializer(serializers.ModelSerializer):
    class Meta:
        model = Form


class EventIndexPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventIndexPage


class MovieSerializer(serializers.ModelSerializer):
    """ Returns serialized data of Movie's instance. """

    class Meta:
        model = Movies
        fields = ['id', 'title', 'slug']

class MovieCampaignSerializer(serializers.ModelSerializer):
    """ Returns serialized data of Movie's instance. """

    class Meta:
        model = Movies
        fields = ['id', 'title']

class EventIdTitleSlugSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'title', 'slug']

class EventIdTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'title']

class CitySerializer(serializers.ModelSerializer):

    """ Returns serialized data of City instances. """

    class Meta:
        model = City
        fields = ['id', 'name', 'code']

class CityIdNameSerializer(serializers.ModelSerializer):

    """ Returns serialized data of City instances. """

    class Meta:
        model = City
        fields = ['id', 'name']


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'name', 'legal_name', 'contact_person', 'contact_no']

class AccountIdNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'name']


class TheatreNameSerializer(serializers.ModelSerializer):

    """ Returns serialized data of Theatre instances. """

    class Meta:
        model = Theatre
        fields = ['id', 'title']

class TheatreDefaultSerializer(serializers.ModelSerializer):

    """ Returns serialized data of Theatre instances. """

    class Meta:
        model = Theatre
        fields = ['id', 'title', 'region', 'city', 'status', 'booking_amount', 'booking_percentage']

class ShowSerializer(serializers.ModelSerializer):

    """"Returns serialized data of Show instances."""

    movie = serializers.SerializerMethodField('get_movie_name')
    theatre = serializers.SerializerMethodField('get_theatre_name')

    def get_movie_name(self, obj):
        try:
            movie_name = obj.movie.title
        except:
            movie_name = None
        return movie_name

    def get_theatre_name(self, obj):
        try:
            theatre_name = obj.theatre.title
        except:
            theatre_name = None
        return theatre_name

    class Meta:
        model = Show
        fields = ['id', 'movie', 'dimension', 'language', 'theatre', 'city', 'enabled','date','start']

class TheatreSerializer(serializers.ModelSerializer):

    """ Returns serialized data of Theatre instances. """

    class Meta:
        model = Theatre
        fields = ['id', 'title']

class CampaignListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Campaign
        fields = ['id', 'name', 'value', 'campaign_type', 'type', 'discount_type']


class CampaignGetSerializer(serializers.ModelSerializer):
    movie = serializers.SerializerMethodField('get_movie_detail')
    event = serializers.SerializerMethodField('get_event_detail')
    city = serializers.SerializerMethodField('get_city_detail')
    theatre = serializers.SerializerMethodField('get_theatre_detail')
    theatre_chain = serializers.SerializerMethodField('get_theatre_chain_detail')


    def get_movie_detail(self, obj):
        try:
            crmobj = Movies.objects.get(id=obj.movie.id)
            crmobj_ser = MovieCampaignSerializer(crmobj)
            return crmobj_ser.data
        except:
            return None

    def get_event_detail(self, obj):
        try:
            crmobj = Event.objects.get(id=obj.event.id)
            crmobj_ser = EventIdTitleSerializer(crmobj)
            return crmobj_ser.data
        except:
            return None

    def get_city_detail(self, obj):
        try:
            crmobj = City.objects.get(id=obj.city.id)
            crmobj_ser = CityIdNameSerializer(crmobj)
            return crmobj_ser.data
        except:
            return None


    def get_theatre_detail(self, obj):
        try:
            crmobj = Theatre.objects.get(id=obj.theatre.id)
            crmobj_ser = TheatreSerializer(crmobj)
            return crmobj_ser.data
        except:
            return None

    def get_theatre_chain_detail(self, obj):
        try:
            crmobj = Account.objects.get(id=obj.theatre_chain.id)
            crmobj_ser = AccountIdNameSerializer(crmobj)
            return crmobj_ser.data
        except:
            return None

    class Meta:
        model = Campaign
        fields = ['id', 'name','created','modified', 'description', 'value','campaign_type','type','discount_type','movie','event', 'city', 'theatre','theatre_chain']

class CampaignPutPostSerializer(serializers.ModelSerializer):

    class Meta:
        model = Campaign

class TheatreSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model=TheatreSources

