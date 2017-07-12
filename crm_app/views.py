from django.shortcuts import render
from django.http import HttpResponse


from tixdo.third_party_apps import juspay as Juspay

from django.conf import settings
from django.views.decorators.csrf import csrf_protect, csrf_exempt


from tixdo.taskapp.tasks import create_msg91_report_task
from tixdo.tixdo_events.event_app.views import admin_org_list_func
from tixdo.crm.serializers import OrganizationSerializer, EventSerializer, EventMainCustomeSerializer
from django.http import JsonResponse

# Create your views here.

Juspay.api_key = settings.JUSPAY_API_KEY
def testview(request):
    justpaylist = Juspay.Orders.list()
    return HttpResponse("Done")


@csrf_exempt
def msg91post(request):
    try:
        if request.META['HTTP_X_FORWARDED_FOR'] == "54.254.154.166":
            if request.POST:
                import ast
                data = ast.literal_eval(request.POST['data'])
                if data[0]['senderId'] == "tixdov":
                    create_msg91_report_task.delay(data[0])
                    return HttpResponse(status=200)
            else:
                return HttpResponse(status=500)
        else:
            return HttpResponse(status=500)
    except:
        return HttpResponse(status=500)


@csrf_exempt
def orgnizationsingledashboard(request, slug):
    context = admin_org_list_func(slug)
    orga = context['organization']
    org_ser = OrganizationSerializer(orga)
    events = context['events']
    events_ser = EventMainCustomeSerializer(events, many=True)
    context['organization'] = org_ser.data
    context['events'] = events_ser.data
    return JsonResponse(context)


