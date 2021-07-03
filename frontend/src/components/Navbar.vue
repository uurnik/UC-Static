<template>
  <nav>
    <v-toolbar flat>
      <v-app-bar-nav-icon  @click.stop="drawer = !drawer"></v-app-bar-nav-icon>
      <v-toolbar-title class="text-uppercase grey--text">
        <span class="font-weight-light">Uurnik</span>
        <span>Connect</span>
      </v-toolbar-title>
      <v-spacer></v-spacer>
      <v-icon style="cursor: pointer" @click="logout()">mdi-logout</v-icon>
    </v-toolbar>
    <v-navigation-drawer v-model="drawer" app>
      <v-list nav>
        <v-list-item route to="/" active-class="white--text">
          <v-img src="@/assets/uurnikblack.png"></v-img>
        </v-list-item>
        <v-list-item-group primary active-class="blue--text">
          <v-list-item route to="/">
            <v-icon left>mdi-view-dashboard</v-icon>
            <v-list-item-title>Dashboard</v-list-item-title>
          </v-list-item>
          <v-list-item route to="/inventory">
            <v-icon left>mdi-router</v-icon>
            <v-list-item-title>Inventory</v-list-item-title>
          </v-list-item>
          <v-list-item route to="/configuration">
            <v-icon left>mdi-cog</v-icon>
            <v-list-item-title>Configuration</v-list-item-title>
          </v-list-item>
          <v-list-item route to="/topology">
            <v-icon left>mdi-gamepad-circle</v-icon>
            <v-list-item-title>Topology</v-list-item-title>
          </v-list-item>
          <v-list-item route to="/troubleshoot">
            <v-icon left>mdi-eye-minus</v-icon>
            <v-list-item-title>TroubleShoot</v-list-item-title>
          </v-list-item>
        </v-list-item-group>
      </v-list>
    </v-navigation-drawer>
  </nav>
</template>

<script>
export default {
  data() {
    return {
      drawer: false,
    };
  },
  methods: {
    logout() {
      this.$store.dispatch("userLogout").then(() => {
        this.$router.push({ name: "login" });
      });
    },
  },
};
</script>