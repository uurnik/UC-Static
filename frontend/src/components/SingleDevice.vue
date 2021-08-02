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
              ><strong>Hostname</strong>
              <span>{{ device.dev_name }}</span></v-col
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
              ><strong>WAN IP Address</strong
              ><span>{{ device.ip }}</span></v-col
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
              ><strong>Vendor</strong><span>{{ device.vendor }}</span>
            </v-col></v-card-text
          >
          <v-card-text class="pb-0 ma-0"
            ><v-col class="d-flex justify-space-between pb-1 pa-0 ml-4 ma-0"
              ><strong>Serial Number</strong
              ><span>{{ device.serial_no }}</span></v-col
            >
          </v-card-text>
          <v-card-text class="pb-0 ma-0"
            ><v-col class="d-flex justify-space-between pb-1 pa-0 ml-4 ma-0"
              ><strong>OS Version</strong><span>{{ device.os_version }}</span>
            </v-col></v-card-text
          >
          <v-card-text class="pb-0 ma-0">
            <v-col class="d-flex justify-space-between pb-1 pa-0 ml-4 ma-0"
              ><strong>RAM Size</strong
              ><span>{{ device.ram_size }}</span></v-col
            >
          
          </v-card-text>
          <v-card-text class="pb-0 ma-0">
            <v-col class="d-flex justify-space-between pb-1 pa-0 ml-4 ma-0"
              ><strong>Uptime</strong
              ><span>{{ uptime }}</span></v-col
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
            type="radialBar"
            height="180px"
            width="180px"
            :options="cpuchart.chartOptions"
            :series="cpuusage"
          ></apexchart>
          <apexchart
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
              type="line"
              height="280px"
              :options="wanchart.chartOptions"
              :series="wseries"
            ></apexchart>
          </v-flex>
        </v-card>
      </v-flex>
    </div>

    <v-flex class="mt-12 mx-auto" lg10 md10 justify-center align-self-center>
      <v-card flat>
        <v-card-title align-center>
          <h2 class="mx-auto my-5 font-weight-light pageheading--text">
            Interface Details
          </h2>
        </v-card-title>
        <v-skeleton-loader :loading="loading" type="table">
          <v-data-table
            :headers="headers"
            :items="interfaces"
            :items-per-page="10"
            fixed-header
          >
            <template v-slot:[`item.proto`]="{ item }">
              <v-icon v-if="item.proto == 'up'" class="pl-4" color="green"
                >mdi-check-circle</v-icon
              >
              <v-icon v-if="item.proto == 'down'" class="pl-4" color="red"
                >mdi-close-circle</v-icon
              ></template
            >
            <template v-slot:[`item.status`]="{ item }">
              <v-icon v-if="item.status == 'up'" class="pl-4" color="green"
                >mdi-check-circle</v-icon
              >
              <v-chip
                v-if="item.status == 'administratively down'"
                class="pl-4"
                color="orange"
                >{{ item.status }}</v-chip
              >
              <v-icon v-if="item.status == 'down'" class="pl-4" color="red"
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
  WANChartOptions
} from "../apexchartsconfigs/monitorcharts";

export default {
  props: ["name"],
  data() {
    return {
      cpuchart: radialCPUoptions,
      memorychart: radialMemoryoptions,
      wanchart: WANChartOptions,

      wseries:[{
        name: 'Kb',
            data: [4, 3, 10, 9, 29, 19, 22, 9, 12, 7, 19, 5, 13, 9, 17, 2, 7, 5]
      }],
      uptime:"",
      ramusage:[],
      cpuusage:[],
      polltimer:null,
      loading: true,
      headers: [
        {
          text: "Name",
          align: "start",
          sortable: false,
          value: "intf",
        },
        { text: "IP Address", value: "ipaddr" },
        { text: "Admin Status", value: "status" },
        { text: "Protocol Status", value: "proto" },
      ],
      interfaces: [],
      device: {},
    };
  },
  methods: {
    snmppoll() {
      this.$getAPI.get("snmp?name=" + this.name).then((response) => {
        this.ramusage = [response.data[0].result.ramusage]
        this.cpuusage = [response.data[0].result.cpmCPUTotal5minRev]
        this.uptime = response.data[0].result.sysUpTime
      })
    }
  },
  destroyed() {
    clearInterval(this.polltimer);
  },
  mounted() {
    this.$getAPI.get("hosts?name=" + this.name).then((response) => {
      this.device = response.data;
      this.snmppoll();
      this.polltimer = setInterval(() => {
        this.snmppoll();
      },15000)

    });
    this.$getAPI.get(`interfaces/${this.name}/`).then((response) => {
      this.interfaces = response.data;
      this.loading = false;
    });
  },
};
</script>

<style>
/* #monitor {
  border: 1px solid #42A5F5;
  border-color:1px #42A5F5;
} */
</style>
