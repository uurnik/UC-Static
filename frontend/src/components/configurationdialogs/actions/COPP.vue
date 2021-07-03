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
        <v-btn
          icon
          dark
          @click="
            $store.state.menuDialogs['1'] = false;
          "
        >
          <v-icon>mdi-close</v-icon>
        </v-btn>
        <v-toolbar-title>Control Plane Policing</v-toolbar-title>
        <v-spacer></v-spacer>
      </v-toolbar>

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
          <v-progress-linear
            v-if="loader"
            indeterminate
            color="pageheading"
          ></v-progress-linear>

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
                      <td>{{ item.name }}</td>
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
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  data() {
    return {
      showstatus: false,
      dialog: true,
      loader: false,
      desserts: [],
      devices: [],
      showbtn: true,
    };
  },
  methods: {
    getStatus() {
      this.loader = true;
      this.showbtn=false;
      this.$getAPI
        .post("copp/")
        .then((response) => {
          this.devices = response.data
          this.loader = false;
          this.showstatus = true;
        });
    },
  },
};
</script>

<style>
</style>