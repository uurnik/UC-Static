<template>
  <div>
    
    <v-col>
      <img src="frontend/src/assets/cisco.png" alt="">
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
    <v-row justify="center">
      <v-dialog v-model="dialog" max-width="450" @click:outside="pingresult = '';dest = '' " >
        <v-card>
          <v-card-title
            class="font-weight-medium pa-4 text-h6 pageheading--text mx-auto"
          >
            Connectivity Test
          </v-card-title>
          <v-text-field
            class="pl-5 pr-5 ma-3 pageheading--text"
            v-model="dest"
            label="Destination IP Address"
          ></v-text-field>
          <v-card-text
            class="font-weight-light text-subtitle-2"
            v-if="pingresult"
          >
            {{ pingresult }}
          </v-card-text>

          <v-card-actions>
            <v-card-text @click="GoToDevice()" class="pageheading--text" style="cursor: pointer;" >
              Device Details
            </v-card-text>
            <v-spacer></v-spacer>
            <v-progress-circular
            v-if="pingloader"
            class="mr-3"
              indeterminate
              color="pageheading"
            ></v-progress-circular>
            <v-btn class="pageheading white--text" @click="Ping()">
              Ping
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-row>
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
          @select-node="netWorkEvent()"
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
      dialog: false,
      devicetoping: null,
      pingresult: null,
      networkEvents: "",
      showtopology: false,
      dest: "",
      network: null,
      pingloader: false,
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
    GoToDevice() {
      let name = ""
      for (let i = 0; i < this.nodes.length; i++) {

        if (this.nodes[i].label == this.devicetoping) {
          name = this.nodes[i].name
          break
        }
      }
      this.$router.push("/host/" + name);

    },
    Ping() {
      this.pingloader = true
      this.$getAPI
        .get("monitoring/testconn/?name=" + this.devicetoping + "&dest=" + this.dest)
        .then((response) => {
          this.pingloader = false
          this.pingresult = response.data.result;
        });
    },
    netWorkEvent() {
      let nodeid = this.$refs.network.getSelection().nodes[0];
      for (let i = 0; i < this.nodes.length; i++) {
        if (this.nodes[i].id == nodeid) {
          this.devicetoping = this.nodes[i].label;
          this.dialog = true;
          break;
        }
      }
    },

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
      this.$getAPI.get("monitoring/topology/get_neighbors").then((response) => {
        for (var i = 0; i < response.data.result.nodes.length; i++) {
          if ("image" in response.data.result.nodes[i]) {
            let image = response.data.result.nodes[i].image;
            response.data.result.nodes[i].image = require(`@/assets/${image}`);
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
          break;
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

<style >

#tooltip-hr {
  margin-top:7px;
  margin-bottom: 5px;
  color:#B0BEC5;
  height:0px;
  border-color: #B0BEC5;
  border: solid;
  border-width: thin 0 0 0;

}

div.tooltip-element {
  color: rgba(0, 0, 0, 0.6);
    padding: 0;
    line-height: 2rem;
}

div.tooltip-content {
  margin: 0;
  padding: 0;
  display:flex;
  flex-direction: column;
  color:#f58319;
  font-family: "Roboto", sans-serif !important;
  text-align: center;
  justify-content: center;
  flex-wrap: wrap;
}

div.vis-tooltip {
  background-color: #ffffff;
  /* border: #42A5F5 solid 2px; */
  border: none;
  width:27em;
  height: 150px;
  color: rgba(0, 0, 0, 0.87);
  text-decoration: none;
  
}

</style>