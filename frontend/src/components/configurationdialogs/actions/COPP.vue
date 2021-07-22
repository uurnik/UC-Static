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
        <v-btn icon dark @click="$store.state.menuDialogs['1'] = false">
          <v-icon>mdi-close</v-icon>
        </v-btn>
        <v-toolbar-title>Device Protection</v-toolbar-title>
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
            <v-icon x-large dark> mdi-arrow-decision </v-icon></v-btn
          >

          <v-list class="list mx-auto" v-if="showitems">
            <v-list-item-group color="pageheading">
              <v-list-item v-for="(item, i) in currenttask" :key="i">
                <v-list-item-icon>
                  <v-icon color="green" class="mr-3">mdi-check-circle</v-icon>
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
        "Protecting Platform Resources from Unwanted IPv6 Traffic",
        "Controlling Undesirable IPv4 Traffic",
        "Controlling Undesirable IPv6 Traffic",
        "Protecting Platform Resources from Unwanted IPv4 Data Plane Traffic",
        "Protecting Platform Resources from Unwanted IPv6 Data Plane Traffic",
        "Protecting Platform Resources from Unwanted IPv4 Management Plane Traffic",
        "Implementing Pass-through Action for Desired IPv4 Traffic",
        "Implementing Pass-through Action for Desired IPv6 Traffic",
        "Allowing Desired Encryption & Authentication Protocols' Traffic",
        "Implementing Global Resource Protection Mechanisms",
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
    loader: async function (value) {
      if (value == true) {
        for (var i = 0; i < this.configurationtasks.length; i++) {
          this.currenttask.push(this.configurationtasks[i]);
          await sleep(1200);
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
      this.$getAPI.post("copp/").then((response) => {
        this.devices = response.data;
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