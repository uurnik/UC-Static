<template>
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
        <div class="font-weight-light pa-4 text-h4 pageheading--text mx-auto">
          Add Device
        </div>
      </v-card-title>
      <v-card-text>
        <div align="center">
          <v-form ref="form" autocomplete="off" class="px-2" style="width: 85%">
            <v-text-field v-model="device.name" label="Name"></v-text-field>
            <v-text-field v-model="device.ip" label="IP Address"></v-text-field>
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
</template>

<script>
export default {
  data() {
    return {
      showerror: false,
      showsuccess: false,
      device: {},
      groups: ["Central Site", "Branch Site"],
    };
  },
  methods: {
    getDevices() {
      this.$getAPI.get("hosts").then((response) => {
        this.$store.state.devices = response.data;
      });
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
};
</script>

<style>
</style>