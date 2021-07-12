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
        User Management
      <v-spacer></v-spacer>
      <v-btn class="pageheading white--text" small dense>Create New User</v-btn>
      </div>
    </v-col>
  </div>
</template>

<script>
export default {
  pageTitle: "My Profile",
  data() {
    return {
      loading: false,
      user: "",
    };
  },
  mounted() {
    this.$getAPI.get("users/user_detail").then((response) => {
      this.user = response.data;
    });
  },
};
</script>