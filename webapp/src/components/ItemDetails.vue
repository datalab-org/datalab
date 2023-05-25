<template>
  <div class="container card-container">
    <div class="row justify-content-start">
      <div class="col-2">
        <div class="card">
          <div class="card-title">Refcode</div>
          <div class="card-body">
            <FormattedRefcode :refcode="item.refcode" />
          </div>
        </div>
      </div>
      <div class="col-2" v-if="item.collections.length > 0">
        <div class="card">
          <div class="card-title">Collections</div>
          <div class="card-body">
            <CollectionList :collections="item.collections" />
          </div>
        </div>
      </div>
      <div class="col-2" v-if="item.name">
        <div class="card">
          <div class="card-title">Name</div>
          <div class="card-body">{{ item.name }}</div>
        </div>
      </div>
      <div class="col-2" v-if="item.creators">
        <div class="card">
          <div class="card-title">Creators</div>
          <div class="card-body">
            <Creators :creators="item.creators" :showNames="true" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CollectionList from "@/components/CollectionList";
import Creators from "@/components/Creators";
import FormattedRefcode from "@/components/FormattedRefcode";

export default {
  data() {
    return {};
  },
  props: {
    item: {
      type: Object,
      required: true,
    },
  },
  components: {
    CollectionList,
    Creators,
    FormattedRefcode,
  },
};
</script>

<style scoped>
.card-container {
  background-color: #ededed;
  margin-left: 50px;
  border-left: 4px solid #42b983;
}
.card {
  background-color: #ededed;
  padding: 0 0 0 0;
  margin: 0.5em;
  border: none;
}

.card-body {
  font-size: 0.75rem;
  margin-left: 0.5em;
  padding: 0;
}

.card-title {
  font-size: 0.75rem;
  margin-left: 0.5em;
  padding: 0;
}
</style>
