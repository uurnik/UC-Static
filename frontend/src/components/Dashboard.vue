<template>
  <div>
    <v-flex class="mx-auto" lg10 md10 justify-space-between row>
      <v-card width="35em" style="border: solid 2px #42A5F5" class="ma-5 elevation-0">
        <v-card-title class="ma-1 elevation-0 pageheading--text" style="border-bottom: solid 2px #42A5F5"
          >Summary</v-card-title
        >
        <v-card-text>
          <apexchart
            type="radialBar"
            height="200"
            :options="chartOptions"
            :series="series"
          ></apexchart>
        </v-card-text>
      </v-card>
      <v-card width="35em" style="border: solid 2px #42A5F5" class="ma-5 elevation-0">
        <v-card-title class="ma-1 elevation-0 pageheading--text" style="border-bottom: solid 2px #42A5F5"
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
    <v-flex class="mx-auto" row mt-5 lg10 md10 justify-space-between>
      <v-card width="35em" class="ma-7 elevation-0">
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
                      :value="item.cpu"
                      color="amber"
                      height="12px"
                    >
                    </v-progress-linear>
                    <span class="ml-3">{{ item.cpu }}%</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>
      </v-card>
      <v-spacer></v-spacer>
      <v-card width="35em" class="ma-7 elevation-0">
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
                      :value="item.mem"
                      color="amber"
                      height="12px"
                    >
                    </v-progress-linear>
                    <span class="ml-3">{{ item.mem }}%</span>
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
          :footer-props="{showFirstLastPage: false}"
          :items="allDevices"
          :search="search"
          disable-pagination
          class="table elevation-0 mx-3 ma-7 table-cursor"
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
      series: [45, 56],
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
              },
              total: {
                show: true,
                label: "Total",
                formatter: function () {
                  // By default this function returns the average of all series. The below is just an example to show the use of custom formatter function
                  return 101;
                },
              },
            },
          },
        },
      },
      devicelocations: [
        {
          name: "ISB",
          loc: "Islamabad",
        },
        {
          name: "KHI",
          loc: "Karachi",
        },
        {
          name: "BWP",
          loc: "Bahawalpur",
        },
      ],
      topcpudevices: [
        {
          name: "KHI",
          cpu: "78",
        },
        {
          name: "ISB",
          cpu: "35",
        },
      ],
      topmemorydevices: [
        {
          name: "KHI",
          mem: "78",
        },
        {
          name: "ISB",
          mem: "35",
        },
      ],
    };
  },
  mounted() {
    this.loading = true;
    this.getDevices();
  },
  methods: {
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
    getDevices() {
      this.$getAPI.get("hosts").then((response) => {
        this.allDevices = response.data;
        this.loading = false;
      });
      // # TODO - add logic for error handing
    },
  },
};
</script>
<style>

</style>