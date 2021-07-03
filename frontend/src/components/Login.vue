<template>
  <v-app id="app">
    <v-img transition="slide-x-transition" src="../assets/uurniklogo.png" max-width="30%"  max-height="40%"></v-img>
    <v-container fill-height app class="fg">
      <v-flex class="mx-auto" md3 lg3 xl2  xs7>
        <v-form
          @submit.prevent="login()"
          class="mx-auto"
          ref="form"
          lazy-validation
        >
          <div align="center">
            <h2 class="mb-4 white--text">Login</h2>
            <v-text-field prepend-icon="mdi-account"
              dark
              autocomplete="off"
              v-model="username"
              label="Username"
              required
            ></v-text-field>

            <v-text-field
              prepend-icon="mdi-form-textbox-password"
              dark
              type="password"
              v-model="password"
              label="Password"
              required
            ></v-text-field>

            <v-btn class="ml-4"
              :loading="loading"
              type="submit"
              style="width: 65%"
              color="pageheading white--text"
            >
              Login
            </v-btn>
          </div>
        </v-form>
      </v-flex>
      <v-snackbar timeout="-1" color="#C62828" v-model="incorrectAuth">
        Invalid Username or Password!
        <v-btn @click="incorrectAuth = false" outlined class="ml-4" text
          >Close</v-btn
        >
      </v-snackbar>
    </v-container>
  </v-app>
</template>



<script>
export default {
  name: "login",
  data() {
    return {
      username: "",
      password: "",
      incorrectAuth: false,
      snackbar: true,
      loading: false,
    };
  },
  methods: {
    login() {
      this.loading = true;
      this.$store
        .dispatch("userLogin", {
          username: this.username,
          password: this.password,
        })
        .then(() => {
          this.loading = false;
          this.$router.push({ path: "/" });
        })
        .catch((err) => {
          console.log(err);
          this.incorrectAuth = true;
          this.loading = false;
        });
    },
  },
};
</script>


<style scoped>
#app {
  background-image: url("../assets/SD_Wan.jpeg");
  min-height: 100%;
  background-size: cover;
  background-repeat: no-repeat;
  background-position: center center;
}
</style>