<template>
  <div>
    <v-col>
      <div
        class="font-weight-light d-flex justify-end pa-4 text-h4 pageheading--text"
      >
        Topology
        <v-spacer></v-spacer>
        <v-icon style="cursor: pointer" class="pt-1 pb-0">mdi-reload</v-icon>
      </div>
      <v-divider class="my-2 mx-2"></v-divider>
    </v-col>
    <v-fab-transition>
    <v-container class="my-4 display-4">
        <network v-if="showtopology"
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
      showtopology: false,
      network: null,
      options: Options,
      nodes: [],
      edges: []
    };
  },
  mounted() {
    this.$getAPI
    .get("neighbors/",{
          headers: {
            Authorization: `Bearer ${localStorage.getItem("UserToken")}`,
          },
        })
    .then(response => {
      for ( var i=0; i < response.data.result.nodes.length; i++) {
        if ("image" in response.data.result.nodes[i]) {
          let image = response.data.result.nodes[i].image
          response.data.result.nodes[i].image = require(`@/assets/${image}`)
          
        }
      }
      
      this.nodes =  response.data.result.nodes;
      this.edges = response.data.result.edges;
      this.showtopology = true
      // this.$refs.network.fit({
      // animation: {
      //   duration: 2000,
      // },
      // })
    })
  }
};
</script>

<style scoped lang="scss">
</style>