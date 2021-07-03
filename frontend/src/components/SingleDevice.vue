<template>
  <div>
    <v-row>
      <v-col>
        <div class="font-weight-light pa-4 ml-3 text-h4 pageheading--text">
          {{ device.name }}
        </div>
        <v-flex align-self-start lg3 md4>
          <v-card flat>
            <v-card-text class="pb-0 ma-0"
              ><v-col class="d-flex justify-space-between pa-0 pb-1 ml-4 ma-0"
                ><strong>Hostname</strong>
                <span>{{ device.dev_name }}</span></v-col
              ></v-card-text
            >
            <v-card-text class="pb-0 ma-0"
              ><v-col class="d-flex justify-space-between pa-0 pb-1 ml-4 ma-0"
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
          </v-card>
        </v-flex>
        <v-flex
          class="mt-12 mx-auto"
          lg10
          md10
          justify-center
          align-self-center
        >
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
                ></template>
                <template v-slot:[`item.status`]="{ item }">
                  <v-icon v-if="item.status == 'up'" class="pl-4" color="green"
                    >mdi-check-circle</v-icon
                  >
                <v-chip v-if="item.status == 'administratively down'" class="pl-4" color="orange"
                  >{{ item.status }}</v-chip
                >
                <v-icon v-if="item.status == 'down'" class="pl-4" color="red"
                  >mdi-close-circle</v-icon
                >
                </template>
                </v-data-table
              >
            </v-skeleton-loader>
          </v-card>
        </v-flex>
      </v-col>
    </v-row>
  </div>
</template>

<script>
export default {
  props: ["name"],
  data() {
    return {
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
  mounted() {
    this.$getAPI
      .get("hosts?name=" + this.name)
      .then((response) => {
        this.device = response.data;
      });
    this.$getAPI
      .get(`interfaces/${this.name}/`)
      .then((response) => {
        this.interfaces = response.data;
        this.loading = false;
      });
  },
};
</script>

<style lang="scss" scoped></style>
