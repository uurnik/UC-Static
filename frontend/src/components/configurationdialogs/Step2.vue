<template>
  <v-container fill-height class="mb-5 justify-center">
    <v-flex md4 lg3 class="pa-4">
      <v-form ref="form"  autocomplete="off">
        <div align="center">

        <v-select  outlined class="pa-0 ma-0 pageheading--text"
      v-model="type"
      :items="items"
      label="Access Type"
      required
      return-object
    ></v-select>
        <v-text-field class="pageheading--text pa-0 ma-0" outlined v-model="dns" label="DNS"></v-text-field>
        <v-btn @click="Submit()"  class="pageheading white--text">Submit</v-btn>
        </div>
      </v-form>
    </v-flex>
  </v-container>
</template>


<script>
export default {
  data() {
    return {
      type: "",
      dns: "",
      items:[
        'Direct Internet Access',
        'Private WAN + DIA',
        'Private WAN + DIA + Addons'
      ]
    };
  },
  methods: {
    reset() {
      this.$refs.form.reset()
    },
    Submit() {
      if (this.type == "Direct Internet Access") {
        this.type = 2
      } else if (this.type == "Private WAN + DIA") {
        this.type = 1
      } else {
        this.type = 3
      }
      this.$store.dispatch('commitparams',{accesstype:this.type ,dns:this.dns})
      this.reset()
      this.$store.state.e1 = 3
    }
  }
};
</script>

