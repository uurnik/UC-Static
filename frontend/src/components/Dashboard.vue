<template>
  <v-app>
    <v-row class="d-flex">
      <v-col>
        <div id="chart">
          <apexchart
            type="radialBar"
            height="350"
            :options="chartOptions"
            :series="series"
          ></apexchart>
        </div>
      </v-col>
    </v-row>
  </v-app>
</template>


<script>
export default {
  data() {
    return {
      series: [90, 40],
      chartOptions: {
        chart: {
          height: 350,
          type: "radialBar",
        },
        plotOptions: {
          radialBar: {
            dataLabels: {
              name: {
                fontSize: "22px",
              },
              value: {
                fontSize: "16px",
                formatter: function (val) {
                  return val;
                },
              },
              total: {
                show: true,
                label: "Total",
                formatter: function () {
                  // By default this function returns the average of all series. The below is just an example to show the use of custom formatter function
                  return 200;
                },
              },
            },
          },
        },
        labels: ["Managed", "UnManaged"],
      },
    };
  },
};
</script>
