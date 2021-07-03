<template>
  <div>
    <v-col class="d-flex justify-end">
      <div class="font-weight-light pa-4 text-h4 pageheading--text">
        Inventory
      </div>
      <v-spacer></v-spacer>
      <v-dialog
        scrollable
        transition="dialog-bottom-transition"
        overlay-color="white"
        v-model="dialog"
        max-width="500px"
        overlay-opacity="0.55"
      >
        <template v-slot:activator="{ on, attrs }">
          <v-btn
            small
            color="pageheading white--text"
            class="mx-4 my-4"
            slot="activator"
            v-on="on"
            v-bind="attrs"
            >Add Device</v-btn
          >
        </template>
        <v-card>
          <!-- <v-toolbar color="primary" dark>Add Device</v-toolbar> -->
          <v-card-title>
            <div
              class="font-weight-light pa-4 text-h4 pageheading--text mx-auto"
            >
              Add Device
            </div>
          </v-card-title>
          <v-card-text>
            <div align="center">
              <v-form
                ref="form"
                autocomplete="off"
                class="px-2"
                style="width: 85%"
              >
                <v-text-field v-model="device.name" label="Name"></v-text-field>
                <v-text-field
                  v-model="device.ip"
                  label="IP Address"
                ></v-text-field>
                <v-text-field
                  v-model="device.username"
                  label="Username"
                ></v-text-field>
                <v-text-field
                  type="password"
                  v-model="device.password"
                  label="Password"
                ></v-text-field>
                <v-select
                  v-model="device.group"
                  :items="groups"
                  label="Group"
                  data-vv-name="select"
                  required
                ></v-select>
                <v-text-field
                  v-model="device.loop_back"
                  label="Logical Address"
                ></v-text-field>

                <v-checkbox
                  v-model="device.fhrp"
                  label="First Hop Redundancy"
                ></v-checkbox>
                <div v-if="device.fhrp">
                  <v-form>
                    <v-checkbox
                      v-model="device.primary_router"
                      label="Primary Router"
                    ></v-checkbox>
                    <v-text-field
                      v-model="device.virtual_ip"
                      label="Virtual IP"
                    ></v-text-field>
                    <v-text-field
                      v-model="device.fhrp_interface"
                      label="FHRP Interface"
                    >
                    </v-text-field>
                  </v-form>
                </div>
                <v-alert
                  transition="scale-transition"
                  :value="showsuccess"
                  dense
                  light
                  max-width="90%"
                  text
                  max-height="40px"
                  class="mt-3"
                  type="success"
                  >Successfully Added!</v-alert
                >
                <v-alert
                  transition="scale-transition"
                  :value="showerror"
                  dense
                  max-width="90%"
                  text
                  max-height="40px"
                  class="mt-3"
                  type="error"
                  >Invalid Form!</v-alert
                >
                <v-btn
                  style="width: 60%"
                  @click="submit()"
                  class="pageheading white--text mx-0 mt-3"
                  >Submit</v-btn
                >
              </v-form>
            </div>
          </v-card-text>
        </v-card>
      </v-dialog>
    </v-col>
    <div>
      <v-col class="d-flex justify-end">
        <v-text-field
          autocomplete="off"
          style="max-width: 12%"
          class="mx-5 pageheading--text"
          v-model="search"
          append-icon="mdi-magnify"
          label="Search"
          single-line
          hide-details
        ></v-text-field>
      </v-col>
    </div>
    <v-fab-transition>
      <v-skeleton-loader :loading="loading" type="table">
        <v-data-table
          flat
          :headers="headers"
          :items="allDevices"
          :search="search"
          class="elevation-1 mx-3 table-cursor"
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
      showerror: false,
      showsuccess: false,
      search: "",
      groups: ["Central Site", "Branch Site"],
      dialog: false,
      device: {},
      headers: [
        { text: "Site Name", align: "start", sortable: false, value: "name" },
        { text: "IP Address", value: "ip" },
        { text: "Hostname", value: "dev_name" },
        { text: "Managed", value: "is_configured" },
        { text: "Group", value: "group" },
        { text: "Vendor", value: "vendor" },
      ],
      allDevices: [],
    };
  },
  watch: {
    showsuccess(value) {
      if (value) {
        setTimeout(() => {
          this.showsuccess = false;
        }, 1800);
      }
    },
    showerror(value) {
      if (value) {
        setTimeout(() => {
          this.showerror = false;
        }, 1800);
      }
    },
  },
  mounted() {
    this.loading = true;
    this.getDevices();
  },
  methods: {
    GoToDevice(name) {
      this.$router.push("/host/" + name.name);
    },
    formatText(group) {
      if (group == true) {
        return (group = "Managed");
      } else {
        return (group = "UnManaged");
      }
    },
    submit() {
      // submit device form
      if (this.device.group == "Central Site") {
        this.device.group = "HUB";
      } else {
        this.device.group = "SPOKE";
      }
      if (this.device.fhrp == null) {
        this.device.fhrp = false;
      }
      var self = this;
      this.$getAPI
        .post("hosts", this.device)
        .then((response) => {
          if (response.status == 201) {
            self.showsuccess = true;
            self.$refs.form.reset(); // reset the form if submit is success
          }
        })
        .catch(function (error) {
          if (error.response.status != 201) {
            self.showerror = true;
          }
        })
        .then(() => {
          this.getDevices();
        });
    },

    getDevices() {
      // get add hosts
      this.$getAPI.get("hosts").then((response) => {
        this.allDevices = response.data;
        this.loading = false;
      });
      // # TODO - add logic for error handing
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
  },
};
</script>

<style>
.table-cursor tbody tr:hover {
  cursor: pointer;
}
</style>