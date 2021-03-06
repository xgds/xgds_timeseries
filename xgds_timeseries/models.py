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

import datetime
from django.conf import settings
from django.db import models
from django.db.models import Min, Max
from django.utils import timezone


from xgds_core.models import downsample_queryset, BroadcastMixin


class ChannelDescription(object):
    """
    A Channel Description is used by a Time Series Model to describe each channel.
    """

    def __init__(self, label, units=None, global_min=None, global_max=None,
                 interval=settings.XGDS_TIMESERIES_DOWNSAMPLE_DATA_SECONDS):
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

    def __repr__(self):
        return '%s: [units: %s, gmin: %s, gmax: %s, interval: %s]' % (self.label, self.units, self.global_min, self.global_max, self.interval)

    def __str__(self):
        return self.__repr__()


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
        fields = ['pk', self.get_time_field_name()]
        fields.extend(channel_names)
        return fields

    def get_flight_data(self, flight_ids, downsample=0):
        """
        This returns a QuerySet including the full model instances for the specified flight ids.
        :param flight_ids: list of ids of flights (pks)
        :param downsample: number of seconds to skip between data samples
        :return: QuerySet with all of the model instances for the specified flight ids
        """
        result = self.filter(flight_id__in=flight_ids)
        result = downsample_queryset(result, downsample, self.model.get_time_field_name())
        return result

    def get_flight_values(self, flight_ids, channel_names=None, downsample=0):
        """
        This HITS THE DATABASE to get a QuerySet of dictionaries which includes the timestamps and the
        values for the specified channels
        :param flight_ids: list of ids of flights (pks)
        :param channel_names: list of names of channels
        :param downsample: number of seconds to skip between data samples
        :return: A QuerySet of dictionaries of the values which include timestamp and selected channels
        """
        return self.get_flight_data(flight_ids, downsample).values(*self.get_fields(channel_names))

    def get_dynamic_flight_values(self, flight_ids, channel_names=None, dynamic_value=None, dynamic_separator=None,
                                  downsample=0):
        """

        :param flight_ids:
        :param channel_names:
        :param dynamic_value:
        :param dynamic_separator:
        :param downsample: number of seconds to skip between data samples
        :return:
        """
        timestamps = {}
        query = self.get_flight_data(flight_ids, downsample)
        for q in query:
            if q.timestamp not in timestamps:
                timestamps[q.timestamp] = {
                    "timestamp": q.timestamp,
                    getattr(q, dynamic_separator): getattr(q, dynamic_value),
                }
            else:
                timestamps[q.timestamp][getattr(q, dynamic_separator)] = getattr(q, dynamic_value)
        timestamps_keys = sorted(list(timestamps.keys()))
        timestamps_as_list = [timestamps[x] for x in timestamps_keys]
        return timestamps_as_list

    def get_data(self, start_time=None, end_time=None, flight_ids=None, filter_dict=None, downsample=0):
        """
        This returns a QuerySet including the full model instances for the specified flight ids and other filters.
        :param start_time: The start time, timezone aware
        :param end_time: The end time, timezone aware
        :param flight_ids: the list of flight ids
        :param filter_dict: A dictionary of other filter terms
        :param downsample: Number of seconds to downsample or skip when filtering data
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

        result = downsample_queryset(result, downsample, self.model.get_time_field_name())

        return result

    def get_dynamic_values(self, start_time=None, end_time=None, flight_ids=None, filter_dict=None,
                           channel_names=None, downsample=0):
        """

        :param start_time:
        :param end_time:
        :param flight_ids:
        :param filter_dict:
        :param channel_names:
        :param downsample:
        :return:
        """
        timestamps = {}
        query = self.get_data(start_time, end_time, flight_ids, filter_dict, downsample)
        for q in query:
            if q.time_stamp not in timestamps:
                timestamps[q.time_stamp] = {
                    "time_stamp": q.time_stamp,
                    getattr(q, q.dynamic_separator): getattr(q, q.dynamic_value),
                }
            else:
                timestamps[q.time_stamp][getattr(q, q.dynamic_separator)] = getattr(q, q.dynamic_value)
        timestamps_keys = sorted(list(timestamps.keys()))
        timestamps_as_list = [timestamps[x] for x in timestamps_keys]
        return timestamps_as_list

    def get_values(self, start_time=None, end_time=None, flight_ids=None, filter_dict=None, channel_names=None,
                   downsample=0):
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
        return self.get_data(start_time, end_time, flight_ids, filter_dict, downsample).values(*self.get_fields(channel_names))

    def get_data_at_time(self, time, flight_ids=None, filter_dict=None):
        """
        This returns a QuerySet including the full model instances for the specified flight ids and other filters.
        The data will be the closest value at this time or before,
        given this setting: GEOCAM_TRACK_CLOSEST_POSITION_MAX_DIFFERENCE_SECONDS
        Unless this is a stateful model, in which case it will take the previous value for the flight
        :param time: The time, timezone aware
        :param flight_ids: the list of flight ids
        :param filter_dict: A dictionary of other filter terms
        :return: QuerySet with all of the model instances that match the filters
        """
        result = self
        if not time:
            raise Exception('Time is required')
        if flight_ids:
            result = result.filter(flight_id__in=flight_ids)
        if self.model.stateful:
            filter_dict = {'%s__lte' % self.get_time_field_name(): time}
        else:
            # time must be gte the time passed in less the delta
            min_time = time - datetime.timedelta(seconds=settings.GEOCAM_TRACK_CLOSEST_POSITION_MAX_DIFFERENCE_SECONDS)
            filter_dict = {'%s__gte' % self.get_time_field_name(): min_time,
                           '%s__lte' % self.get_time_field_name(): time}

        result = result.filter(**filter_dict)
        if not self.model.stateful:
            result = result.order_by('-%s' % self.get_time_field_name())
        return result

    def get_values_at_time(self, time=None, flight_ids=None, filter_dict=None, channel_names=None):
        """
        This HITS THE DATABASE to get a QuerySet of dictionaries which includes the timestamps and the
        values for the specified channels which match the filter
        The data will be the closest value at this time or before,
        given this setting: GEOCAM_TRACK_CLOSEST_POSITION_MAX_DIFFERENCE_SECONDS
        Unless this is a stateful model, in which case it will take the previous value for the flight
        :param time: The time, timezone aware
        :param flight_ids: the list of flight ids
        :param filter_dict: A dictionary of other filter terms
        :param channel_names: list of names of channels
        :return: A QuerySet of dictionaries of the values which include timestamp and selected channels
        """
        return self.get_data_at_time(time, flight_ids, filter_dict).values(*self.get_fields(channel_names))

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

    def get_dynamic_min_max(self, start_time=None, end_time=None, flight_ids=None, filter_dict=None, channel_names=None,
                            dynamic_value=None, dynamic_separator=None):

        def dynamic_aggregate(field_name, data, func):
            custom_data = [getattr(x, dynamic_value) for x in data if getattr(x, dynamic_separator) == field_name]
            return func(custom_data)

        filtered_data = self.get_data(start_time, end_time, flight_ids, filter_dict)
        if not filtered_data.exists():
            return None

        result = {}
        for field in self.get_fields(channel_names):
            if field in channel_names:
                result[field] = {
                    'min': dynamic_aggregate(field, filtered_data, min),
                    'max': dynamic_aggregate(field, filtered_data, max),
                }
            else:
                result[field] = {
                    'min': filtered_data.aggregate(Min(field))['%s__min' % field],
                    'max': filtered_data.aggregate(Max(field))['%s__max' % field],
                }
        return result


class TimeSeriesModel(models.Model, BroadcastMixin):

    creation_time = models.DateTimeField(blank=True, default=timezone.now, editable=False, db_index=True)

    objects = TimeSeriesModelManager()
    channel_descriptions = {}

    # If your model is stateful, ie has data coming in itermittantly that indicates state, override stateful with true.
    stateful = False

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
        **IMPORTANT** if you override this be sure to change the meta ordering in your class
        :return: the name of the field
        """
        return 'timestamp'

    def to_dict(self):
        time_field_name = self.get_time_field_name()
        returned_dict = {time_field_name: getattr(self, time_field_name)}
        for name in self.get_channel_names():
            returned_dict[name] = getattr(self, name)
        return returned_dict

    class Meta:
        abstract = True
        ordering = ['timestamp']


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

    title = 'Time Series Example'

    channel_descriptions = {
                            'temperature': ChannelDescription('Temp', units='C', global_min=0.000000, global_max=45.000000),
                            'pressure': ChannelDescription('Pressure'),
                            'humidity': ChannelDescription('Humidity', global_min=0.000000, global_max=100.000000),
                            }

    @classmethod
    def get_channel_names(cls):
        return ['temperature', 'pressure', 'humidity', ]

