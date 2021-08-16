<template>
  <div>
    <v-col>
      <div
        class="
          font-weight-light
          d-flex
          justify-end
          pa-4
          text-h4
          pageheading--text
        "
      >
        <v-spacer></v-spacer>
    <v-menu offset-y class="">
          <template v-slot:activator="{ on, attrs }">
            <v-btn
              small
              class="mr-5 mt-1"
              color="pageheading white--text"
              v-bind="attrs"
              v-on="on"
            >
              <span>Set Interval</span>
            </v-btn>
          </template>
          <v-list dense>
            <v-list-item
              link
              v-for="(item, index) in timers"
              :key="index"
              @click="setPollInterval(index)"
            >
              <v-list-item-title link ripple dense
                >{{ item.title
                }}<v-icon
                  class="pl-7"
                  v-if="item.selected"
                  color="pageheading"
                  pl-3
                  small
                  >mdi-check-circle</v-icon
                ></v-list-item-title
              >
            </v-list-item>
          </v-list>
        </v-menu>
        </div>
      </v-col>
    <v-flex  class="mx-auto" lg12 md12 justify-space-between row>
      <v-card
        width="45%"
        style="border: solid 2px #42a5f5"
        class="ma-5 elevation-0"
      >
        <v-card-title
          class="ma-1 elevation-0 pageheading--text"
          style="border-bottom: solid 2px #42a5f5"
          >Summary</v-card-title
        >
        <v-card-text>
          <apexchart
            ref="radialchart"
            type="radialBar"
            height="200"
            :options="chartOptions"
            :series="series"
          ></apexchart>
        </v-card-text>
      </v-card>
      <v-card
        width="45%"
        style="border: solid 2px #42a5f5"
        class="ma-5 elevation-0"
      >
        <v-card-title
          class="ma-1 elevation-0 pageheading--text"
          style="border-bottom: solid 2px #42a5f5"
          >Locations</v-card-title
        >
        <v-simple-table height="220px" class="ma-0 pa-0" scrollable>
          <template v-slot:default>
            <thead>
              <tr>
                <th class="text-left">Name</th>
                <th class="text-left">Location</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in devicelocations" :key="item.name">
                <td style="border-bottom: none">{{ item.name }}</td>
                <td style="border-bottom: none">
                  {{ item.loc }}
                </td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>
      </v-card>
    </v-flex>
    <v-divider class="ma-5"></v-divider>
    <v-flex class="mx-auto" row mt-5 lg12 md12 justify-space-between>
      <v-card width="45%" class="ma-7 elevation-0">
        <v-card-title class="grey lighten-3"
          >Top 5 Devices By CPU Utilization</v-card-title
        >
        <v-simple-table>
          <template v-slot:default>
            <thead>
              <tr>
                <th class="text-left">Name</th>
                <th class="text-left">CPU Avg.</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in topcpudevices" :key="item.name">
                <td style="border-bottom: none">{{ item.name }}</td>
                <td style="border-bottom: none">
                  <div class="d-flex">
                    <v-progress-linear
                      class="mt-1"
                      :value="item.result.cpmCPUTotal5minRev"
                      color="success"
                      height="12px"
                    >
                    </v-progress-linear>
                    <span class="ml-3">{{ item.result.cpmCPUTotal5minRev }}%</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>
      </v-card>
      <v-spacer></v-spacer>
      <v-card width="45%" class="ma-7 elevation-0">
        <v-card-title class="grey lighten-3"
          >Top 5 Devices By Memory Utilization</v-card-title
        >
        <v-simple-table>
          <template v-slot:default>
            <thead>
              <tr>
                <th class="text-left">Name</th>
                <th class="text-left">Memory Avg.</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in topmemorydevices" :key="item.name">
                <td style="border-bottom: none">{{ item.name }}</td>
                <td style="border-bottom: none">
                  <div class="d-flex">
                    <v-progress-linear
                      class="mt-1"
                      :value="item.result.ramusage"
                      color="success"
                      height="12px"
                    >
                    </v-progress-linear>
                    <span class="ml-3">{{ item.result.ramusage }}%</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>
      </v-card>
    </v-flex>
    <div class="font-weight-light pa-4 ml-3 text-h4 pageheading--text">
      Sites
    </div>
    <v-fab-transition>
      <v-skeleton-loader :loading="loading" type="table">
        <v-data-table
          flat
          :headers="headers"
          :footer-props="{ showFirstLastPage: false }"
          :items="allDevices"
          disable-pagination
          class="table elevation-0 pl-4 pr-4 mx-3 ma-7 table-cursor"
          @click:row="GoToDevice"
        >
          <template v-slot:[`item.is_configured`]="{ item }">
            <v-icon v-if="item.is_configured" class="pl-4" color="green"
              >mdi-check-circle</v-icon
            >
            <v-icon v-if="!item.is_configured" class="pl-4" color="red"
              >mdi-close-circle</v-icon
            >
          </template>
          <template v-slot:[`item.group`]="{ item }">
            <span>{{ showGroups(item.group) }}</span>
          </template>
        </v-data-table>
      </v-skeleton-loader>
    </v-fab-transition>
  </div>
</template>


<script>
export default {
  data() {
    return {
      timer: "",
      timers: [
        { title: "15s", id: 1, value: 15000, selected: false },
        { title: "30s", id: 2, value: 30000, selected: false },
        { title: "1m", id: 3, value: 60000, selected: false },
        { title: "2m", id: 4, value: 120000, selected: false },
        { title: "5m", id: 5, value: 300000, selected: false },
      ],
      loading: false,
      headers: [
        { text: "Site Name", align: "start", sortable: false, value: "name" },
        { text: "IP Address", value: "ip" },
        { text: "Hostname", value: "dev_name" },
        { text: "Managed", value: "is_configured" },
        { text: "Group", value: "group" },
        { text: "Vendor", value: "vendor" },
      ],
      allDevices: [],
      series: [],
      chartOptions: {

        labels: ["Managed", "UnManaged"],
        legend: { show: true },
        responsive: [
          {
            legend: {
              position: "left",
            },
          },
        ],
        chart: {
          fontFamily: 'Roboto,sans-serif',
          height: 200,
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
              },
            },
          },
        },
      },
      devicelocations: [
      ],
      topmemorydevices: [],
      topcpudevices:[],
    };
  },
  mounted() {
    this.loading = true;
    this.getDevices();
    this.getsummary();
    this.snmp_poll();
  },
  methods: {
    snmp_poll() {

      this.$getAPI.get("monitoring/snmp?avg=true").then((response) => {
        this.topcpudevices = response.data['topcpuusage']
        this.topmemorydevices = response.data['topramusage']

    })},
    getsummary() {
      this.$getAPI.get("/monitoring/summary").then((response) => {
        this.total = response.data.total;
        this.series.push(response.data.managed);
        this.series.push(response.data.unmanaged);

        this.chartOptions.plotOptions.radialBar.dataLabels.total.formatter =
          function () {
            return response.data.total;
          };
        this.$refs.radialchart.updateOptions(this.chartOptions);
      });
    },

    formatText(group) {
      if (group == true) {
        return (group = "Managed");
      } else {
        return (group = "UnManaged");
      }
    },
    showGroups(group) {
      if (group == "HUB") {
        return (group = "Central Site");
      } else if (group == "SPOKE") {
        return (group = "Branch");
      }
    },
    getColor(status) {
      if (status == false) return "orange";
      else return "green";
    },

    GoToDevice(name) {
      this.$router.push("/host/" + name.name);
    },
    getDevices() {
      this.$getAPI.get("hosts").then((response) => {
        this.allDevices = response.data;
        this.loading = false;
      });
    },
    setPollInterval(index) {
      for (let i = 0; i < this.timers.length; i++) {
        this.timers[i].selected = false;
      }
      clearInterval(this.timer);
      localStorage.setItem("refreshdashboard", this.timers[index].value);
      this.timers[index].selected = true;
      this.timer = setInterval(() => {
        this.snmp_poll();
      }, this.timers[index].value);
    },
  },
  created() {
    var interval = null;
    if (localStorage.getItem("refreshdashboard")) {
      interval = parseInt(localStorage.getItem("refreshdashboard"));
      for (let i = 0; i < this.timers.length; i++) {
        if (this.timers[i].value == interval) {
          this.timers[i].selected = true;
          break
        }
      }
    } else {
      interval = 30000;
      this.timers[1].selected = true;
    }
    this.snmp_poll();
    this.timer = setInterval(() => {
      this.snmp_poll();
    }, interval);
  },
  destroyed() {
    clearInterval(this.timer);
  },
};
</script>
<style>
</style>