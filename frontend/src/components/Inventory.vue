<template>
  <div>
    <v-col class="d-flex justify-end">
      <div class="font-weight-light pa-4 text-h4 pageheading--text">
        Inventory
      </div>
      <v-spacer></v-spacer>
    </v-col>
    <div>
      <v-col class="d-flex justify-end">
        <v-text-field
          autocomplete="off"
          style="max-width: 12%"
          class="mx-5 pageheading--text"
          v-model="search"
          append-icon="mdi-magnify"
          label="Search"
          single-line
          hide-details
        ></v-text-field>
      </v-col>
    </div>
    <v-fab-transition>
      <v-skeleton-loader :loading="loading" type="table">
        <v-data-table
          flat
          :headers="headers"
          :items="allDevices"
          :search="search"
          class="elevation-1 mx-3 table-cursor"
          @click:row="GoToDevice"
        >
          <template v-slot:[`item.is_configured`]="{ item }">
            <v-icon v-if="item.is_configured" class="pl-4" color="green"
              >mdi-check-circle</v-icon
            >
            <v-icon v-if="!item.is_configured" class="pl-4" color="red"
              >mdi-close-circle</v-icon
            >
          </template>
          <template v-slot:[`item.group`]="{ item }">
            <span>{{ showGroups(item.group) }}</span>
          </template>
        </v-data-table>
      </v-skeleton-loader>
    </v-fab-transition>
  </div>
</template>



<script>
export default {
  data() {
    return {
      loading: false,
      search: "",
      headers: [
        { text: "Site Name", align: "start", sortable: false, value: "name" },
        { text: "IP Address", value: "ip" },
        { text: "Hostname", value: "dev_name" },
        { text: "Managed", value: "is_configured" },
        { text: "Group", value: "group" },
        { text: "Vendor", value: "vendor" },
      ],
      allDevices: [],
    };
  },
  mounted() {
    this.loading = true;
    this.getDevices();
  },
  methods: {
    GoToDevice(name) {
      this.$router.push("/host/" + name.name);
    },
    formatText(group) {
      if (group == true) {
        return (group = "Managed");
      } else {
        return (group = "UnManaged");
      }
    },
    

    getDevices() {
      // get add hosts
      this.$getAPI.get("hosts").then((response) => {
        this.allDevices = response.data;
        this.loading = false;
      });
      // # TODO - add logic for error handing
    },
    showGroups(group) {
      if (group == "HUB") {
        return (group = "Central Site");
      } else if (group == "SPOKE") {
        return (group = "Branch");
      }
    },
    getColor(status) {
      if (status == false) return "orange";
      else return "green";
    },
  },
};
</script>

<style>
.table-cursor tbody tr:hover {
  cursor: pointer;
}
</style>