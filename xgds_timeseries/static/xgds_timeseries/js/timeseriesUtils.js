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

var xgds_timeseries = xgds_timeseries || {};
$.extend(xgds_timeseries, {
	playback : {
		lastUpdate: undefined,
		invalid: false,
		initialized: false,
		initialize: function() {
			if (this.initialized){
				return;
			}
			//moment.tz.setDefault(app.getTimeZone()); // handled in planner app now
			var _this = this;

			this.initialized = true;
		},
		doSetTime: function(currentTime){
			if (currentTime === undefined){
				return;
			}
			this.lastUpdate = moment(currentTime);
			//app.vent.trigger('updatePlotTime', this.lastUpdate.toDate().getTime());
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
	},
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
        // yaxis: {
        //     //max: 100, // set a manual maximum to allow for labels
        //     ticks: 0 // this line removes the y ticks
        // },
        xaxis: {
            mode: 'time',
            timeformat: DEFAULT_PLOT_TIME_FORMAT,
            timezone: getTimeZone(),
            reserveSpace: false
        },
		yaxes: [],
        legend: {
            show: false
        }
    },
    clearMessage: function(msg){
        $('#timeseries_message').html('');
    },
    setMessage: function(msg){
        $('#timeseries_message').html(msg);
    },
    showValue: function(x, y){
    	var str = this.labels[0] + ": "+ x + "<br/>";
		xgds_timeseries.setMessage(str);
    },
    getChannelDescriptions: function(postOptions) {
        $.ajax({
            url: '/timeseries/channel_descriptions/json',
            dataType: 'json',
			type: 'POST',
            data: postOptions,
            success: $.proxy(function(data) {
                if (_.isUndefined(data) || data.length === 0){
                    this.setMessage("None found.");
                } else {
                	this.labels = [];
                	this.channel_descriptions = data;
                    for (var key in data){
                    	this.labels.push([data[key].label]);
					}
					this.getMinMax(postOptions);

                }
            }, this),
            error: $.proxy(function(data){
                this.setMessage("Channel descriptions failed.");
            }, this)
          });
    },
	getMinMax: function(postOptions) {
		$.ajax({
            url: '/timeseries/min_max/json',
            dataType: 'json',
			type: 'POST',
            data: postOptions,
            success: $.proxy(function(data) {
                if (_.isUndefined(data) || data.length === 0){
                    this.setMessage("None found.");
                } else {
                    for (var key in data){
                    	if (key !== 'timestamp') {
                            this.plotOptions.yaxes.push({
                                'min': data[key].min,
                                'max': data[key].max,
                                'ticks': 0
                            });
                        }
					}
					playback.initialize({getStartTime: function(){return data['timestamp'].min;},
	    						 getEndTime: function(){return data['timestamp'].max;},
	    						 displayTZ: getTimeZone(),
                                 slider: true
	    						 });
					this.loadData(postOptions);
                }
            }, this),
            error: $.proxy(function(data){
                this.setMessage("MinMax failed.");
            }, this)
          });
	},
	loadData: function(options){
		$.ajax({
            url: '/timeseries/values/json',
            dataType: 'json',
            data: options,
			type: 'POST',
            success: $.proxy(function(data) {
                if (_.isUndefined(data) || data.length === 0){
                    this.setMessage("None found.");
                } else {
                	this.clearMessage();
                	var data_dict = {};
                	_.each(Object.keys(this.channel_descriptions), function(field_name, index, list){
                		data_dict[field_name] = [];
                	});
                	for (var i=0; i<data.length; i++){
                		var the_time = moment(data[i]['timestamp']).valueOf();
                		_.each(Object.keys(this.channel_descriptions), function(field_name, index, list){
							data_dict[field_name].push([the_time, data[i][field_name]]);
						})
					}
                	this.rendertimeseriesPlot(options, data_dict);
                }
            }, this),
            error: $.proxy(function(data){
                this.setMessage("Search failed.");
            }, this)
          });
	},
	getData: function(options){
		if (this.plot != undefined){
			this.plot.destroy();
			this.plot = null;
		}
		if (this.labels === undefined) {
            this.getChannelDescriptions(options);
        } else {
			this.loadData(options);
		}
	},

	rendertimeseriesPlot: function(options, timeseriesData){
		var data_config = [];
		for (var key in timeseriesData){
			// TODO STORE MAP OF COLORS
			data_config.push({data: timeseriesData[key]});
		}
		this.plot = $.plot("#plotDiv",
			               data_config,
						   this.plotOptions);

		// get the colors
		var keys = Object.keys( this.channel_descriptions );
		_.each(this.plot.getData(), function(data, index){
			this.channel_descriptions[keys[index]].color = data.color;
		}, this);

		$("#plotDiv").bind("plothover", function (event, pos, item) {
			if (item) {
				var	y = item.datapoint[1];
				xgds_timeseries.plot.unhighlight();
				xgds_timeseries.plot.highlight(item.series, item.datapoint);
				xgds_timeseries.showValue(y);
			}
		});

		playback.addListener(this.playback);
	}
    
    
});