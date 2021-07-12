<template>
  <v-container fill-height class="mb-5">
    <v-btn
      v-if="showbtn"
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
    <span v-if="loader" class="mx-auto">{{ currenttask }}</span>

    <v-col v-if="showstatus" class="d-flex justify-center">
      <v-flex md10 xs12 lg8>
        <v-simple-table class="mx-auto align-center">
          <template v-slot:default>
            <thead>
              <tr>
                <th>Name</th>
                <th>Success</th>
                <th v-for="(task, index) in devices[0].tasks" :key="index + 1">
                  {{ task }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in devices" :key="item.name">
                <td>
                  <h4 class="grey--text text--darken-3">{{ item.name }}</h4>
                </td>
                <td v-if="item.failed == false">
                  <v-icon class="pl-4" color="green">mdi-check-circle</v-icon>
                </td>
                <td v-if="item.failed == true">
                  <v-icon class="pl-4" color="red">mdi-close-circle</v-icon>
                </td>
                <td v-for="task in item.tasks" :key="task.index + 3">
                  <v-icon class="pl-4" color="green">mdi-check-circle</v-icon>
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

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export default {
  name: "Step4",
  data() {
    return {
      configurationtasks: [
        "Settings up devices",
        "Creating Overlay Network",
        "Setting up Encryption",
        "Configuring Segmented Routing",
        "Advertising Routes",
      ],
      currenttask: "",
      dns: "",
      loader: false,
      showtable: false,
      showbtn: true,
      devices: [],
      showstatus: false,
    };
  },
  mounted() {
    this.reset();
  },
  watch: {
    loader: async function(value) {
      if (value == true) {
        for (var i = 0; i < this.configurationtasks.length; i++) {
            // if (this.$store.state.accesstype != 2 && i != 3 ) {
            this.currenttask = this.configurationtasks[i]
            await sleep(2200)
            // }

        }
      }

    }
  },
  methods: {
    reset() {
      this.loader = false;
      this.showbtn = true;
      this.showstatus = false;
    },

    Deploy() {
      this.showbtn = false;
      this.loader = true;
      this.dns = { dns: this.$store.state.dns };
      this.$getAPI
        .post(`configure/${this.$store.state.accesstype}/`, this.dns)
        .then((response) => {
          this.devices = response.data;
          this.loader = false;
          this.showstatus = true;
          this.$store.state.notConfigured = false;
        });
    },
  },
};
</script>
