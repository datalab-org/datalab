<template>
  <!-- render the chat with the LLM bot as a green chat bubble on the left, and the user's messages as a grey chat bubble on the right -->
  <div
    class="message-bubble"
    :class="{ 'message-bubble--left': !isUserMessage, 'message-bubble--right': isUserMessage }"
  >
    <div
      class="message-bubble__content"
      :class="{ 'message-bubble--system': !isUserMessage, 'message-bubble--user': isUserMessage }"
    >
      {{ message.content }}
    </div>
  </div>
</template>

<script>
export default {
  name: "MessageBubble",
  props: {
    message: {
      type: Object,
      required: true,
    },
  },
  computed: {
    isUserMessage() {
      return this.message.role === "user";
    },
  },
};
</script>

<style scoped>
.message-bubble {
  display: flex;
  font-size: 0.8em;
  flex-direction: column;
  margin: 0.5rem 0;
  margin-bottom: 2rem;
}

.message-bubble--left {
  align-items: flex-start;
}

.message-bubble--user {
  background-color: rgba(25, 150, 25, 0.3);
}

.message-bubble--system {
  background-color: rgba(25, 25, 25, 0.1);
  font-family: "Roboto Mono", monospace;
}

.message-bubble--right {
  align-items: flex-end;
}

.message-bubble__content {
  border-radius: 0.5rem;
  padding: 1rem;
  max-width: 65%;
  color: black;
}
</style>
