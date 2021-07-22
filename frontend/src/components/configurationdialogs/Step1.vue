<template>
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

      <v-icon x-large dark> mdi-bullseye </v-icon></v-btn
    >
    <v-col v-if="showstatus" class="d-flex justify-center">
      <v-flex md7 xs9 lg5>
        <v-simple-table class="mx-auto align-center">
          <template v-slot:default>
            <thead>
              <tr>
                <th>Name</th>
                <th>Discovered</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in devices" :key="item.name">
                <td><h4 class="grey--text text--darken-3">{{ item.name }}</h4></td>
                <td v-if="item.failed == false"><v-icon class="pl-4" color="green">mdi-check-circle</v-icon></td>
                <td v-if="item.failed == true"><v-icon class="pl-4" color="red">mdi-close-circle</v-icon></td>
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
  name: "Step1",
  data() {
    return {
      showstatus: false,
      devices: [],
      showbtn: true,
    };
  },
  destroyed() {
    this.$store.state.toggleloader = false;
    this.showstatus = false;
    this.devices = []
  },
  methods: {
    getStatus() {
      this.$store.state.toggleloader = true;
      this.showbtn=false;
      this.$getAPI
        .get("facts/")
        .then((response) => {
          this.devices = response.data
          this.$store.state.toggleloader = false;
          this.showstatus = true;
        });
    },
  },
};
</script>
