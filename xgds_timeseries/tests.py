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
from django.db import models
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
                 'channel_names': ['temperature', 'pressure'],
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
        response = self.client.get(reverse('timeseries_classes_json_example'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        content = response.content
        self.assertIsNotNone(content)
        self.assertIn('xgds_timeseries.TimeSeriesExample', content)

    def test_get_timeseries_classes_and_titles(self):
        """
        Test getting the timeseries classes and titles including the example one
        """
        result = views.get_time_series_classes_metadata(skip_example=False)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        tsExample = None
        for entry in result:
            if entry['model_name'] == 'xgds_timeseries.TimeSeriesExample':
                tsExample = entry
                break
        self.assertIsNotNone(tsExample)
        self.assertEqual(tsExample['title'], 'Time Series Example')

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
        self.assertIn('temperature', content)
        temperature = content['temperature']
        self.assertEqual(temperature['units'], 'C')
        self.assertEqual(temperature['global_max'], 45)
        self.assertEqual(temperature['global_min'], 0)
        self.assertEqual(temperature['label'], 'Temp')

    def test_get_humidity_channel_descriptions(self):
        """
        Test getting the channel descriptions for the example, humidity only, should contain humidity
        """
        response = self.client.post(reverse('timeseries_channel_descriptions_json'), {'model_name':'xgds_timeseries.TimeSeriesExample', 'channel_name':'humidity'})
        content = self.is_good_json_response(response)
        self.assertIn('humidity', content)
        humidity = content['humidity']
        self.assertIsNone(humidity['units'])
        self.assertEqual(humidity['global_max'], 100)
        self.assertEqual(humidity['global_min'], 0)
        self.assertEqual(humidity['label'], 'Humidity')

    def test_get_channel_descriptions_bad_channel_name(self):
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

    def test_get_channel_descriptions_no_post(self):
        """
        Test getting the channel descriptions with a get
        """
        response = self.client.get(reverse('timeseries_channel_descriptions_json'))
        self.assertEqual(response.status_code, 403)

    def test_get_min_max(self):
        """
        Test getting the min and max values with a good filter, including temperature and pressure
        """
        response = self.client.post(reverse('timeseries_min_max_json'), self.post_dict)
        content = self.is_good_json_response(response)

        self.assertIn('timestamp', content)
        timestamp_dict = content['timestamp']
        self.assertEqual(timestamp_dict["max"], "2017-11-10T23:17:26.663000+00:00")
        self.assertEqual(timestamp_dict["min"], "2017-11-10T23:15:01.284000+00:00")

        self.assertIn('temperature', content)
        temp_dict = content['temperature']
        self.assertEqual(temp_dict["max"], 8.15)
        self.assertEqual(temp_dict["min"], 8.12)

        self.assertIn('pressure', content)
        pressure_dict = content['pressure']
        self.assertEqual(pressure_dict["max"], 3.98)
        self.assertEqual(pressure_dict["min"], 1.26)

        self.assertNotIn('humidity', content)

    def test_get_min_max_time_bounds(self):
        """
        Test getting the min and max values with a good filter, including temp press humidity but for
        a bounded time
        """
        response = self.client.post(reverse('timeseries_min_max_json'),
                                    {'model_name': 'xgds_timeseries.TimeSeriesExample',
                                     'flight_ids': [22],
                                     'start_time': '2017-11-10T23:16:17.673Z',
                                     'end_time': '2017-11-10T23:16:29.528Z'})
        content = self.is_good_json_response(response)

        self.assertIn('timestamp', content)
        timestamp_dict = content['timestamp']
        self.assertEqual(timestamp_dict["max"], "2017-11-10T23:16:29.528000+00:00")
        self.assertEqual(timestamp_dict["min"], "2017-11-10T23:16:17.673000+00:00")

        self.assertIn('temperature', content)
        temp_dict = content['temperature']
        self.assertEqual(temp_dict["max"], 8.14)
        self.assertEqual(temp_dict["min"], 8.13)

        self.assertIn('pressure', content)
        pressure_dict = content['pressure']
        self.assertEqual(pressure_dict["max"], 3.98)
        self.assertEqual(pressure_dict["min"], 3.98)

        self.assertIn('humidity', content)
        humidity_dict = content['humidity']
        self.assertEqual(humidity_dict["max"], 45)
        self.assertEqual(humidity_dict["min"], 45)

    def test_get_min_max_none(self):
        """
        Test getting the min and max values with a bad filter
        """
        response = self.client.post(reverse('timeseries_min_max_json'),
                                    {'model_name': 'xgds_timeseries.TimeSeriesExample',
                                     'flight_ids': [1, 2, 3]})
        self.assertEqual(response.status_code, 204)

    def test_get_min_max_bad_model(self):
        """
        Test getting the min and max values with a bad model
        """
        response = self.client.post(reverse('timeseries_min_max_json'),
                                    {'model_name': 'xgds_timeseries.Mistake'})
        self.assertEqual(response.status_code, 405)

    def test_get_min_max_no_post(self):
        """
        Test getting the min and max values with a get
        """
        response = self.client.get(reverse('timeseries_min_max_json'))
        self.assertEqual(response.status_code, 403)

    def test_get_values_all(self):
        """
        Test getting all the values
        """
        response = self.client.post(reverse('timeseries_values_json'), self.post_dict)
        content = self.is_good_json_response(response, is_list=True)
        self.assertIsNotNone(content)
        self.assertEqual(len(content), 100)
        first = content[0]
        self.assertEqual(first['pk'], 1375)
        self.assertEqual(first['timestamp'], '2017-11-10T23:15:01.284000+00:00')
        self.assertEqual(first['temperature'], 8.13)
        self.assertEqual(first['pressure'], 3.98)

    def test_get_values_list_all(self):
        """
        Test getting all the values as a list
        """
        response = self.client.post(reverse('timeseries_values_list_json'), self.post_dict)
        content = self.is_good_json_response(response, is_list=True)
        self.assertIsNotNone(content)
        self.assertEqual(len(content), 100)
        first = content[0]
        self.assertEqual(first[0], 1375)
        self.assertEqual(first[1], '2017-11-10T23:15:01.284000+00:00')
        self.assertEqual(first[2], 8.13)
        self.assertEqual(first[3], 3.98)

    def test_get_values_filter(self):
        """
        Test getting filtered values
        """
        response = self.client.post(reverse('timeseries_values_json'),
                                    {'model_name': 'xgds_timeseries.TimeSeriesExample',
                                     'filter': '{"humidity__gte":50, "humidity__lte":99}' })
        content = self.is_good_json_response(response, is_list=True)
        self.assertIsNotNone(content)
        self.assertEqual(len(content), 2)

        first = content[0]
        second = content[1]
        self.assertEqual(first['timestamp'], '2017-11-10T23:15:19.062000+00:00')
        self.assertEqual(first['temperature'], 8.13)
        self.assertEqual(first['pressure'], 3.98)
        self.assertEqual(first['humidity'], 99)

        self.assertEqual(second['timestamp'], '2017-11-10T23:15:27.758000+00:00')
        self.assertEqual(second['temperature'], 8.14)
        self.assertEqual(second['pressure'], 3.98)
        self.assertEqual(second['humidity'], 99)

    def test_get_values_none(self):
        """
        Test get no values because bad query
        """
        response = self.client.post(reverse('timeseries_values_json'),
                                            {'model_name': 'xgds_timeseries.TimeSeriesExample',
                                            'filter': '{"temperature__gte":300}'})
        self.assertEqual(response.status_code, 204)

    def test_get_values_error(self):
        """
        Test get no values because bad model name
        """
        response = self.client.post(reverse('timeseries_values_json'),
                                    {'model_name': 'garbage'})
        self.assertEqual(response.status_code, 405)

    def test_get_values_no_post(self):
        """
        Test getting the values with a get
        """
        response = self.client.get(reverse('timeseries_values_json'))
        self.assertEqual(response.status_code, 403)

    def test_get_flight_values_all(self):
        """
        Test getting all the values
        """
        response = self.client.post(reverse('timeseries_flight_values_json'), self.post_dict)
        content = self.is_good_json_response(response, is_list=True)
        self.assertIsNotNone(content)
        self.assertEqual(len(content), 100)
        first = content[0]
        self.assertEqual(first['timestamp'], '2017-11-10T23:15:01.284000+00:00')
        self.assertEqual(first['temperature'], 8.13)
        self.assertEqual(first['pressure'], 3.98)

    def test_get_packed_flight_values_all(self):
        """
        Test getting all the values, as a list of lists
        """
        response = self.client.post(reverse('timeseries_flight_values_list_json'), self.post_dict)
        content = self.is_good_json_response(response, is_list=True)
        self.assertIsNotNone(content)
        self.assertEqual(len(content), 100)
        first = content[0]
        self.assertEqual(first[0], 1375)
        self.assertEqual(first[1], '2017-11-10T23:15:01.284000+00:00')
        self.assertEqual(first[2], 8.13)
        self.assertEqual(first[3], 3.98)

    def test_get_flight_values_none(self):
        """
        Test get no values because bad flight ids
        """
        response = self.client.post(reverse('timeseries_flight_values_json'),
                                            {'model_name': 'xgds_timeseries.TimeSeriesExample',
                                            'flight_ids': [55, 42]})
        self.assertEqual(response.status_code, 204)

    def test_get_flight_values_error(self):
        """
        Test get no values because bad model name
        """
        response = self.client.post(reverse('timeseries_flight_values_json'),
                                    {'model_name': 'garbage'})
        self.assertEqual(response.status_code, 405)

    def test_get_flight_values_no_post(self):
        """
        Test getting the flight values with a get
        """
        response = self.client.get(reverse('timeseries_flight_values_json'))
        self.assertEqual(response.status_code, 403)

    def test_get_model_flight_data(self):
        """
        Test directly getting the flight data
        """
        result = TimeSeriesExample.objects.get_flight_data([22])
        self.assertIsNotNone(result)
        self.assertIsInstance(result, models.QuerySet)
        self.assertEqual(result.exists(), True)
        self.assertEqual(result.count(), 100)

    def test_get_model_flight_data_bad_flight_ids(self):
        """
        Test directly getting the flight data with bad flight ids
        """
        result = TimeSeriesExample.objects.get_flight_data([1])
        self.assertIsNotNone(result)
        self.assertIsInstance(result, models.QuerySet)
        self.assertEqual(result.count(), 0)
        self.assertEqual(result.exists(), False)

    def test_get_version(self):
        from xgds_timeseries import get_version
        result = get_version()
        self.assertEqual(result, '0.1')


