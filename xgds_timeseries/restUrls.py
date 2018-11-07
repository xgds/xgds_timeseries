#__BEGIN_LICENSE__
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
#__END_LICENSE__

from django.conf.urls import url

from django.conf import settings

import xgds_timeseries.views as views

urlpatterns = [url(r'^classes/metadata/json$', views.get_time_series_classes_metadata_json, {'skip_example': True},
                   'timeseries_classes_metadata_json'),
               url(r'^classes/metadata/example/json$', views.get_time_series_classes_metadata_json, {'skip_example': False},
                   'timeseries_classes_metadata_json_example'),
               url(r'^classes/json$', views.get_time_series_classes_json, {'skip_example': True}, 'timeseries_classes_json'),
               url(r'^classes/example/json$', views.get_time_series_classes_json, {'skip_example': False},
                   'timeseries_classes_json_example'),
               url(r'^min_max/json$', views.get_min_max_json, {}, 'timeseries_min_max_json'),
               url(r'^values/json$', views.get_values_json, {'packed': False}, 'timeseries_values_json'),
               url(r'^values/flight/json$', views.get_flight_values_json, {'packed': False}, 'timeseries_flight_values_json'),
               url(r'^values/flight/time/json$', views.get_flight_values_time_json, {'packed': False}, 'timeseries_flight_time_values_json'),
               url(r'^values/flight/downsample/json$', views.get_flight_values_json, {'packed': False, 'downsample': settings.XGDS_TIMESERIES_DOWNSAMPLE_DATA_SECONDS}, 'timeseries_flight_values_json'),
               url(r'^values/flight/time/downsample/json$', views.get_flight_values_time_json, {'packed': False, 'downsample': settings.XGDS_TIMESERIES_DOWNSAMPLE_DATA_SECONDS}, 'timeseries_flight_time_values_json'),
               url(r'^values/list/json$', views.get_values_json, {}, 'timeseries_values_list_json'),
               url(r'^values/flight/list/json$', views.get_flight_values_json, {}, 'timeseries_flight_values_list_json'),
               url(r'^values/flight/time/list/json$', views.get_flight_values_time_json, {}, 'timeseries_flight_values_time_list_json'),
               url(r'^channel_descriptions/json$', views.get_channel_descriptions_json, {}, 'timeseries_channel_descriptions_json'),
               ]
