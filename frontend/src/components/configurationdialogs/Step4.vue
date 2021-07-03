<template>
  <v-container fill-height class="mb-5">
    <v-btn v-if="showbtn"
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
                <th>Success</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in devices" :key="item.name">
                <td>{{ item.name }}</td>
                <td v-if="item.failed == false">
                  <v-icon class="pl-4" color="green">mdi-check-circle</v-icon>
                </td>
                <td v-if="item.failed == true">
                  <v-icon class="pl-4" color="red">mdi-close-circle</v-icon>
                </td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>
      </v-flex>
    </v-col>
  </v-container>
</template>

<script>


export default {
  name: "Step4",
  data() {
    return {
      dns: "",
      loader: false,
      showtable: false,
      showbtn: true,
      devices: [],
      showstatus:false
    };
  },
  mounted() {
    this.reset();
  },
  methods: {
    reset() {
      this.loader = false;
      this.showbtn = true;
      this.showstatus = false;
    },

    Deploy() {
      this.showbtn = false
      this.loader = true;
      this.dns = { dns: this.$store.state.dns };
      this.$getAPI
        .post(`configure/${this.$store.state.accesstype}/`, this.dns)
        .then((response) => {
          this.devices = response.data;
          this.loader = false;
          this.showstatus = true;
          this.$store.state.notConfigured = false
        });
    },
  },
};
</script>
