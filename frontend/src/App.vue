<template>
  <v-app>
    <v-main>
      <div>
        <Navbar v-if="!$route.meta.hidenavbar" />
      </div>
      <v-slide-x-transition mode="out-in">
        <router-view />
      </v-slide-x-transition>
    </v-main>
    <Footer v-if="!$route.meta.hidenavbar" />
  </v-app>
</template>

<script>
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";

export default {
  name: "App",
  components: {
    Navbar,
    Footer,
  },

  data: () => ({}),
  created: function () {
    var self = this
    this.$getAPI.interceptors.response.use(undefined, function (err) {
      return new Promise(function () {
        if (err.response.status === 401) {
          console.log(err.response.status)
          self.$store.dispatch('userLogout')
          self.$router.push({name:'login'})
        }
        throw err;
      });
    });
  }
};
</script>
