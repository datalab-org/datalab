<template>
  <div :class="{ 'border-left pl-3 mt-2': currentDepth > 0 }">
    <div v-if="node.children.length" class="mb-2">
      <button
        type="button"
        class="btn btn-sm mr-2"
        :class="node.negate ? 'btn-danger' : 'btn-outline-danger'"
        :aria-pressed="!!node.negate"
        title="Negate this group (OPTIMADE NOT)"
        @click="$emit('update:node', { ...node, negate: !node.negate })"
      >
        NOT
      </button>
      <div v-if="node.children.length > 1" class="btn-group btn-group-sm" role="group">
        <button
          type="button"
          class="btn"
          :class="node.combinator === 'and' ? 'btn-primary' : 'btn-outline-primary'"
          @click="setCombinator('and')"
        >
          AND
        </button>
        <button
          type="button"
          class="btn"
          :class="node.combinator === 'or' ? 'btn-primary' : 'btn-outline-primary'"
          @click="setCombinator('or')"
        >
          OR
        </button>
      </div>
    </div>

    <div v-for="(child, index) in node.children" :key="child._uid" class="mb-2">
      <QueryRule
        v-if="child.kind === 'rule'"
        :node="child"
        :fields="fields"
        @update:node="updateChild(index, $event)"
        @remove="removeChild(index)"
      />
      <QueryGroup
        v-else
        :node="child"
        :fields="fields"
        :max-depth="maxDepth"
        :current-depth="currentDepth + 1"
        @update:node="updateChild(index, $event)"
        @remove="removeChild(index)"
      />
    </div>

    <div class="d-flex align-items-center">
      <button type="button" class="btn btn-sm btn-outline-primary mr-2" @click="addRule">
        <font-awesome-icon icon="plus" class="mr-1" />New rule
      </button>
      <button
        v-if="currentDepth < maxDepth - 1"
        type="button"
        class="btn btn-sm btn-outline-secondary"
        @click="addGroup"
      >
        Add group
      </button>
      <button
        v-if="currentDepth > 0"
        type="button"
        class="btn btn-sm btn-link text-danger ml-auto"
        @click="$emit('remove')"
      >
        <font-awesome-icon icon="times" class="mr-1" />Remove group
      </button>
    </div>
  </div>
</template>

<script>
import QueryRule from "@/components/QueryRule.vue";

let uidCounter = 0;

export default {
  name: "QueryGroup",
  components: { QueryRule },
  props: {
    node: { type: Object, required: true },
    fields: { type: Array, required: true },
    maxDepth: { type: Number, default: 3 },
    currentDepth: { type: Number, default: 0 },
  },
  emits: ["update:node", "remove"],
  methods: {
    setCombinator(val) {
      this.$emit("update:node", { ...this.node, combinator: val });
    },
    addRule() {
      const firstField = this.fields[0];
      const firstOp = firstField?.operators[0]?.id || "";
      this.$emit("update:node", {
        ...this.node,
        children: [
          ...this.node.children,
          { kind: "rule", field: firstField?.id || "", operator: firstOp, _uid: ++uidCounter },
        ],
      });
    },
    addGroup() {
      this.$emit("update:node", {
        ...this.node,
        children: [
          ...this.node.children,
          { kind: "group", combinator: "and", children: [], _uid: ++uidCounter },
        ],
      });
    },
    updateChild(index, updated) {
      const children = [...this.node.children];
      children[index] = updated;
      this.$emit("update:node", { ...this.node, children });
    },
    removeChild(index) {
      this.$emit("update:node", {
        ...this.node,
        children: this.node.children.filter((_, i) => i !== index),
      });
    },
  },
};
</script>
