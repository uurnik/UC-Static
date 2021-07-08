<template>
  <div>
    <v-col class="d-flex justify-start">
      <div class="font-weight-light pa-4 text-h4 pageheading--text">
        Configuration
      </div>
      <v-spacer></v-spacer>
      <AddDevice/>
      <v-dialog
        style="height: 100%"
        overlay-opacity="0.75"
        scrollable
        fullscreen
        v-model="dialog"
        transition="dialog-bottom-transition"
      >
        <template v-slot:activator="{ on, attrs }">
          <v-btn
            small
            color="pageheading"
            class="mr-2 mt-4"
            dark
            v-bind="attrs"
            v-on="on"
          >
            <span>Deployment</span>
          </v-btn>
        </template>
        <v-card class="white white--text" height="100%">
          <v-toolbar max-height="65px" dark color="pageheading">
            <v-btn
              icon
              dark
              @click="
                dialog = false;
                $store.state.e1 = 1;
              "
            >
              <v-icon>mdi-close</v-icon>
            </v-btn>
            <v-toolbar-title>Configuration</v-toolbar-title>
            <v-spacer></v-spacer>
          </v-toolbar>

          <v-card-title>
            <span class="font-weight-light pa-4 text-h4 pageheading--text">{{
              steptitle
            }}</span>
          </v-card-title>
          <v-card-text>
            <Step1 v-if="$store.state.e1 == 1" />
            <Step2 v-if="$store.state.e1 == 2" />
            <Step3 v-if="$store.state.e1 == 3" />
            <Step4 v-if="$store.state.e1 == 4" />
            <!-- Action buttons -->
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn v-if="showcardaction" color="pageheading white--text mb-2 mr-2" @click="$store.state.e1 += 1">
              {{ cardaction }}
            </v-btn>
          </v-card-actions>
          <!-- /Action buttons -->

          <!-- Footer -->
          <v-footer padless bottom>
            <v-flex>
              <v-stepper v-model="$store.state.e1">
                <v-stepper-header>
                  <v-stepper-step :complete="$store.state.e1 > 1" step="1">
                    Discover Devices
                  </v-stepper-step>
                  <v-divider></v-divider>
                  <v-stepper-step :complete="$store.state.e1 > 2" step="2">
                    Select Access Type & DNS
                  </v-stepper-step>
                  <v-divider></v-divider>
                  <v-stepper-step :complete="$store.state.e1 > 3" step="3"
                    >Discover Networks</v-stepper-step
                  >
                  <v-divider></v-divider>
                  <v-stepper-step :complete="$store.state.e1 > 4" step="4"
                    >Deploy</v-stepper-step
                  >
                </v-stepper-header>
              </v-stepper>
            </v-flex>
          </v-footer>
          <!-- /Footer -->
        </v-card>
      </v-dialog>

      <v-menu offset-y>
        <template v-slot:activator="{ on, attrs }">
          <v-btn
            small
            :disabled="!stats[0].status"
            class="mr-5 mt-4"
            color="pageheading white--text"
            v-bind="attrs"
            v-on="on"
            ><v-icon color="white" left>mdi-menu</v-icon>
            <span>Actions</span>
          </v-btn>
        </template>
        <v-list dense>
          <v-list-item
            @click="$store.state.menuDialogs[item.id] = true"
            link
            v-for="(item, index) in menuitems"
            :key="index"
          >
            <v-list-item-title link ripple>{{ item.title }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>

      <COPP v-if="$store.state.menuDialogs['1']" />
      <DeviceHardening v-if="$store.state.menuDialogs['2']" />
      <ChangeKeys v-if="$store.state.menuDialogs['3']" />
    </v-col>

    <v-row>
      <v-col v-for="(stat, index) in stats" :key="index">
        <v-card
          elevation="2"
          class="mx-auto"
          max-width="340"
          height="85px"
          outlined
        >
          <v-list-item three-line>
            <v-list-item-content>
              <v-list-item-title class="font-weight-light text-h6 mb-1">
                {{ stat.name }}
              </v-list-item-title>
              <v-list-item-subtitle v-if="index == 0">{{
                stat.accesstype
              }}</v-list-item-subtitle>
            </v-list-item-content>

            <v-avatar text tile rounded size="40">
              <v-icon v-if="stat.status" color="success" text>{{
                stat.icon
              }}</v-icon>
              <v-icon v-if="!stat.status" color="red" text>{{
                stat.icon
              }}</v-icon>
            </v-avatar>
          </v-list-item>
        </v-card>
      </v-col>
    </v-row>

    <v-divider class="ma-5"></v-divider>
    <v-col>
      <v-card flat>
        <!-- <v-card-title align-center>
              <h2 class="mx-auto my-5 font-weight-light pageheading--text">
                Sites
              </h2>
            </v-card-title> -->

        <v-fab-transition>
          <v-skeleton-loader :loading="loading" type="table">
            <v-data-table
              flat
              hide-default-footer
              :headers="headers"
              :items="$store.state.devices"
              class="elevation-0 mx-3 mt-5 table-cursor"
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
      </v-card>
    </v-col>
  </div>
</template>



<script>
import Step1 from "./configurationdialogs/Step1";
import Step2 from "./configurationdialogs/Step2";
import Step3 from "./configurationdialogs/Step3";
import Step4 from "./configurationdialogs/Step4";
import DeviceHardening from "./configurationdialogs/actions/DeviceHardening";
import ChangeKeys from "./configurationdialogs/actions/ChangeKeys";
import COPP from "./configurationdialogs/actions/COPP";
import AddDevice from "./AddDevice";

export default {
  components: {
    Step1,
    Step2,
    Step3,
    Step4,
    DeviceHardening,
    ChangeKeys,
    COPP,
    AddDevice,
  },

  data() {
    return {
      stats: [
        {
          name: "Deployment Status",
          status: !this.$store.state.notConfigured,
          accesstype: this.$store.state.accessType,
          icon: "mdi-moon-new",
        },
        {
          name: "Control Plane Policing",
          status: this.$store.state.copp,
          icon: "mdi-moon-new",
        },
        {
          name: "Device Hardening",
          status: this.$store.state.devicehardening,
          icon: "mdi-moon-new",
        },
      ],
      steptitle: "Discover Devices",
      cardaction: "Next",
      show: true,
      adddialog: false,
      dialog: false,
      notifications: false,
      sound: true,
      widgets: false,
      allDevices: [],
      loading: false,

      menuitems: [
        { title: "COPP", id: "1" },
        { title: "Device Hardening", id: "2" },
        { title: "Change IPsec Keys", id: "3" },
      ],
      headers: [
        { text: "Site Name", align: "start", sortable: false, value: "name" },
        { text: "IP Address", value: "ip" },
        { text: "Hostname", value: "dev_name" },
        { text: "Managed", value: "is_configured" },
        { text: "Group", value: "group" },
        { text: "Vendor", value: "vendor" },
      ],
    };
  },
  computed: {
    showcardaction: function() {
      if (this.$store.state.e1 == 2 ||  this.$store.state.e1 == 3){
        return false
      } else {
        return true
      }
    }
  },
  beforeMount() {
    this.DeployementStatus();
  },
  mounted() {
    this.loading = true;
    this.getDevices();
  },
  methods: {
    DeployementStatus() {
      this.$getAPI.get("access-type/").then((response) => {
        this.$store.state.copp = response.data.copp_configured;
        this.$store.state.devicehardening = response.data.device_hardening;
        this.stats[1].status = this.$store.state.copp;
        this.stats[2].status = this.$store.state.devicehardening;

        if (response.data.access_type != null) {
          this.$store.state.notConfigured = false;
          this.stats[0].status = true;
        }
      });
    },
    getDevices() {
      this.$getAPI.get("hosts").then((response) => {
        this.$store.state.devices = response.data;
        this.loading = false;
      });
    },
    showGroups(group) {
      if (group == "HUB") {
        return (group = "Central Site");
      } else if (group == "SPOKE") {
        return (group = "Branch");
      }
    },
  },
  watch: {
    '$store.state.e1': function (value) {
      if (value == 1) {
        this.steptitle = "Discover Devices";
        this.cardaction = "Next";
      } else if (value == 2) {
        this.steptitle = "Select Access Type & DNS";
      } else if (value == 3) {
        this.steptitle = "Discover Networks";
      } else if (value == 4) {
        this.steptitle = "Deploy";
        this.cardaction = "Finish";
      } else if (value > 4) {
        this.dialog = false;
        this.$store.state.e1 = 1;
        this.cardaction = "Next";
      }
    },
  },
};
</script>

<style scoped>
</style>