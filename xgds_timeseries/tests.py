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
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden, Http404, JsonResponse


from xgds_timeseries import views
from xgds_timeseries.models import TimeSeriesExample


class xgds_timeseriesTest(TestCase):
    """
    Tests for xgds_timeseries
    """
    fixtures = ['timeseries_test_fixture.json']

    post_dict = {'model_name': 'xgds_timeseries.TimeSeriesExample',
                 'channel_names': ['value'],
                 'flight_ids': [22],
                 # 'start_time': '2017-11-10T23:15:33.487643Z',
                 # 'end_time': '2017-11-10T23:26:59.594971Z',
                 # 'filter': '{"value__gte":1.2}'
                 }

    def test_get_timeseries_classes(self):
        """
        Test getting the timeseries classes including the example one
        :return:
        """
        result = views.get_time_series_classes(skip_example=False)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertIn('xgds_timeseries.TimeSeriesExample', result)
        pass

    def test_get_timeseries_classes_json(self):
        """
        Test getting the timeseries classes as a json response
        :return:
        """
        response = self.client.get(reverse('timeseries_classes_json'), kwargs={'skip_example':False})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        content = response.content
        self.assertIsNotNone(content)
        self.assertIn('xgds_timeseries.TimeSeriesExample', content)
        pass

    def test_unravel_post(self):
        """
        Test unraveling the post data into a PostData class
        :return:
        """
        # post_data = views.unravel_post(self.post_dict)
        # self.assertIsNotNone(post_data)
        # self.assertEqual(post_data.model, TimeSeriesExample)
        # self.assertEqual(post_data.channel_names, self.post_dict['channel_names'])
        # self.assertEqual(post_data.start_time, dateparser(self.post_dict['start_time']))
        # self.assertEqual(post_data.end_time, dateparser(self.post_dict['end_time']))
        # self.assertEqual(post_data.filter_dict, {'value__gte':8.12})
        pass

    def test_get_min_max(self):
        response = self.client.post(reverse('timeseries_min_max_json'), self.post_dict)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        string_content = response.content
        self.assertIsNotNone(string_content)
        content = json.loads(string_content)
        self.assertIsInstance(content, dict)

        self.assertIn('timestamp', content)
        timestamp_dict = content['timestamp']
        self.assertEqual(timestamp_dict["max"], "2017-11-10T23:26:59.594000+00:00")
        self.assertEqual(timestamp_dict["min"], "2017-11-10T23:15:33.487000+00:00")

        self.assertIn('value', content)
        value_dict = content['value']
        self.assertEqual(value_dict["max"], 4.1)
        self.assertEqual(value_dict["min"], 1.05)
        pass

    def test_get_min_max_none(self):
        response = self.client.post(reverse('timeseries_min_max_json'),
                                    {'model_name': 'xgds_timeseries.TimeSeriesExample',
                                     'flight_ids': [1, 2, 3]})
        self.assertEqual(response.status_code, 204)
        pass

