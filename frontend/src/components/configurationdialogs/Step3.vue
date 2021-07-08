<template>
  <v-container fill-height class="mb-5">
    <v-btn
      v-if="showbtn"
      @click="getRoutes()"
      class="mx-auto"
      fab
      dark
      x-large
      color="pageheading"
      width="90px"
      height="90px"
    >
      <v-icon x-large dark>mdi-router</v-icon></v-btn
    >
    <v-progress-linear
      v-if="loader"
      indeterminate
      color="pageheading"
    ></v-progress-linear>
    <v-col v-if="showroutes" class="d-flex justify-start">
      <v-flex lg11 md12 xs8 justify-start>
        <v-form autocomplete="off" v-for="device in routes" :key="device.name">
          <h1 class="py-3">{{ device.name }}</h1>
          <v-checkbox
            color="pageheading"
            class="pa-0 pl-4"
            v-for="(route, index) in device.routes"
            :key="index + 8"
            dense
            v-model="postroutes[device.name][route]"
            :label="route"
          ></v-checkbox>
            <v-chip
              v-for="(addedroute, rindex) in chips[device.name]"
              :key="rindex"
              @click:close="deleteRoutes(addedroute, device.name)"
              class="mb-4 ml-3 white--text"
              close
              color="pageheading"
              >{{ addedroute }}</v-chip
            >

          <v-row align-self="left">
            <v-flex md5 lg3 xs6>
              <v-text-field
                dense
                outlined
                class="pageheading--text pa-0 pl-4 ml-2 mt-2"
                height="18px"
                v-model="customroute[device.name]"
                label="Route"
                placeholder="x.x.x.x/x x.x.x.x"
              ></v-text-field>
            </v-flex>
            <v-btn
              color="pageheading white--text ml-2 mt-2"
              style="margin-top: 5px"
              meduim
              @click="addCustomRoute(device.name, customroute[device.name])"
              >Add</v-btn
            >
          </v-row>
          <!-- <v-divider></v-divider> -->
        </v-form>
        <v-btn class="pageheading white--text mt-3" @click="postRoutes()"
          >submit</v-btn
        >
      </v-flex>
    </v-col>
  </v-container>
</template>

<script>

// import Vue from 'vue'
export default {
  name: "Step3",
  data() {
    return {
      routes: null,
      postroutes: {},
      formatedroutes: [],
      showroutes: false,
      finalroutes: [],
      customroute: {},
      showbtn: true,
      loader: false,
      chips: {},
    };
  },
  methods: {
    getRoutes() {
      this.loader = true;
      this.showbtn = false;
      this.$getAPI.get("routing/").then((response) => {
        this.routes = response.data;
        this.loader = false;
        this.showroutes = true;
        for (const value of Object.values(response.data)) {
          this.chips[value.name] = [];
          this.postroutes[value.name] = { custom: [] };
        }
      });
    },
    postRoutes() {
      for (const [key, value] of Object.entries(this.postroutes)) {
        this.formatedroutes[key] = { routes: [], custom: [] };
        for (const [ikey, exists] of Object.entries(value)) {
          if (ikey == "custom") {
            this.formatedroutes[key].custom = exists;
          }
          if (exists == true) {
            this.formatedroutes[key].routes.push(ikey);
          }
        }
      }
      for (let device in this.formatedroutes) {
        this.finalroutes.push({
          name: device,
          routes: this.formatedroutes[device].routes,
          custom: this.formatedroutes[device].custom,
        });
      }
      console.log(this.finalroutes)
      this.$getAPI.post("routing/", this.finalroutes)
      .then(() => {
        this.finalroutes = []
      })
      this.$store.state.e1 += 1
    },
    addCustomRoute(name, route) {
      if (route !== "") {
        this.postroutes[name].custom.push(route);
        this.chips[name] = this.postroutes[name].custom
        console.log(this.chips[name])
      }
      this.customroute[name] = "";
    },
    deleteRoutes(route, name) {
      this.chips[name].splice(this.chips[name].indexOf(route), 1);
      this.chips = Object.assign({}, this.chips, { name: this.chips[name] })
      console.log(this.chips[name])
      for (const key of Object.keys(this.postroutes)) {
        if (key == name) {
          this.postroutes[key].custom = this.chips[name]

        }
      }
    },
  },
};
</script>
