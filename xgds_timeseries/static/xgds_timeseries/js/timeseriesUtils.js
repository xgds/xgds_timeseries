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
            //max: 100, // set a manual maximum to allow for labels
            ticks: 0 // this line removes the y ticks
        },
        xaxis: {
            mode: 'time',
            timeformat: DEFAULT_PLOT_TIME_FORMAT,
            timezone: getTimeZone(),
            reserveSpace: false
        },
        legend: {
            show: false
        },
		hooks: {
            processRawData: function (plot, series, data, datapoints) {
                debugger;
                console.log('in process raw data');
                console.log(data);
            },
            processDatapoints: function (plot, series, datapoints) {
                debugger;
                console.log('in process datapoints');
            }
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
                    for (var key in data){
                    	this.labels = [data[key].label];
					}
					//TODO handle multiple plots ...
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
                    var skipped = false;
                    for (var key in data){
                    	if (!skipped) {
                    		skipped = true;
                    		continue;
						}
                    	this.plotOptions['yaxis'].min = data[key].min;
                    	this.plotOptions['yaxis'].max = data[key].max;
					}
					//TODO handle multiple plots ...
                }
            }, this),
            error: $.proxy(function(data){
                this.setMessage("MinMax failed.");
            }, this)
          });
	},
	getData: function(options){
		if (this.plot != undefined){
			this.plot.destroy();
			this.plot = null;
		}
		this.getChannelDescriptions(options);
		//this.getMinMax(options);
		this.setMessage('Loading data...');
		$.ajax({
            url: '/timeseries/values/list/json',
            dataType: 'json',
            data: options,
			type: 'POST',
            success: $.proxy(function(data) {
                if (_.isUndefined(data) || data.length === 0){
                    this.setMessage("None found.");
                } else {
                	this.clearMessage();
                	console.log(data);
                	var cleandata = [];
                	for (var i=0; i<data.length; i++){
                		// assume timestamp is [1]
						var the_time = moment(data[i][1]).valueOf();
                		var singlepair = data[i].slice(2);
                		singlepair.unshift(the_time);
                		cleandata.push(singlepair);
					}
                	this.rendertimeseriesPlot(options, cleandata);
                }
            }, this),
            error: $.proxy(function(data){
                this.setMessage("Search failed.");
            }, this)
          });
	},

	rendertimeseriesPlot: function(options, timeseriesData){

		this.plot = $.plot("#plotDiv",
			               [{ data: timeseriesData, color: 'blue'}],
						   this.plotOptions);
		console.log("made the plot");

		$("#plotDiv").bind("plothover", function (event, pos, item) {
			if (item) {
				var	y = item.datapoint[1];
				xgds_timeseries.plot.unhighlight();
				xgds_timeseries.plot.highlight(item.series, item.datapoint);
				xgds_timeseries.showValue(y);
			}
		});
	}
    
    
});