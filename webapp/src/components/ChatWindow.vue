<template>
  <!-- <div v-if="!loaded" class="alert alert-secondary">Data will be displayed here</div>
  <div v-if="loading" class="alert alert-secondary">Loading...</div>
  -->
  <div ref="chatWindow" :style="{ height: windowHeight }" />
  <transition-group name="message-list" tag="ul">
    <ul v-for="(message, index) in chatMessages" :key="index">
      <MessageBubble :message="message" />
    </ul>
  </transition-group>
  <font-awesome-icon v-if="isLoading" class="ellipsis" :icon="['fas', 'ellipsis-h']" beat-fade />
</template>

<script>
import MessageBubble from "@/components/MessageBubble.vue";

export default {
  components: {
    MessageBubble,
  },
  props: {
    chatMessages: Array,
    isLoading: Boolean,
  },
  data: function () {
    return {
      loading: false,
      loaded: false,
      windowHeight: "auto",
    };
  },
  watch: {
    chatMessages() {
      this.windowHeight = "auto";
    },
  },
};
</script>

<style scoped>
.message-list-enter-active,
.message-list-leave-active {
  transition: all 0.5s ease;
}

.message-list-enter-from,
.message-list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

.ellipsis {
  font-size: 1.5rem;
  color: lightgrey;
  position: relative;
  top: -1rem;
}
</style>
