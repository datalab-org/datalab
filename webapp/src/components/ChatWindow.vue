<template>
  <!-- <div v-if="!loaded" class="alert alert-secondary">Data will be displayed here</div>
  <div v-if="loading" class="alert alert-secondary">Loading...</div>
  -->
  <div ref="chatWindow" :style="{ height: windowHeight }" />
  <div v-for="message in chatMessages.slice(2)" :key="message.id">
    <MessageBubble :message="message" />
  </div>
</template>

<script>
import MessageBubble from "@/components/MessageBubble.vue";

export default {
  props: ["chatMessages"],
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
  components: {
    MessageBubble,
  },
};
</script>
