<template>
  <div>
    <v-col>
      <div
        class="
          font-weight-light
          d-flex
          justify-end
          pa-4
          text-h4
          pageheading--text
        "
      >
        Topology
        <v-spacer></v-spacer>
        <v-menu offset-y>
          <template v-slot:activator="{ on, attrs }">
            <v-btn
              small
              class="mr-5 mt-4"
              color="pageheading white--text"
              v-bind="attrs"
              v-on="on"
            >
              <span>Set Interval</span>
            </v-btn>
          </template>
          <v-list dense>
            <v-list-item
              link
              v-for="(item, index) in timers"
              :key="index"
              @click="setPollInterval(index)"
            >
              <v-list-item-title link ripple dense
                >{{ item.title
                }}<v-icon
                  class="pl-7"
                  v-if="item.selected"
                  color="pageheading"
                  pl-3
                  small
                  >mdi-check-circle</v-icon
                ></v-list-item-title
              >
            </v-list-item>
          </v-list>
        </v-menu>
      </div>
      <v-divider class="my-2 mx-2"></v-divider>
    </v-col>
    <v-fab-transition>
      <v-container class="my-4 display-4">
        <network
          v-if="showtopology"
          style="
            height: 80%;
            position: absolute;
            right: 0px;
            left: 0px;
            top: 161px;
            bottom: 1px;
          "
          ref="network"
          class="network"
          :nodes="nodes"
          :edges="edges"
          :options="options"
        />
      </v-container>
    </v-fab-transition>
  </div>
</template>

<script>
import { Network } from "vue-vis-network";
import { Options } from "../visnetwork_config";

export default {
  name: "Topology",
  components: {
    Network,
  },
  data() {
    return {
      networkEvents: "",
      showtopology: false,
      network: null,
      options: Options,
      timers: [
        { title: "15s", id: 1, value: 15000, selected: false },
        { title: "30s", id: 2, value: 30000, selected: false },
        { title: "1m", id: 3, value: 60000, selected: false },
        { title: "2m", id: 4, value: 120000, selected: false },
        { title: "5m", id: 5, value: 300000, selected: false },
      ],
      nodes: [],
      edges: [],
      timer: "",
    };
  },
  methods: {
    setPollInterval(index) {
      for (let i = 0; i < this.timers.length; i++) {
        this.timers[i].selected = false;
      }
      clearInterval(this.timer);
      localStorage.setItem("neighborpoll", this.timers[index].value);
      this.timers[index].selected = true;
      this.timer = setInterval(() => {
        this.getNeighbors();
      }, this.timers[index].value);
    },
    getNeighbors() {
      this.$getAPI
        .get("neighbors/", {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("UserToken")}`,
          },
        })
        .then((response) => {
          for (var i = 0; i < response.data.result.nodes.length; i++) {
            if ("image" in response.data.result.nodes[i]) {
              let image = response.data.result.nodes[i].image;
              response.data.result.nodes[
                i
              ].image = require(`@/assets/${image}`);
            }
          }

          this.nodes = response.data.result.nodes;
          this.edges = response.data.result.edges;
          this.showtopology = true;
        });
    },
  },
  created() {
    var interval = null;
    if (localStorage.getItem("neighborpoll")) {
      interval = parseInt(localStorage.getItem("neighborpoll"));
      for (let i = 0; i < this.timers.length; i++) {
        if (this.timers[i].value == interval) {
          this.timers[i].selected = true;
          break
        }
      }
    } else {
      interval = 30000;
      this.timers[1].selected = true;
    }
    this.getNeighbors();
    this.timer = setInterval(() => {
      this.getNeighbors();
    }, interval);
  },
  destroyed() {
    clearInterval(this.timer);
  },
};
</script>