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
        """
        result = views.get_time_series_classes(skip_example=False)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertIn('xgds_timeseries.TimeSeriesExample', result)

    def test_get_timeseries_classes_json(self):
        """
        Test getting the timeseries classes as a json response
        """
        response = self.client.get(reverse('timeseries_classes_json'), kwargs={'skip_example':False})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        content = response.content
        self.assertIsNotNone(content)
        self.assertIn('xgds_timeseries.TimeSeriesExample', content)

    def is_good_json_response(self, response, is_list=False):
        """
        Test that a json response is good, and return its content as a dict
        :param response:
        """
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        string_content = response.content
        self.assertIsNotNone(string_content)
        content = json.loads(string_content)
        if not is_list:
            self.assertIsInstance(content, dict)
        else:
            self.assertIsInstance(content, list)
        return content

    def test_get_all_channel_descriptions(self):
        """
        Test getting all the channel descriptions for the example, should contain value
        """
        response = self.client.post(reverse('timeseries_channel_descriptions_json'), {'model_name':'xgds_timeseries.TimeSeriesExample'})
        content = self.is_good_json_response(response)
        self.assertIn('value', content)
        value = content['value']
        self.assertEqual(value['units'], 'meters')
        self.assertEqual(value['global_max'], 100)
        self.assertEqual(value['global_min'], 0)
        self.assertEqual(value['label'], 'Value')

    def test_get_value_channel_descriptions(self):
        """
        Test getting all the channel descriptions for the example, value only, should contain value
        """
        response = self.client.post(reverse('timeseries_channel_descriptions_json'), {'model_name':'xgds_timeseries.TimeSeriesExample', 'channel_name':'value'})
        content = self.is_good_json_response(response)
        self.assertIn('value', content)
        value = content['value']
        self.assertEqual(value['units'], 'meters')
        self.assertEqual(value['global_max'], 100)
        self.assertEqual(value['global_min'], 0)
        self.assertEqual(value['label'], 'Value')

    def test_get_value_channel_descriptions_bad_channel_name(self):
        """
        Test getting all the channel descriptions for the example, pass bad channel name,
        should be 204.
        """
        response = self.client.post(reverse('timeseries_channel_descriptions_json'),
                                    {'model_name': 'xgds_timeseries.TimeSeriesExample', 'channel_name': 'error'})
        self.assertEqual(response.status_code, 204)

    def test_get_channel_descriptions_bad_model(self):
        """
        Test getting all the channel descriptions for the example, pass bad channel name,
        should be 405.
        """
        response = self.client.post(reverse('timeseries_channel_descriptions_json'),
                                    {'model_name': 'bad.error'})
        self.assertEqual(response.status_code, 405)

    def test_get_min_max(self):
        """
        Test getting the min and max values with a good filter
        """
        response = self.client.post(reverse('timeseries_min_max_json'), self.post_dict)
        content = self.is_good_json_response(response)

        self.assertIn('timestamp', content)
        timestamp_dict = content['timestamp']
        self.assertEqual(timestamp_dict["max"], "2017-11-10T23:26:59.594000+00:00")
        self.assertEqual(timestamp_dict["min"], "2017-11-10T23:15:33.487000+00:00")

        self.assertIn('value', content)
        value_dict = content['value']
        self.assertEqual(value_dict["max"], 4.1)
        self.assertEqual(value_dict["min"], 1.05)

    def test_get_min_max_none(self):
        """
        Test getting the min and max values with a bad filter
        """
        response = self.client.post(reverse('timeseries_min_max_json'),
                                    {'model_name': 'xgds_timeseries.TimeSeriesExample',
                                     'flight_ids': [1, 2, 3]})
        self.assertEqual(response.status_code, 204)

    def test_get_values_all(self):
        """
        Test getting all the values
        """
        response = self.client.post(reverse('timeseries_values_json'), self.post_dict)
        content = self.is_good_json_response(response, is_list=True)
        self.assertIsNotNone(content)
        self.assertEqual(len(content), 687)
        first = content[0]
        self.assertEqual(first['timestamp'], '2017-11-10T23:15:33.487000+00:00')
        self.assertEqual(first['value'], 1.2)


    def test_get_values_filter(self):
        """
        Test getting filtered values
        """
        response = self.client.post(reverse('timeseries_values_json'),
                                    {'model_name': 'xgds_timeseries.TimeSeriesExample',
                                     'filter': '{"value__gte":1.2, "value__lte":1.8}' })
        content = self.is_good_json_response(response, is_list=True)
        self.assertIsNotNone(content)
        self.assertEqual(len(content), 679)


    def test_get_values_none(self):
        """
        Test get no values because bad query
        :return:
        """
        response = self.client.post(reverse('timeseries_values_json'),
                                            {'model_name': 'xgds_timeseries.TimeSeriesExample',
                                            'filter': '{"value__gte":300}'})
        self.assertEqual(response.status_code, 204)

    def test_get_values_error(self):
        response = self.client.post(reverse('timeseries_values_json'),
                                    {'model_name': 'garbage'})
        self.assertEqual(response.status_code, 405)


