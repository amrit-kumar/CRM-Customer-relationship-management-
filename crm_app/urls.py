from django.conf.urls import url, include

from rest_framework.routers import DefaultRouter
# from rest_framework_nested import routers

from tixdo.crm.api import JusPayViewSet, CrmOrderViewSet, TheatersViewSet, ShowsViewSet, CampaignDataViewSet, CouponDataViewSet, MsgReportViewSet, \
    OrganizationViewSet, CategoryViewSet, OrgMemberViewSet, VenueViewSet, EventViewSet, EventShowsViewSet, TicketTypeViewSet, SeatsViewSet, \
    DiscountViewSet, CrmMovieOrderViewSet, CrmEventOrderViewSet, OrganizationDashboardViewSet, TheatreSourcesViewSet
from tixdo.crm.views import msg91post, orgnizationsingledashboard


router = DefaultRouter()


# router1 = routers.SimpleRouter()
# router1.register(r'campaignsn', CampaignDataViewSet, base_name='campaignsn')
# campaigns_router = routers.NestedSimpleRouter(router1, r'campaignsn')
# campaigns_router.register(r'couponsn', CouponNestedViewSet, base_name='couponsn')

router.register(r'orders', CrmOrderViewSet, base_name='ordersdata')
router.register(r'movie-orders', CrmMovieOrderViewSet, base_name='movieorders')
router.register(r'event-orders', CrmEventOrderViewSet, base_name='eventorders')
router.register(r'transactions', JusPayViewSet, base_name='transactions')
router.register(r'theatres', TheatersViewSet, base_name='theatres')
router.register(r'shows', ShowsViewSet, base_name='shows')
router.register(r'campaigns', CampaignDataViewSet, base_name='campaign')
router.register(r'coupons', CouponDataViewSet, base_name='coupon')
router.register(r'msg91reports', MsgReportViewSet, base_name='msg91reports')

router.register(r'organizations', OrganizationViewSet, base_name='organizations')
router.register(r'categories', CategoryViewSet, base_name='categories')
router.register(r'orgmember', OrgMemberViewSet, base_name='orgmember')
router.register(r'venues', VenueViewSet, base_name='venues')
router.register(r'events', EventViewSet, base_name='events')
router.register(r'eventshows', EventShowsViewSet, base_name='eventshows')
router.register(r'tickettypes', TicketTypeViewSet, base_name='tickettypes')
router.register(r'seats', SeatsViewSet, base_name='seats')
router.register(r'discounts', DiscountViewSet, base_name='discount')
router.register(r'theatre-source', TheatreSourcesViewSet, base_name='theatre_source')

router.register(r'orgdashboard', OrganizationDashboardViewSet, base_name='orgdashboard')


urlpatterns = router.urls

urlpatterns += [
    url(r'^msg91/$', msg91post, name='msg91post'),
    # url(r'^', include(router1.urls)),
    # url(r'^', include(campaigns_router.urls)),
    url(r'^organizationsdata/(?P<slug>[-\w\d]+)/$', orgnizationsingledashboard, name='orgnizationsingledashboard'),

]

