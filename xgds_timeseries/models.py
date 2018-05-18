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


from django.db import models
from django.db.models import Min, Max


class Channel(object):
    """
    A channel represents a single value over time
    name
    units
    global min
    global max
    get data function
    label
    """
    def __init__(self, name, units=None, global_min=None, global_max=None, label=None):
        self.name = name
        self.units = units
        self.global_min = global_min
        self.global_max = global_max
        self.label = label

    def get_data(self, start_time, end_time, filter):
        pass

    def get_data_bounds(self, filter):
        """
        Returns the min and max value of the data collected defined by the filter for the given channels
        :param filter: The filter, such as the flight id or anything else
        :param filter: The channels, such as the flight id or anything else
        :return: a dictionary with {min: value, max: value}
        """
        pass


class TimeSeriesModelManager(models.Manager):
    """
    This is really a manager for many time series samples
    Mixin this class to have your model get the methods it needs to be an interactive, discoverable
    time series model
    A Time Series model represents one or more channels of data collected for a range of time
    Typically for a flight
    This represents data all collected by a single instrument

    get data for a range of time
    get min / max time per flight
    get min / max values over range of time

    get the channels
    """

    def __init__(self):
        super(TimeSeriesModelManager, self).__init__()
        self.channels = None
        self.channel_names = None
        self.name = 'data'

    def get_channel_names(self):
        """
        Get the channel names defined in the model
        :return: the list of channel names
        """
        if not self.channel_names:
            self.channel_names = self.model.get_channel_names()
        return self.channel_names

    def get_channels(self):
        if not self.channels:
            self.channels = []
            for channel_name in self.get_channel_names():
                self.channels.append(Channel(channel_name, label=channel_name.capitalize()))
        return self.channels

    def get_fields(self, channel_names=None):
        """
        Get the fields including the timestamp.  If channel_names are not included, all fields will be looked up.
        :param channel_names: the names of the channels to include
        :return: the list of field names, including timestamp.
        """
        if not channel_names:
            channel_names = self.get_channel_names()
        fields = ['timestamp']  # TODO maybe have the model define the field name for the timestamp
        fields.extend(channel_names)
        return fields

    def get_flight_data(self, flight_ids):
        """
        This returns a QuerySet including the full model instances for the specified flight ids.
        :param flight_ids: list of ids of flights (pks)
        :return: QuerySet with all of the model instances for the specified flight ids
        """
        return self.filter(flight_id__in=flight_ids)

    def get_flight_values(self, flight_ids, channel_names=None):
        """
        This HITS THE DATABASE to get a QuerySet of dictionaries which includes the timestamps and the
        values for the specified channels
        :param flight_ids: list of ids of flights (pks)
        :param channel_names: list of names of channels
        :return: A QuerySet of dictionaries of the values which include timestamp and selected channels
        """
        return self.get_flight_data(flight_ids).values(*self.get_fields(channel_names))

    def get_data(self, start_time=None, end_time=None, flight_ids=None, filter_dict=None):
        """
        This returns a QuerySet including the full model instances for the specified flight ids and other filters.
        :param start_time: The start time, timezone aware
        :param end_time: The end time, timezone aware
        :param flight_ids: the list of flight ids
        :param filter_dict: A dictionary of other filter terms
        :return: QuerySet with all of the model instances that match the filters
        """
        result = self
        if flight_ids:
            result = result.filter(flight_id__in=flight_ids)
        if start_time:
            result = result.filter(timestamp__gte=start_time)
        if end_time:
            result = result.filter(timestamp__lte=end_time)
        if filter_dict:
            result = result.filter(**filter_dict)
        return result

    def get_values(self, start_time=None, end_time=None, flight_ids=None, filter_dict=None, channel_names=None):
        """
        This HITS THE DATABASE to get a QuerySet of dictionaries which includes the timestamps and the
        values for the specified channels which match the filter
        :param start_time: The start time, timezone aware
        :param end_time: The end time, timezone aware
        :param flight_ids: the list of flight ids
        :param filter_dict: A dictionary of other filter terms
        :param channel_names: list of names of channels
        :return: A QuerySet of dictionaries of the values which include timestamp and selected channels
        """
        return self.get_data(start_time, end_time, flight_ids, filter_dict).values(*self.get_fields(channel_names))

    def get_bounds(self, start_time=None, end_time=None, flight_ids=None, filter_dict=None, channel_names=None):
        """
        This HITS THE DATABASE to get a dictionary of min/max values for the channels.  Timestamp is always provided.
        :param start_time: The start time, timezone aware
        :param end_time: The end time, timezone aware
        :param flight_ids: the list of flight ids
        :param filter_dict: A dictionary of other filter terms
        :param channel_names: list of names of channels
        :return: A dictionary
        """
        filtered_data = self.get_data(start_time, end_time, flight_ids, filter_dict)
        fields = self.get_fields(channel_names)
        result = {}
        for field in fields:
            result[field] = {'min': filtered_data.aggregate(Min(field)),
                             'max': filtered_data.aggregate(Max(field))}
        return result


class TimeSeriesMixin(models.Model):

    objects = TimeSeriesModelManager()

    @classmethod
    def get_channel_names(cls):
        """
        You must override this method
        :return: a list of the fields which are the named channels for this model
        """
        pass

    class Meta:
        abstract = True
