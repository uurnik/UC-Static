<template>
  <div v-if="show" id="chart">
    <apexchart
      type="line"
      height="350"
      ref="chart"
      :options="chartOptions"
      :series="series"
    ></apexchart>
  </div>
</template>

<script>
var lastDate = 0;
var data = [];
var TICKINTERVAL = 86400000;
let XAXISRANGE = 777600000;
function getDayWiseTimeSeries(baseval, count, yrange) {
  var i = 0;
  while (i < count) {
    var x = baseval;
    var y =
      Math.floor(Math.random() * (yrange.max - yrange.min + 1)) + yrange.min;

    data.push({
      x,
      y,
    });
    lastDate = baseval;
    baseval += TICKINTERVAL;
    i++;
  }
}

getDayWiseTimeSeries(new Date("11 Feb 2017 GMT").getTime(), 10, {
  min: 10,
  max: 90,
});

function getNewSeries(baseval, yrange) {
  var newDate = baseval + TICKINTERVAL;
  lastDate = newDate;

  for (var i = 0; i < data.length - 10; i++) {
    // IMPORTANT
    // we reset the x and y of the data which is out of drawing area
    // to prevent memory leaks
    data[i].x = newDate - XAXISRANGE - TICKINTERVAL;
    data[i].y = 0;
  }

  data.push({
    x: newDate,
    y: Math.floor(Math.random() * (yrange.max - yrange.min + 1)) + yrange.min,
  });
}

//   function resetData(){
//     // Alternatively, you can also reset the data at certain intervals to prevent creating a huge series
//     data = data.slice(data.length - 10, data.length);
//   }

export default {
  props: ["name"],
  data() {
    return {
      interval: true,
      show: false,
      series: [
        {
          data: data.slice(),
        },
      ],
      chartOptions: {
        chart: {
          id: "realtime",
          height: 350,
          type: "line",
          animations: {
            enabled: true,
            easing: "linear",
            dynamicAnimation: {
              speed: 1000,
            },
          },
          toolbar: {
            show: false,
          },
          zoom: {
            enabled: false,
          },
        },
        dataLabels: {
          enabled: false,
        },
        stroke: {
          curve: "smooth",
        },
        title: {
          text: "Dynamic Updating Chart",
          align: "left",
        },
        markers: {
          size: 0,
        },
        xaxis: {
          type: "datetime",
          range: XAXISRANGE,
        },
        yaxis: {
          max: 100,
        },
        legend: {
          show: false,
        },
      },
    };
  },
  beforeDestroy() {
    this.interval = false;
  },
  mounted: function () {
    var me = this;
    const chart = setInterval(function () {
      if (!me.interval) {
        clearInterval(chart);
      }

      getNewSeries(lastDate, {
        min: 10,
        max: 90,
      });
      me.$refs.chart.updateSeries([
        {
          data: data,
        },
      ]);
    }, 1000);

    // every 60 seconds, we reset the data to prevent memory leaks
    //   setInterval(function () {
    //     resetData()
    //   }, 60000)

    this.show = true;
  },
};
</script>
