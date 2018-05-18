# __BEGIN_LICENSE__
# Copyright (c) 2015, United States Government, as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All rights reserved.
#
# The xGDS platform is licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
# __END_LICENSE__

import json
from dateutil.parser import parse as dateparser


from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404, JsonResponse
from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _

from geocamUtil.loader import getModelByName
from geocamUtil.datetimeJsonEncoder import DatetimeJsonEncoder


def get_data(request):
    """
    Returns a JsonResponse of the data described by the filters in the POST dictionary
    :param request: the request
    :request.POST:
    :return:
    """
    if request.method == 'POST':
        model_name = request.POST.get('modelName', None)
        # model name is required
        model = getModelByName(model_name)
        channels = request.POST.getlist('channels', None)
        flight_ids = request.POST.getlist('flight_ids', None)
        start_time_string = request.POST.get('start_time', None)
        start_time = None
        if start_time_string:
            start_time = dateparser(start_time_string)
        end_time_string = request.POST.get('end_time', None)
        end_time = None
        if end_time_string:
            end_time = dateparser(end_time_string)

        filter_json = request.POST.get('filter', None)
        filter_dict = None
        if filter_json:
            filter_dict = json.loads(filter_json)

        values = model.objects.get_values(start_time, end_time, flight_ids, filter_dict, channels)

        return JsonResponse(list(values), encoder=DatetimeJsonEncoder)



