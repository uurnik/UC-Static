<template>
  <v-container fill-height class="mb-5">
    <v-btn
      v-if="showbtn"
      @click="Deploy()"
      class="mx-auto"
      fab
      dark
      x-large
      color="pageheading"
      width="90px"
      height="90px"
    >
      <v-icon x-large dark>mdi-cog</v-icon></v-btn
    >

    <v-list class="list mx-auto" v-if="$store.state.toggleloader == true">
      <v-list-item-group color="pageheading">
        <v-list-item v-for="(item, i) in currenttask" :key="i">
          <v-list-item-icon>
            <v-icon color="green" class="mr-2">mdi-check-circle</v-icon>
          </v-list-item-icon>
          <v-list-item-content>
            <v-list-item-title v-text="item"></v-list-item-title>
          </v-list-item-content>
        </v-list-item>
      </v-list-item-group>
    </v-list>

    <v-col v-if="showstatus" class="d-flex justify-center">
      <v-flex md10 xs12 lg8>
        <v-simple-table class="mx-auto align-center">
          <template v-slot:default>
            <thead>
              <tr>
                <th>Name</th>
                <th>Success</th>
                <!-- <th v-for="(task, index) in devices[0].tasks" :key="index + 1">
                  {{ task }}
                </th> -->
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in devices" :key="item.name">
                <td>
                  <h4 class="grey--text text--darken-3">{{ item.name }}</h4>
                </td>
                <td v-if="item.failed == false">
                  <v-icon class="pl-4" color="green">mdi-check-circle</v-icon>
                </td>
                <td v-if="item.failed == true">
                  <v-icon class="pl-4" color="red">mdi-close-circle</v-icon>
                </td>
                <!-- <td v-for="task in item.tasks" :key="task.index + 3">
                  <v-icon class="pl-4" color="green">mdi-check-circle</v-icon>
                </td> -->
              </tr>
            </tbody>
          </template>
        </v-simple-table>
      </v-flex>
    </v-col>
  </v-container>
</template>

<script>
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export default {
  name: "Step4",
  data() {
    return {
      configurationtasks: [
        "Developing Secure Connection with Uurnik Connect Orchestrator",
        "Archiving Current Configuration of Edge Devices",
        "Acquiring Overlay Prerequisites",
        "Configuring Segmented Routing",
        "Compiling Overlay Parameters",
        "Name-based (FQDN instead of IP address) Edge Device Discovery & Provisioning",
        "Deploying Secure Overlay",
        "Building Transport Layer Security Profile",
        "Proctecting Overlay Using Certificate Based Authentication",
        "Registering branch site central site & Orchestrator",
        "Completing Overlay Network Relationship",
        "Routing Plane Segmentation, Isolation Between Different Network Domains",
        "Ring Fencing Transport Link (e.g INETNET , MPLS )",
        "Compiling Routing of Multiple Networks",
        "Advertising of Inter-site networks for End-to-End Reachablility",
        "Preparing Branch Edge Device for Direct Internet Access",
        "Branch LAN Automatic Addressing Assignment",
        "Verifying Deployement",
      ],

      currenttask: [],
      dns: "",
      loader: false,
      showtable: false,
      showbtn: true,
      devices: [],
      showstatus: false,
    };
  },
  mounted() {
    this.reset();
  },
  watch: {
    "$store.state.toggleloader": async function (value) {
      if (value == true) {
        for (var i = 0; i < this.configurationtasks.length; i++) {
          // if (this.$store.state.accesstype != 2 && i != 3 ) {
          this.currenttask.push(this.configurationtasks[i]);
          await sleep(1000);
          // }
        }
      }
    },
  },
  methods: {
    reset() {
      this.loader = false;
      this.showbtn = true;
      this.showstatus = false;
    },

    Deploy() {
      this.showbtn = false;
      this.$store.state.toggleloader = true;
      this.dns = { dns: this.$store.state.dns };
      this.$getAPI
        .post(`configure/${this.$store.state.accesstype}/`, this.dns)
        .then((response) => {
          this.devices = response.data;
          this.$store.state.hidestatusbtn = false;
          this.$store.state.toggleloader = false;
          this.showstatus = true;
          this.$store.state.notConfigured = false;
        });
    },
  },
};
</script>
<style>
.list {
  -moz-column-count: 2;
  -moz-column-gap: 15px;
  -webkit-column-count: 2;
  -webkit-column-gap: 15px;
  column-count: 2;
  column-gap: 15px;
}
</style>