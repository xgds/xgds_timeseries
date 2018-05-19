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

from xgds_timeseries.models import TimeSeriesModel


def get_time_series_classes():
    """
    :return: a list of [app_label.classname] for classes that extend TimeSeriesModel
    """
    list_result = []
    for the_class in TimeSeriesModel.__subclasses__():
        list_result.append('%s.%s' % (the_class._meta.app_label, the_class.__name__))
    return JsonResponse(list_result)


def unravel_post(post_dict):
    """
    Read the useful contents of the post dictionary
    :param post_dict:
    :return:
    """
    class PostData(object):
        model = None
        channel_names = None
        flight_ids = None
        start_time = None
        end_time = None
        filter_dict = None

    result = PostData()
    model_name = post_dict.get('modelName', None)
    # model name is required
    if model_name:
        result.model = getModelByName(model_name)
    result.channel_names = post_dict.getlist('channel_names', None)
    result.flight_ids = post_dict.getlist('flight_ids', None)
    start_time_string = post_dict.get('start_time', None)
    if start_time_string:
        result.start_time = dateparser(start_time_string)
    end_time_string = post_dict.get('end_time', None)
    if end_time_string:
        result.end_time = dateparser(end_time_string)
    filter_json = post_dict.get('filter', None)
    if filter_json:
        result.filter_dict = json.loads(filter_json)
    return result


def get_min_max(model, start_time=None, end_time=None, flight_ids=None, filter_dict=None, channel_names=None):
    """
    Returns a dict with the min max values
    :param model: The model to use
    :param start_time: datetime of start time
    :param end_time: datetime of end time
    :param flight_ids: The list of channel names you are interested in
    :param filter_dict: a dictionary of any other filter
    :param channel_names: The list of channel names you are interested in
    :return: a list of dicts with the min max values.
    """
    return model.objects.get_min_max(start_time, end_time, flight_ids, filter_dict, channel_names)


def get_min_max_json(request):
    """
    Returns a JsonResponse with min and max values
    :param request:
    :return:
    """
    if request.method == 'POST':
        post_values = unravel_post(request.POST)
        if not post_values.model:
            return Http404('Model is required')

        values = get_min_max(post_values.model, post_values.channel_names, post_values.flight_ids,
                             post_values.start_time, post_values.end_time, post_values.filter_dict)
        return JsonResponse(values, encoder=DatetimeJsonEncoder)
    return HttpResponseForbidden()


def get_values_list(model, channels, flight_ids, start_time, end_time, filter_dict):
    """
    Returns a list of dicts of the data values
    :param model: The model to use
    :param channels: The list of channel names you are interested in
    :param flight_ids: The list of channel names you are interested in
    :param start_time: datetime of start time
    :param end_time: datetime of end time
    :param filter_dict: a dictionary of any other filter
    :return: a list of dicts with the results.
    """
    values = model.objects.get_values(start_time, end_time, flight_ids, filter_dict, channels)
    return list(values)


def get_values_json(request):
    """
    Returns a JsonResponse of the data values described by the filters in the POST dictionary
    :param request: the request
    :request.POST:
    : modelName: The fully qualified name of the model, ie xgds_braille_app.Environmental
    : channel_names: The list of channel names you are interested in
    : flight_ids: The list of flight ids to filter by
    : start_time: Isoformat start time
    : end_time: Isoformat end time
    : filter: Json string of a dictionary to further filter the data
    :return: a JsonResponse with a list of dicts with all the results
    """
    if request.method == 'POST':
        post_values = unravel_post(request.POST)
        if not post_values.model:
            return Http404('Model is required')

        values = get_values_list(post_values.model, post_values.channel_names, post_values.flight_ids,
                                 post_values.start_time, post_values.end_time, post_values.filter_dict)
        return JsonResponse(values, encoder=DatetimeJsonEncoder)
    return HttpResponseForbidden()



