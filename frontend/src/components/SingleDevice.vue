<template>
  <div>
    <div class="font-weight-light pa-4 ml-3 text-h4 pageheading--text">
      {{ device.name }}
    </div>
    <div class="d-flex justify-space-between">
      <v-flex align-self-start lg4 md4>
        <v-card flat>
          <v-card-text class="pb-0 ma-0"
            ><v-col class="d-flex justify-space-between pa-0 pb-1 ml-4 ma-0"
              ><strong>Hostname</strong> <span>{{ fqdn }}</span></v-col
            ></v-card-text
          >
          <v-card-text class="pb-0 ma-0">
            <v-col class="d-flex justify-space-between pa-0 pb-1 ml-4 ma-0"
              ><strong>Managed</strong>
              <v-icon v-if="device.is_configured" class="pl-4" color="green"
                >mdi-check-circle</v-icon
              >
              <v-icon v-if="!device.is_configured" class="pl-4" color="red"
                >mdi-close-circle</v-icon
              ></v-col
            ></v-card-text
          >
          <v-card-text class="pb-0 ma-0"
            ><v-col class="d-flex justify-space-between pb-1 pa-0 ml-4 ma-0"
              ><strong>WAN IP Address</strong><span>{{ wan_ip }}</span></v-col
            >
          </v-card-text>
          <v-card-text class="pb-0 ma-0"
            ><v-col class="d-flex justify-space-between pb-1 pa-0 ml-4 ma-0"
              ><strong>Platform</strong
              ><span>{{ device.platform }}</span></v-col
            >
          </v-card-text>
          <v-card-text class="pb-0 ma-0"
            ><v-col class="d-flex justify-space-between pb-1 pa-0 ml-4 ma-0"
              ><strong>Model</strong><span>{{ device.model }}</span></v-col
            >
          </v-card-text>
          <v-card-text class="pb-0 ma-0"
            ><v-col class="d-flex justify-space-between pb-1 pa-0 ml-4 ma-0"
              ><strong>Vendor</strong><span>{{ vendor }}</span>
            </v-col></v-card-text
          >
          <v-card-text class="pb-0 ma-0"
            ><v-col class="d-flex justify-space-between pb-1 pa-0 ml-4 ma-0"
              ><strong>Serial Number</strong><span>{{ serialNo }}</span></v-col
            >
          </v-card-text>
          <v-card-text class="pb-0 ma-0"
            ><v-col class="d-flex justify-space-between pb-1 pa-0 ml-4 ma-0"
              ><strong>OS Version</strong><span>{{ osversion }}</span>
            </v-col></v-card-text
          >
          <v-card-text class="pb-0 ma-0">
            <v-col class="d-flex justify-space-between pb-1 pa-0 ml-4 ma-0"
              ><strong>RAM Size</strong><span>{{ ramsize }}</span></v-col
            >
          </v-card-text>
          <v-card-text class="pb-0 ma-0">
            <v-col class="d-flex justify-space-between pb-1 pa-0 ml-4 ma-0"
              ><strong>Uptime</strong><span>{{ uptime }}</span></v-col
            >
          </v-card-text>
        </v-card>
      </v-flex>
      <v-spacer></v-spacer>

      <v-flex md6 lg6>
        <v-card
          id="monitor"
          class="d-flex flex-row justify-center elevation-0 mr-5"
        >
          <apexchart
            ref="cpuradial"
            type="radialBar"
            height="180px"
            width="180px"
            :options="cpuchart.chartOptions"
            :series="cpuusage"
          ></apexchart>
          <apexchart
            ref="ramradial"
            type="radialBar"
            height="180px"
            width="180px"
            title="WAN Interface"
            :options="memorychart.chartOptions"
            :series="ramusage"
          ></apexchart>
        </v-card>
        <v-card class="mr-5 mx-auto mt-5 elevation-0">
          <v-flex class="mx-auto" md9 lg9>
            <apexchart
              ref="chart"
              type="line"
              height="280px"
              :options="chartOptions"
              :series="series"
            ></apexchart>
          </v-flex>
        </v-card>
      </v-flex>
    </div>
    <v-flex class="mx-auto" row mt-5 lg12 md12 justify-space-between>
      <v-card width="40%" class="elevation-0 mr-4 ml-4">
        <v-card-title class="grey lighten-3">CPU Utilization</v-card-title>

        <div v-if="cpuusage[0] || cpuusage[0] == 0" class="d-flex">
          <v-progress-linear
            class="mt-5 ml-1 mr-9"
            :value="cpuusage"
            :color="GetColor(cpuusage[0])"
            height="8px"
          >
          </v-progress-linear>
          <span  class="mr-2 mt-2 ml-9"
            >{{ cpuusage[0] }}%</span>
        </div>
      </v-card>
      <v-spacer></v-spacer>
      <v-card width="40%" class="elevation-0 mr-4 ml-4">
        <v-card-title class="grey lighten-3">Memory Utilization</v-card-title>
        <div v-if="ramusage[0] ||  ramusage[0] == 0" class="d-flex">
          <v-progress-linear
            class="mt-5 ml-1 mr-9"
            :value="ramusage[0]"
            :color="GetColor(ramusage[0])"
            height="8px"
          >
          </v-progress-linear>
          <span class="mr-2 mt-2 ml-9">{{ ramusage[0] }}%</span>
        </div>
      </v-card>
    </v-flex>

    <v-flex class="mt-12 mr-4 ml-4 mx-auto" lg12 md12 justify-center align-self-center>
      <v-card flat>
        <v-card-title align-center>
          <h2 class="mx-auto my-5 font-weight-light pageheading--text">
            Interface Details
          </h2>
        </v-card-title>
        <v-skeleton-loader :loading="loading" type="table">
          <v-data-table
            id="interfaces"
            :headers="headers"
            :items="interfaces"
            :items-per-page="10"
            fixed-header
          >
            <template v-slot:[`item.adminstatus`]="{ item }">
              <v-icon v-if="item.adminstatus == 1" class="pl-4" color="green"
                >mdi-check-circle</v-icon
              >
              <v-icon v-if="item.adminstatus != 1" class="pl-4" color="red"
                >mdi-close-circle</v-icon
              ></template
            >
            <template v-slot:[`item.status`]="{ item }">
              <v-icon v-if="item.status == 1" class="pl-4" color="green"
                >mdi-check-circle</v-icon
              >
              <v-icon v-if="item.status != 1" class="pl-4" color="red"
                >mdi-close-circle</v-icon
              >
            </template>
          </v-data-table>
        </v-skeleton-loader>
      </v-card>
    </v-flex>
  </div>
</template>

<script>
import {
  radialCPUoptions,
  radialMemoryoptions,
  WANChartOptions,
} from "../apexchartsconfigs/monitorcharts";

export default {
  props: ["name"],
  data() {
    return {
      interval: true,
      show: false,
      series: [],
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
          text: "WAN Interface",
          align: "center",
          style: {
            fontSize: "17px",
            fontWeight: "medium",
            fontFamily: "Roboto,sans-serif",
            color: "#42A5F5",
          },
        },
        colors: ["#42A5F5"],
        markers: {
          size: 0,
        },
        xaxis: {
          type: "datetime",
        },
        legend: {
          show: false,
        },
      },
      cpuchart: radialCPUoptions,
      ramsize: "",
      memorychart: radialMemoryoptions,
      wanchart: WANChartOptions,
      interfaceout: "",
      uptime: "",
      ramusage: [],
      cpuusage: [],
      serialNo: "",
      polltimer: null,
      vendor: "",
      wan_ip: "",
      loading: true,
      osversion: "",
      headers: [
        {
          text: "Name",
          align: "start",
          sortable: false,
          value: "name",
        },
        { text: "IP Address", value: "ipaddr" },
        { text: "Admin Status", value: "adminstatus" },
        { text: "Oper Status", value: "status" },
        { text: "In (MB) ", value: "In" },
        { text: "Out (MB)", value: "Out" },
        { text: "InErrors", value: "InErrors" },
        { text: "OutErrors", value: "OutErrors" },
        { text: "PhyAddress", value: "mac" },
      ],
      interfaces: [],
      device: {},
      fqdn: "",
    };
  },
  watch: {
    ramusage: function () {
      if (this.ramusage[0] <= 50) {
        this.memorychart.chartOptions.colors = ["#42A5F5"];
        this.$refs.ramradial.updateOptions(this.memorychart.chartOptions);
      } else if (this.ramusage[0] >= 80) {
        this.memorychart.chartOptions.colors = ["#FF3D00"];
        this.$refs.ramradial.updateOptions(this.memorychart.chartOptions);
      } else {
        this.memorychart.chartOptions.colors = ["#FFB300"];
        this.$refs.ramradial.updateOptions(this.memorychart.chartOptions);
      }
    },
    cpuusage: function () {
      if (this.cpuusage[0] <= 50) {
        this.cpuchart.chartOptions.colors = ["#42A5F5"];
        this.$refs.cpuradial.updateOptions(this.cpuchart.chartOptions);
      } else if (this.cpuusage[0] >= 80) {
        this.cpuchart.chartOptions.colors = ["#FF3D00"];
        this.$refs.cpuradial.updateOptions(this.cpuchart.chartOptions);
      } else {
        this.cpuchart.chartOptions.colors = ["#FFB300"];
        this.$refs.cpuradial.updateOptions(this.cpuchart.chartOptions);
      }
    },
  },
  beforeDestroy() {
    this.interval = false;
  },
  methods: {
    GetColor(value) {
      let color;
      if (value <= 50) {
        color = "#42A5F5";
      } else if (value >= 80) {
        color = "#FF3D00";
      } else {
        color = "#FFB300";
      }
      return color;
    },
    snmppoll() {
      this.$getAPI.get("monitoring/snmp?name=" + this.name).then((response) => {
        this.ramusage = [response.data[0].result.ramusage];
        this.cpuusage = [response.data[0].result.cpuusage];
        this.uptime = response.data[0].result.uptime;
        this.interfaces = response.data[0].result.interfaces;
        this.serialNo = response.data[0].result.chassisid;
        this.fqdn = response.data[0].result.fqdn;
        this.ramsize = response.data[0].result.totalramsize;
        this.osversion = response.data[0].result.sysDescr;
        this.vendor = response.data[0].result.vendor;
        this.wan_ip = response.data[0].result.wan_ip;

        this.loading = false;
      });
    },
  },
  destroyed() {
    clearInterval(this.polltimer);
  },
  mounted() {
    this.loading = true;
    this.$getAPI.get("hosts?name=" + this.name).then((response) => {
      this.device = response.data;
      this.snmppoll();
      this.polltimer = setInterval(() => {
        this.snmppoll();
      }, 15000);
    });
  },
};
</script>

<style>

#interfaces th {
  background-color:#EEEEEE;

}

</style>
