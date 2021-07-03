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
        <v-btn icon dark @click="$store.state.menuDialogs['3'] = false;">
          <v-icon>mdi-close</v-icon>
        </v-btn>
        <v-toolbar-title>Change IPsec Keys</v-toolbar-title>
        <v-spacer></v-spacer>
      </v-toolbar>

    <v-card-text>

    </v-card-text>
      <v-container fill-height class="mb-5 justify-center">
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
          <v-flex md6 xs9 lg3 v-if="showform">
        <v-form  ref="form" autocomplete="off">
            <div align="center">
              <v-text-field
                type="password"
                class="pageheading--text pa-0 ma-0"
                v-model="oldkey"
                label="Current Key"
              ></v-text-field>
              <v-text-field
                type="password"
                class="pageheading--text pa-0 ma-0"
                v-model="newkey"
                label="New Key"
              ></v-text-field>
              <v-text-field
                type="password"
                class="pageheading--text pa-0 ma-0"
                v-model="confirm"
                label="Confirm Key"
              ></v-text-field>
              <v-btn @click="postKeys()" class="pageheading white--text">Submit</v-btn>
            </div>
          </v-form>
          </v-flex>
      </v-container>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  data() {
    return {
      showstatus: false,
      dialog: true,
      showform: true,
      loader: false,
      devices: [],
      showbtn: true,
      oldkey: "",
      newkey: "",
      confirm: "",
    };
  },
  mounted() {
    this.showstatus = false
    this.showform = true
  },
  methods: {
    postKeys() {
      this.loader = true
      this.showform = false
      this.$getAPI.put("change-keys-ipsec/", {
        old_key: this.oldkey,
        new_key: this.newkey,
      }).then((response) => {
        this.devices = response.data
        this.loader = false
        this.$refs.form.reset()
        this.showform = false
        this.showstatus = true
      })
    },
  },
};
</script>

<style>
</style>