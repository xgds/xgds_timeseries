//__BEGIN_LICENSE__
//Copyright (c) 2015, United States Government, as represented by the
//Administrator of the National Aeronautics and Space Administration.
//All rights reserved.

//The xGDS platform is licensed under the Apache License, Version 2.0
//(the "License"); you may not use this file except in compliance with the License.
//You may obtain a copy of the License at
//http://www.apache.org/licenses/LICENSE-2.0.

//Unless required by applicable law or agreed to in writing, software distributed
//under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
//CONDITIONS OF ANY KIND, either express or implied. See the License for the
//specific language governing permissions and limitations under the License.
//__END_LICENSE__

BLANKS = '';

$(function() {
    app.views = app.views || {};
    app.models = app.models || {};

    (function(models) {

        models.ChannelDescriptionModel = Backbone.Model.extend({

            defaults: {
                'label': null,
                'units': null,
                'global_min': null,
                'global_max': null,
                'min': null,
                'max': null,
                'interval': 1,
                'lineColor':     'blue',
                'usesPosition':    false,
                //'update': UPDATE_ON.UpdatePlanDuration,
                'inverse': false,
                'visible': true
            },

            initialize: function(data) {
                this.set('label', data['label']);
                this.set('units', data['units']);
                this.set('global_min', data['global_min']);
                this.set('global_max', data['global_max']);
                if ('interval' in data && !_.isNull(data.interval)) {
                    this.set('interval', data['interval']);
                }
                this.set('data', []);
            },

            getDataValues: function(startMoment, endMoment, intervalSeconds) {
                // TODO does not yet use start end or interval
                return this.data;
            },

            getLineColor: function() {
                return this.get('lineColor');
            },

            getLabel: function() {
                return this.get('label');
            }

        });

        var PlotPlayback = {
                lastUpdate: undefined,
                invalid: false,
                initialized: false,
                initialize: function() {
                    if (this.initialized){
                        return;
                    }
                    this.initialized = true;
                },
                doSetTime: function(currentTime){
                    if (currentTime === undefined){
                        return;
                    }
                    this.lastUpdate = moment(currentTime);
                    app.vent.trigger('updateTimeseriesTime:' + this.model_name, currentTime);
                },
                start: function(currentTime){
                    this.doSetTime(currentTime);
                },
                update: function(currentTime){
                    if (this.lastUpdate === undefined){
                        this.doSetTime(currentTime);
                        return;
                    }
                    var delta = currentTime.diff(this.lastUpdate);
                    if (Math.abs(delta) >= 100) {
                        this.doSetTime(currentTime);
                    }
                },
                pause: function() {
                    // noop
                }
            };
        models.PlotModel = Backbone.Model.extend({
            initialized: false,
            skip_keys: ['timestamp','pk'],
            intervalSeconds: 1,
            cached_index: undefined,
            buildPlayback: function() {
                this.playback = _.clone(PlotPlayback);
                this.playback.model_name = this.model_name;
            },
            initialize: function(options) {
                this.postOptions = options;
                this.model_name = options.model_name;
                this.buildPlayback();
                if (this.channel_descriptions === undefined) {
                    this.getChannelDescriptions();
                } else {
                    this.loadData();
                }

                var _this = this;
                this.listenTo(app.vent, 'updateTimeseriesTime:' + this.model_name, function(currentTime) {
                    var index = _this.getPlotIndex(currentTime);
                    if (!_.isUndefined((index)) && index > -1){
                        _this.cached_index = index;
                    } else {
                        _this.cached_index = undefined;
                    }
                    app.vent.trigger('updateTimeseriesValue:' + _this.model_name, _this.cached_index);

                });
            },
            getChannelDescriptions: function() {
                $.ajax({
                    url: '/timeseries/channel_descriptions/json',
                    dataType: 'json',
                    type: 'POST',
                    data: this.postOptions,
                    success: $.proxy(function(data) {
                        if (_.isUndefined(data) || data.length === 0){
                            this.trigger('setMessage', "None found.");
                        } else {
                            this.channel_descriptions = {};
                            for (var channel in data){
                                var cd = new app.models.ChannelDescriptionModel(data[channel]);
                                this.channel_descriptions[channel] = cd;
                                this.intervalSeconds = cd.get('interval');
                                this.loadLegendCookie(channel);
                            }
                            this.getMinMax();
                        }
                    }, this),
                    error: $.proxy(function(data){
                        this.trigger('setMessage', "Channel descriptions failed.");
                    }, this)
                });
            },
            getMinMax: function() {
                $.ajax({
                    url: '/timeseries/min_max/json',
                    dataType: 'json',
                    type: 'POST',
                    data: this.postOptions,
                    success: $.proxy(function(data) {
                        if (_.isUndefined(data) || data.length === 0){
                            this.trigger('setMessage', "None found.");
                        } else {

                            for (var channel in data){
                                if (!this.skip_keys.includes(channel)) {
                                    this.channel_descriptions[channel].set('min', data[channel].min);
                                    this.channel_descriptions[channel].set('max', data[channel].max);
                                }
                            }
                            this.time_range = data['timestamp'];
                            this.time_range.duration = moment(this.time_range.max).diff(this.time_range.min, 'seconds');
                            this.time_range.start = moment(this.time_range.min);
                            this.loadData();
                        }
                    }, this),
                    error: $.proxy(function(data){
                        this.trigger('setMessage', "MinMax failed.");
                    }, this)
                });
            },
            loadLastFlightData: function() {
                // this only has to get called for stateful data, so that we at least have a pair of data values to draw a plot line.
                var _this = this;
                var options = Object.assign({}, this.postOptions);
                var flight_end_unix = undefined;

                if (!_.isUndefined(flight_end)) {  // this is defined right now in the html template top level
                    options.time = flight_end.format();
                    flight_end_unix = flight_end.valueOf();
                } else {
                    // can't do this function
                    this.initialized = true;
                    app.vent.trigger('data:loaded', this.postOptions.model_name);
                }

                $.ajax({
                    url: '/timeseries/values/flight/time/downsample/json',
                    dataType: 'json',
                    data: options,
                    type: 'POST',
                    success: $.proxy(function(data) {
                        if (_.isUndefined(data) || data.length === 0){
                            // this might be fine.  Just go on.
                            this.initialized = true;
                            app.vent.trigger('data:loaded', this.postOptions.model_name);
                        } else {
                            this.trigger('clearMessage');
                            _.each(data, function(data_block) {
                                var the_time = moment(data_block['timestamp']).valueOf();
                                _.each(Object.keys(this.channel_descriptions), function(field_name, index, list){
                                    var data_array = _this.channel_descriptions[field_name].get('data');
                                    var datum = data_block[field_name];
                                    // we looked up this data to see what was the value at the end time, if we got data back then it is to be used for this end time.
                                    data_array.push([flight_end_unix, datum]);
                                });
                            }, this);

                            this.initialized = true;
                            app.vent.trigger('data:loaded', this.postOptions.model_name);
                        }
                    }, this),
                    error: $.proxy(function(data){
                        this.setMessage("Search failed.");
                    }, this)
                });
            },
            loadData: function(){
                var _this = this;
                $.ajax({
                    url: '/timeseries/values/flight/downsample/json',
                    dataType: 'json',
                    data: this.postOptions,
                    type: 'POST',
                    success: $.proxy(function(data) {
                        if (_.isUndefined(data) || data.length === 0){
                            this.trigger('setMessage', "None found.");
                        } else {
                            this.trigger('clearMessage');
                            _.each(data, function(data_block) {
                                var the_time = moment(data_block['timestamp']).valueOf();
                                _.each(Object.keys(this.channel_descriptions), function(field_name, index, list){
                                    var data_array = _this.channel_descriptions[field_name].get('data');
                                    var datum = data_block[field_name]
                                    data_array.push([the_time, datum]);
                                });
                            }, this);

                            if ('flight_ids' in this.postOptions && this.postOptions['stateful'] == "true") {
                                // make sure we have the last data for the flight
                                _this.loadLastFlightData();
                            } else {
                                this.initialized = true;
                                playback.addListener(this.playback);
                                app.vent.trigger('data:loaded', this.postOptions.model_name);
                            }
                        }
                    }, this),
                    error: $.proxy(function(data){
                        this.trigger('setMessage', "Search failed.");
                    }, this)
                });
            },
            buildPlotDataArray: function() {
                if (_.isUndefined(this.plot_data_array)) {
                    this.plot_data_array = [];
                    _.each(Object.keys(this.channel_descriptions), function (channel) {
                        var cd = this.channel_descriptions[channel];
                        if (cd.get('visible')) {
                            var channel_dict = {label: cd.get('label'), data: cd.get('data'), channel: channel};
                            var color = cd.get('color');
                            if (!_.isUndefined(color)) {
                                channel_dict['color'] = color;
                            }
                            this.plot_data_array.push(channel_dict);
                        }
                    }, this);
                }
                return this.plot_data_array;
            },
            getPlotIndex: function(currentTime){
                if (!this.initialized) {
                    return;
                }

                var shouldUpdate = true;
                if (!_.isUndefined(this.lastDataIndexTime)) {
                    var timedeltaMS = Math.abs(this.lastDataIndexTime - currentTime);
                    if (timedeltaMS / 1000 < this.intervalSeconds) {
                        shouldUpdate = false;
                    }
                }

                if (shouldUpdate) {
                    var context = this;
                    var sampleData = this.buildPlotDataArray()[0].data;
                    var currentTimeValue = currentTime.valueOf();
                    var foundIndex = _.findIndex(sampleData, function(value){
                        var delta = Math.abs(currentTimeValue - value[0])/1000;
                        return delta < context.intervalSeconds;
                    });

                    if (foundIndex == -1) {
                        return undefined;
                    }
                    if (this.lastDataIndex !== foundIndex){
                        // now verify the actual time at that index
                        var testData = sampleData[foundIndex];
                        if (_.isUndefined(testData)) {
                            return undefined;
                        }
                        var testDiff = Math.abs((currentTime - testData[0])/1000)
                        if (testDiff > this.intervalSeconds) {
                            console.log('BOO bad time ' + testDiff);
                            //TODO find better time.  This may easily happen if we have data dropouts.
                            return undefined; // not sure what to do
                        }

                        this.lastDataIndex = foundIndex;
                        this.lastDataIndexTime = currentTime;
                    }
                }
                return this.lastDataIndex;
            },
            getCookieKey: function(channel) {
                return this.model_name + '.' + channel;
            },
            loadLegendCookie: function(channel) {
                var cookieKey = this.getCookieKey(channel);
                var cookieVisible = Cookies.get(cookieKey);
                var visible = true;
                if (!_.isUndefined(cookieVisible)){
                    visible = (cookieVisible == 'true');
                } else {
                    Cookies.set(cookieKey, visible);
                }
                this.channel_descriptions[channel].set('visible', visible);
                return visible;
            },
        })

    })(app.models);

    app.views.TimeseriesPlotView = Marionette.View.extend({

        plotOptions: {
            series: {
                lines: {show: true},
                points: {show: false}
            },
            clickable: true,
            grid: {
                backgroundColor: '#FFFFFF',
                hoverable: true,
                clickable: true,
                autoHighlight: true,
                margin: {
                    top: 5,
                    left: 0,
                    bottom: 5,
                    right: 0
                },
                axisMargin: 0,
                borderWidth: 1,
                borderColor: '#C0C0C0'
            },
            shadowSize: 0,
            zoom: {
                interactive: true
            },
            pan: {
                interactive: true
            },
            axisLabels: {
                show: true
            },
            yaxis: {
                ticks: 0 // this line removes the y ticks
            },
            xaxis: {
                mode: 'time',
                timeformat: DEFAULT_PLOT_TIME_FORMAT,
                timezone: getTimeZone(),
                reserveSpace: false
            },
            //yaxes: [],
            legend: {
                show: false
            }
        },
        template: '#plot_contents',
        initialize: function(options) {
            if (_.isEmpty(options)) {
                options = app.options.plotOptions;
            }

            this.model_name = options.model_name;
            this.title = options.title;
            if (!_.isUndefined(app.plot_models_initialized) && app.plot_models_initialized){
                this.model = app.plot_models[options.model_name];
            }

            this.model.on('clearMessage', this.clearMessage);
            this.model.on('setMessage', function(message) {this.setMessage(message);});

            if (this.plot != undefined){
                this.plot.destroy();
                this.plot = null;
            }

            this.listenTo(app.vent, 'updateTimeseriesValue:' + this.model_name, function(index) {
                if (!_.isUndefined((index)) && index > -1){
                    _this.selectData(index);
                } else {
                    _this.clearData();
                }
            });

        },
        clearMessage: function(msg){
            if (!_.isUndefined(this.$el)) {
                this.$el.find('#timeseries_message').html('');
            }
        },
        setMessage: function(msg){
            this.$el.find('#timeseries_message').html(msg);
        },
        showValue: function(x, y){
            var str = this.labels[0] + ": "+ x + "<br/>";
            xgds_timeseries.setMessage(str);
        },
        togglePlot(channel, visible){
            var cd = this.channel_descriptions[channel];
            if (cd.get('visible') != visible){
                cd.set('visible', visible);
                this.renderPlots();
            }
        },
        drawTitle: function() {
            this.$el.find("#plotTitle").html('&nbsp;&nbsp;&nbsp;<strong>' + this.title + '</strong>')
        },

        drawLegendLabels: function() {
            var context = this;
            var plotLegend = this.$el.find("#plotLegend");
            _.each(Object.keys(this.model.channel_descriptions), function(channel) {
                var cd = context.model.channel_descriptions[channel];
                var underChannel = channel.split(' ').join('_');

                var content = '<div id="' + underChannel + 'legend_div" class="d-sm-inline-flex flex-row" style="min-width:180px;">';
                content += '<label><input type="checkbox" id="' + underChannel + '_checkbox" value="' + channel +
                    '" style="display:inline-block;" class="mr-1"><span id="' + underChannel + '_label" style="color:' +
                    cd.get('color') + '">' + cd.get('label') + ':</span><span id="' + underChannel + '_value">' +
                    BLANKS + '</span>';
                if (cd.get('units') !== null) {
                    content += '<span id="\' + underChannel + \'_units">&nbsp;' + cd.get('units') + '</span>';
                }
                content += '</label></div>';
                plotLegend.append(content);

                var checkboxId = "#" + underChannel + "_checkbox";
                $(checkboxId).prop('checked', cd.get('visible'));

                $(checkboxId).change(function() {
                    var id = $(this).attr('id');
                    var checked = $(this).is(":checked");
                    Cookies.set(context.model.getCookieKey($(this).attr('value')), checked);
                    context.togglePlot($(this).attr('value'), checked);
                });

            });
        },

        clearData: function() {
            this.plot.unhighlight();
            _.each(Object.keys(this.model.channel_descriptions), function(key) {
                this.updateDataValue(key);
            }, this);
        },
        selectData: function(index) {
            if (this.plot != undefined){
                this.plot.unhighlight();
                var time = null;
                var context = this;
                _.each(this.plot.getData(), function(plotData, i) {
                    var channel = plotData.channel;
                    var value = null;
                    if (!_.isUndefined(channel)) {
                        var dataAtIndex = plotData.data[index];
                        if (!_.isUndefined(dataAtIndex)) {
                            context.plot.highlight(i, index);
                            time = dataAtIndex[0];
                            value = dataAtIndex[1];
                        }
                        context.updateDataValue(channel, value);
                    }
                });
                if (!_.isNull(time)) {
                    this.updateTimeValue(time);
                }
            }
        },
        updateDataValue: function(label, value){
            // show the value from the plot below the plot.
            var labelValue = ('#' + label + '_value');
            var labelValue = labelValue.split(' ').join('_');
            if (value != null && value != undefined){
                value = value.toFixed(2);
                this.$el.find(labelValue).text(value);
            } else {
                this.$el.find(labelValue).text(BLANKS);
            }
        },
        updateTimeValue: function(newTime){
            //TODO update the time for the slider maybe
        },
        rendering: false,
        onRender: function() {
            if (!_.isUndefined(this.model) && this.model.initialized){
                this.renderPlots();
            } else {
                var _this = this;
                app.listenTo(app.vent, 'data:loaded', function(model_name) {
                    if (model_name == _this.model_name){
                        if (_.isUndefined(_this.model)){
                             _this.model = app.plot_models[model_name];
                        }
                        _this.renderPlots();
                    }
                });
            }
        },
        renderPlots: function() {
            if (!app.plot_models_initialized) {
                return;
            }
            if (_.isUndefined(this.model)){
                this.model = app.plot_models[this.model_name];
            }
            if (this.rendering || !this.model.initialized) {
                return;
            }
            this.rendering = true;
            var plotDiv = this.$el.find("#plotDiv");
            if (this.plot == undefined) {
                this.drawTitle();

                this.plot = $.plot(plotDiv, this.model.buildPlotDataArray(), this.plotOptions);
                var context = this;
                // get the colors
                var keys = Object.keys( this.model.channel_descriptions );
                _.each(this.plot.getData(), function(data, index){
                    this.model.channel_descriptions[keys[index]].set('color', data.color);
                }, this);

                // draw the legend labels
                this.drawLegendLabels();

                // hook up the click and hover
                plotDiv.bind("plotclick", function (event, pos, item) {
                    context.selectData(item.dataIndex);
                });
                plotDiv.bind("plothover", function (event, pos, item) {
                    if (item != null){
                        context.selectData(item.dataIndex);
                    }
                });
                // this.$el.resize(function(event) {context.handleResize();});
            } else {
                var plotOptions = this.plot.getOptions();
                //plotOptions.xaxis.timeformat = this.plotOptions.xaxis.timeformat;
                //plotOptions.colors = this.getPlotColors();
                this.plot.setupGrid();
                this.plot.setData(this.model.buildPlotDataArray());
                this.plot.draw();
            }
            this.rendering = false;
        }

    });

    app.views.TimeseriesValueView = Marionette.View.extend({
        template: '#template-data-value-table',
        table_setup: false,
        initialize: function(options) {
            if (_.isEmpty(options)) {
                options = app.options.plotOptions;
            }

            this.model_name = options.model_name;
            this.title = options.title;
            // the model must be initialized in the app
            if (!_.isUndefined(app.plot_models_initialized) && app.plot_models_initialized){
                this.model = app.plot_models[options.model_name];
            }

            var _this = this;
            this.listenTo(app.vent, 'updateTimeseriesValue:' + this.model_name, function(index) {
                if (!_.isUndefined((index)) && index > -1){
                    _this.showData(index);
                } else {
                    _this.clearData();
                }
            });


        },
        clearData: function() {
            var plot_data_array = this.model.buildPlotDataArray();
            var _this = this;
            _.each(plot_data_array, function(channel_dict) {
                var channel = channel_dict.channel;
                _this.$el.find("#" + channel + 'value_value').html(BLANKS);
            });
        },
        showData: function(index){
            var plot_data_array = this.model.buildPlotDataArray();
            var _this = this;
            _.each(plot_data_array, function(channel_dict) {
                var values = channel_dict.data[index];
                var channel = channel_dict.channel;
                var print_value = values[1];
                if (_.isNumber(print_value)){
                    print_value = print_value.toFixed(2);
                }
                _this.$el.find("#" + channel + 'value_value').html(print_value);
            });
        },
        onAttach: function() {
            if (!_.isUndefined(this.model) && this.model.initialized){
                this.setupTable();
            } else {
                var _this = this;
                app.listenTo(app.vent, 'data:loaded', function(model_name) {
                    if (model_name == _this.model_name){
                        _this.setupTable();
                    }
                });
            }
        },
         setupTable: function() {
            if (this.table_setup){
                return;
            }
            if (_.isUndefined(this.model)){
                this.model = app.plot_models[this.model_name];
            }

            var context = this;
            var append_to = this.$el.find('.plot-value-tbody');
            var content = '<tr>';
            var col_count = 0;
            _.each(Object.keys(this.model.channel_descriptions), function(channel) {
                var cd = context.model.channel_descriptions[channel];
                var underChannel = channel.split(' ').join('_');

                content += '<td id="' + underChannel + 'value_label" ><strong>';
                content += cd.get('label');
                content += ':</strong>&nbsp;</td>';
                content += '<td id="' + underChannel + 'value_td" >';
                content += '<span id="' + underChannel + 'value_value">' + BLANKS + '</span>';
                if (cd.get('units') !== null) {
                    content += '&nbsp;<span id="' + underChannel + 'value_units">' + cd.get('units') + '</span>';
                }
                content += '</td>';
                col_count += 2;
            });
            content += '</tr>';
            append_to.append(content);

            append_to = this.$el.find('.plot-value-thead');
            content = '<tr>';
            content +='<td colspan=' + col_count + '>' + this.title + '</td>';
            content += '</tr>';
            append_to.append(content);
            this.table_setup = true;

        }

    });

});