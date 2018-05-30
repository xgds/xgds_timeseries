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

var ChannelDescriptionModel = Backbone.Model.extend({

	defaults: {
		'label': null,
		'units': null,
		'global_min': null,
		'global_max': null,
		'min': null,
		'max': null,
		'interval': null,
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
		this.set('interval', data['interval']);
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

app.views.TimeseriesPlotView = Marionette.View.extend({
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
	template: '#plot_contents',
	initialized: false,
	initialize: function(options) {
		if (_.isEmpty(options)) {
			this.postOptions = appOptions.plotOptions;  // TODO fix.
		} else {
			this.postOptions = options;
		}
		if (this.plot != undefined){
			this.plot.destroy();
			this.plot = null;
		}
		var _this = this;
		this.model_name = this.postOptions.model_name;
		app.listenTo(app.vent, 'data:loaded', function(model_name) {
			if (model_name == _this.model_name){
				_this.onRender();
			}
		});
		if (this.channel_descriptions === undefined) {
            this.getChannelDescriptions();
        } else {
			this.loadData();
		}
		playback.addListener(this.playback);

    },
    clearMessage: function(msg){
        this.$el.find('#timeseries_message').html('');
    },
    setMessage: function(msg){
        this.$el.find('#timeseries_message').html(msg);
    },
    showValue: function(x, y){
    	var str = this.labels[0] + ": "+ x + "<br/>";
		xgds_timeseries.setMessage(str);
    },
    getChannelDescriptions: function() {
        $.ajax({
            url: '/timeseries/channel_descriptions/json',
            dataType: 'json',
			type: 'POST',
            data: this.postOptions,
            success: $.proxy(function(data) {
                if (_.isUndefined(data) || data.length === 0){
                    this.setMessage("None found.");
                } else {
                	this.channel_descriptions = {};
                    for (var key in data){
                    	this.channel_descriptions[key] = new ChannelDescriptionModel(data[key]);
					}
					this.getMinMax();
                }
            }, this),
            error: $.proxy(function(data){
                this.setMessage("Channel descriptions failed.");
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
                    this.setMessage("None found.");
                } else {
                	var skip_keys = ['timestamp','pk'];
                    for (var key in data){
                    	if (!skip_keys.includes(key)) {
                    		this.channel_descriptions[key].set('min', data[key].min);
                            this.channel_descriptions[key].set('max', data[key].max);
                            // this.plotOptions.yaxes.push({
                            //     'min': data[key].min,
                            //     'max': data[key].max,
                            //     'ticks': 0
                            // });
                        }
					}
					playback.initialize({getStartTime: function(){return data['timestamp'].min;},
	    						 getEndTime: function(){return data['timestamp'].max;},
	    						 displayTZ: getTimeZone(),
                                 slider: true
	    						 });
					this.loadData();
                }
            }, this),
            error: $.proxy(function(data){
                this.setMessage("MinMax failed.");
            }, this)
          });
	},
	loadData: function(){
		var _this = this;
		$.ajax({
            url: '/timeseries/values/json',
            dataType: 'json',
            data: this.postOptions,
			type: 'POST',
            success: $.proxy(function(data) {
                if (_.isUndefined(data) || data.length === 0){
                    this.setMessage("None found.");
                } else {
                	this.clearMessage();
					_.each(data, function(data_block) {
						var the_time = moment(data_block['timestamp']).valueOf();
						_.each(Object.keys(this.channel_descriptions), function(field_name, index, list){
							var data_array = _this.channel_descriptions[field_name].get('data');
							var datum = data_block[field_name]
							data_array.push([the_time, datum]);
							var i = 10;
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
    loadLegendCookie: function(key) {
		var cookieVisible = Cookies.get(key);
		var visible = true;
		if (cookieVisible != undefined){
			visible = (cookieVisible == 'true');
		} else {
			Cookies.set(key, true);
		}
		return visible;
	},
    togglePlot(key, visible){
		var cd = this.channel_descriptions[key];
		if (cd.get('visible') != visible){
			cd.set('visible', visible);
			this.onRender();
		}
	},
	drawTitle: function() {
		this.$el.find("#plotTitle").html('<strong>' + this.postOptions.title + '</strong>')
	},
    drawLegendLabels: function() {
		var context = this;
		var keys = Object.keys(this.channel_descriptions);
		for (var i=0; i<keys.length; i++) {
			var label=keys[i];
			var underLabel = label.split(' ').join('_');
			var theColor = this.channel_descriptions[label].color;
			var content = '<div id="' + underLabel + 'legend_div" class="d-sm-inline-flex flex-row" style="min-width:180px;">';
			content += '<label><input type="checkbox" id="' + underLabel + '_checkbox" value="' + label + '" style="display:inline-block;" class="mr-1"><span id="' + underLabel + '_label" style="color:' + theColor + '">' + label + ':</span><span id="' + underLabel + '_value">' + BLANKS + '</span></label>';
			content += '</div>'
            this.$el.find("#plotLegend").append(content);
			var visible = this.loadLegendCookie(label);
			$("#" + underLabel + "_checkbox").prop('checked', visible);
			this.channel_descriptions[label].set('visible', visible);
			$("#" + underLabel + "_checkbox").change(function() {
				var id = $(this).attr('id');
				var checked = $(this).is(":checked");
				Cookies.set($(this).attr('value'), checked);
				context.togglePlot($(this).attr('value'), checked);
			});
		}
	},
	buildPlotDataArray: function() {
		var result = [];
		_.each(Object.keys(this.channel_descriptions), function(key) {
			var cd = this.channel_descriptions[key];
			if (cd.get('visible')) {
                result.push({label: cd.get('label'), data: cd.get('data'), key: key})
            }
		}, this);
        return result;
	},
	selectData: function(index) {
		if (this.plot != undefined){
			this.plot.unhighlight();
			var plotData = this.plot.getData();
			var time = null;
			var value = null;
			var label = undefined;
			for (var i=0; i<plotData.length; i++){
				label = plotData[i].label;
				if (label !== undefined){
					var dataAtIndex = plotData[i].data[index];
					this.plot.highlight(i, index);

					if (dataAtIndex != undefined) {
						if (time == null){
							time = dataAtIndex[0];
							value = dataAtIndex[1];
						}
					} else {
						if (time == null){
							time = dataAtIndex[0];
							value = null;
						}
                    }

					this.updateDataValue(plotData[i].key, value);
				}
				label = undefined;
			}
			this.updateTimeValue(time);
		}
	},
	updateDataValue: function(label, value){
		// show the value from the plot below the plot.
		var labelValue = ('#' + label + '_value');
		var labelValue = labelValue.split(' ').join('_');
		if (value != null && value != undefined){
			value = value.toFixed(2);
			$(labelValue).text(value);
		} else {
			$(labelValue).text(BLANKS);
		}
	},
	updateTimeValue: function(newTime){
		//TODO update the time for the slider maybe
	},
	rendering: false,
    onRender: function() {
		if (this.rendering || !this.initialized) {
			return;
		}
		this.rendering = true;
		var plotDiv = this.$el.find("#plotDiv");
		if (this.plot == undefined) {
			this.drawTitle();

			this.plot = $.plot(plotDiv, this.buildPlotDataArray(), this.plotOptions);
			var context = this;
			// get the colors
			var keys = Object.keys( this.channel_descriptions );
			_.each(this.plot.getData(), function(data, index){
				this.channel_descriptions[keys[index]].color = data.color;
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
			$('#plot-container').resize(function(event) {context.handleResize();});
		} else {
			var plotOptions = this.plot.getOptions();
			//plotOptions.xaxis.timeformat = this.plotOptions.xaxis.timeformat;
			//plotOptions.colors = this.getPlotColors();
			this.plot.setupGrid();
			this.plot.setData(this.buildPlotDataArray());
			this.plot.draw();
		}
		this.rendering = false;
	}
	// rendertimeseriesPlot: function(options, timeseriesData){
	// 	var data_config = [];
	// 	for (var key in timeseriesData){
	// 		data_config.push({data: timeseriesData[key]});
	// 	}
	// 	this.plot = $.plot("#plotDiv",
	// 		               data_config,
	// 					   this.plotOptions);
    //
    //
    //
	// 	$("#plotDiv").bind("plothover", function (event, pos, item) {
	// 		if (item) {
	// 			var	y = item.datapoint[1];
	// 			xgds_timeseries.plot.unhighlight();
	// 			xgds_timeseries.plot.highlight(item.series, item.datapoint);
	// 			xgds_timeseries.showValue(y);
	// 		}
	// 	});
    //
	// }
    
    
});

});