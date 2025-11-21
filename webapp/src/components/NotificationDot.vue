<template>
  <StyledTooltip
    v-if="isUnverified || hasUnverifiedUser"
    :delay="500"
    anchor-display="inline-block"
    anchor-class="notification-anchor"
  >
    <template #anchor>
      <span
        class="notification-dot"
        :class="{
          'user-unverified': isUnverified,
          'admin-unverified': hasUnverifiedUser,
        }"
        tabindex="0"
      ></span>
    </template>
    <template #content>
      <p v-if="isUnverified">
        Your account is currently unverified, please contact an administrator.
      </p>
      <p v-if="hasUnverifiedUser">There is an unverified user in the database</p>
    </template>
  </StyledTooltip>
</template>

<script>
import StyledTooltip from "@/components/StyledTooltip";

export default {
  components: {
    StyledTooltip,
  },
  computed: {
    isUnverified() {
      return this.$store.getters.getCurrentUserIsUnverified;
    },
    hasUnverifiedUser() {
      return this.$store.getters.getHasUnverifiedUser;
    },
  },
};
</script>

<style scoped>
.notification-anchor {
  position: absolute;
  top: 0;
  left: 0;
  width: 0;
  height: 0;
}

.notification-dot {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 1;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.user-unverified {
  background-color: red !important;
}

.admin-unverified {
  background-color: orange;
}
</style>
