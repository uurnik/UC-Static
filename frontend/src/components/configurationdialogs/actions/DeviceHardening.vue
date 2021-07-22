<template>
  <v-dialog
    style="height: 100%"
    overlay-opacity="0.75"
    scrollable
    fullscreen
    v-model="dialog"
    transition="dialog-bottom-transition"
  >
    <v-card class="white white--text" height="100%">
      <v-toolbar max-height="65px" dark color="pageheading">
        <v-btn icon dark @click="$store.state.menuDialogs['2'] = false">
          <v-icon>mdi-close</v-icon>
        </v-btn>
        <v-toolbar-title>Secure Access Control</v-toolbar-title>
        <v-spacer></v-spacer>
      </v-toolbar>
      <v-progress-linear
        v-if="loader"
        indeterminate
        color="#FF8A65"
      ></v-progress-linear>

      <v-card-text>
        <v-container fuild fill-height class="mb-5">
          <v-btn
            v-if="showbtn"
            @click="getStatus()"
            class="mx-auto"
            fab
            dark
            x-large
            color="pageheading"
            width="90px"
            height="90px"
          >
            <v-icon x-large dark> mdi-shield </v-icon></v-btn
          >

          <v-list class="list mx-auto" v-if="showitems">
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
            <v-flex md7 xs9 lg5>
              <v-simple-table class="mx-auto align-center">
                <template v-slot:default>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in devices" :key="item.name">
                      <td><h4 class="grey--text text--darken-3">{{ item.name }}</h4></td>
                      <td v-if="item.failed == false">
                        <v-icon class="pl-4" color="green"
                          >mdi-check-circle</v-icon
                        >
                      </td>
                      <td v-if="item.failed == true">
                        <v-icon class="pl-4" color="red"
                          >mdi-close-circle</v-icon
                        >
                      </td>
                    </tr>
                  </tbody>
                </template>
              </v-simple-table>
            </v-flex>
          </v-col>
        </v-container>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          v-if="loader == false && showstatusbtn == true"
          class="pageheading white--text"
          @click="
            showstatus = true;
            showitems = false;
            showstatusbtn = false;
          "
        >
          Status
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export default {
  data() {
    return {
      configurationtasks: [
        "Enabling Connection Monitroing Capablities",
        "Securing Against Unauthorized Web Access",
        "Preventing Unsolicited Boot Processes/Lookups",
        "Disabling Legacy WAN Features",
        "Protecting User Session Identity",
        "Protection Against Unauthorized Traffic Path Engineering",
        "Securing MAC Address Tables",
        "Disabling TFTP Server Access",
        "Preventing Unauthorized Information Access",
        "Setting Up Remote Access",
        "Securing & Optimizing Remote Access",
        "Encrypting Users' Information",
        "Protecting Internal Platform Resources",
        "Enabling User Friendly Logs Functionality",
        "Disabling Unnecessary Traffic Flooding",
        "Protecting Platform Interfaces",
        "Optimizing Ipv6 Features",
        "Gaurding Against Unauthorized Management Access",
      ],
      currenttask: [],
      showstatus: false,
      dialog: true,
      showitems: false,
      loader: false,
      showstatusbtn: false,
      desserts: [],
      devices: [],
      showbtn: true,
    };
  },
  watch: {
    showitems: async function (value) {
      if (value == true) {
        for (var i = 0; i < this.configurationtasks.length; i++) {
          this.currenttask.push(this.configurationtasks[i]);
          await sleep(1000);
        }
      }
    },
    currenttask(value) {
      if (value.length == this.configurationtasks.length) {
        this.showstatusbtn = true;
      }
    },
  },
  methods: {
    getStatus() {
      this.showitems = true;
      this.loader = true;
      this.showbtn = false;
      this.$getAPI.post("device-hardening/").then((response) => {
        this.devices = response.data;
        this.$store.state.devicehardening = true;
        this.loader = false;
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