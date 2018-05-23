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

# TODO support number of samples so that we can express how many samples, or what interval of data we are looking for
# to limit the number of results we get


class ChannelDescription(object):
    """
    A Channel Description is used by a Time Series Model to describe each channel.
    """

    def __init__(self, label, units=None, global_min=None, global_max=None, interval=None):
        """
        :param label: The label will be shown with plots in the UI
        :param units: The units for the channel, ie meter
        :param global_min: The global minimum
        :param global_max: The global maximum
        :param interval: The expected time interval between samples in seconds
        """
        self.label = label
        self.units = units
        self.global_min = global_min
        self.global_max = global_max
        self.interval = interval


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
        self.time_field_name = None
        self.name = 'data'

    def get_time_field_name(self):
        """
        Get the name of the time field defined in the model
        :return: the name of the time field
        """
        if not self.time_field_name:
            self.time_field_name = self.model.get_time_field_name()
        return self.time_field_name
    
    def get_channel_names(self):
        """
        Get the channel names defined in the model
        :return: the list of channel names
        """
        if not self.channel_names:
            self.channel_names = self.model.get_channel_names()
        return self.channel_names

    def get_fields(self, channel_names=None):
        """
        Get the fields including the timestamp.  If channel_names are not included, all fields will be looked up.
        :param channel_names: the names of the channels to include
        :return: the list of field names, including timestamp.
        """
        if not channel_names:
            channel_names = self.get_channel_names()
        fields = [self.get_time_field_name()]
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
            filter_dict = {'%s__gte'% self.get_time_field_name():start_time}
            result = result.filter(**filter_dict)
        if end_time:
            filter_dict = {'%s__lte'% self.get_time_field_name():end_time}
            result = result.filter(**filter_dict)
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

    def get_min_max(self, start_time=None, end_time=None, flight_ids=None, filter_dict=None, channel_names=None):
        """
        This HITS THE DATABASE to get a dictionary of min/max values for the channels.  Timestamp is always provided.
        :param start_time: The start time, timezone aware
        :param end_time: The end time, timezone aware
        :param flight_ids: the list of flight ids
        :param filter_dict: A dictionary of other filter terms
        :param channel_names: list of names of channels
        :return @dictionary: A dictionary, or None
        """
        filtered_data = self.get_data(start_time, end_time, flight_ids, filter_dict)
        if not filtered_data.exists():
            return None
        fields = self.get_fields(channel_names)
        result = {}
        for field in fields:
            result[field] = {'min': filtered_data.aggregate(Min(field))['%s__min' % field],
                             'max': filtered_data.aggregate(Max(field))['%s__max' % field]}
        return result


class TimeSeriesModel(models.Model):

    objects = TimeSeriesModelManager()
    channel_descriptions = {}

    @classmethod
    def get_channel_description(cls, channel_name):
        """
        You must override this method
        :param channel_name: The name of the channel for which you want a description
        :return: a dictionary of useful things
        """
        try:
            return {channel_name: cls.channel_descriptions[channel_name]}
        except:
            return None

    @classmethod
    def get_channel_descriptions(cls):
        """
        You must override this method
        :param channel_name: The name of the channel for which you want a description
        :return: a dictionary of useful things
        """
        return cls.channel_descriptions


    @classmethod
    def get_channel_names(cls):
        """
        You must override this method
        :return: a list of the fields which are the named channels for this model
        """
        pass

    @classmethod
    def get_time_field_name(cls):
        """
        Override this method if the time field is not named timestamp
        :return:
        """
        return 'timestamp'

    class Meta:
        abstract = True


class TimeSeriesExample(TimeSeriesModel):
    """
    This is an auto-generated Django model created from a
    YAML specifications using ./apps/xgds_core/importer/yamlModelBuilder.py
    and YAML file ./apps/xgds_timeseries/test_data/TimeSeries_Example.yaml
    """

    timestamp = models.DateTimeField(db_index=True, null=False, blank=False)
    temperature = models.FloatField(null=True, blank=True)
    pressure = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    flight = models.ForeignKey('xgds_core.Flight', on_delete=models.SET_NULL, blank=True, null=True)

    channel_descriptions = {
                            'temperature': ChannelDescription('Temp', units='C', global_min=0.000000, global_max=45.000000),
                            'pressure': ChannelDescription('Pressure'),
                            'humidity': ChannelDescription('Humidity', global_min=0.000000, global_max=100.000000),
                            }

    @classmethod
    def get_channel_names(cls):
        return ['temperature', 'pressure', 'humidity', ]

