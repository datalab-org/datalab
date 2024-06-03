<template>
  <span
    v-if="isUnverified || hasUnverifiedUser"
    ref="tooltipTarget"
    class="notification-dot"
    :class="{
      'user-unverified': isUnverified,
      'admin-unverified': hasUnverifiedUser,
    }"
    @mouseenter="delayedShowTooltip"
    @mouseleave="hideTooltip"
    @focus="delayedShowTooltip"
    @blur="hideTooltip"
  ></span>
  <div id="tooltip" ref="tooltipContent" role="tooltip">
    <p v-if="isUnverified">
      Your account is currently unverified, please contact an administrator.
    </p>
    <p v-if="hasUnverifiedUser">There is an unverified user in the database</p>
  </div>
</template>

<script>
import { createPopper } from "@popperjs/core";

export default {
  data() {
    return {
      tooltipDisplay: false,
      tooltipTimeout: null,
      popperInstance: null,
    };
  },
  computed: {
    isUnverified() {
      return this.$store.getters.getCurrentUserIsUnverified;
    },
    hasUnverifiedUser() {
      return this.$store.getters.getHasUnverifiedUser;
    },
  },
  mounted() {
    const tooltipTarget = this.$refs.tooltipTarget;
    const tooltipContent = this.$refs.tooltipContent;
    this.popperInstance = createPopper(tooltipTarget, tooltipContent, {
      placement: "bottom-start",
      strategy: "fixed",
      modifiers: [
        {
          name: "offset",
          options: {
            offset: [0, 4],
          },
        },
      ],
    });
  },
  methods: {
    delayedShowTooltip() {
      this.tooltipTimeout = setTimeout(() => {
        this.$refs.tooltipContent.setAttribute("data-show", "");
        this.popperInstance.update();
      }, 500);
    },
    hideTooltip() {
      clearTimeout(this.tooltipTimeout);
      this.$refs.tooltipContent.removeAttribute("data-show");
    },
  },
};
</script>

<style scoped>
.notification-dot {
  position: absolute;
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

#tooltip {
  text-align: center;
  z-index: 9999;
  border: 1px solid grey;
  width: 30%;
  background: #333;
  color: white;
  font-weight: bold;
  padding: 4px 8px;
  font-size: 13px;
  border-radius: 4px;
  padding: 0.5em;
}

#tooltip p {
  margin: 0;
}

#tooltip {
  display: none;
}

#tooltip[data-show] {
  display: block;
}
</style>
