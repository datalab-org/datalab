<template>
  <div id="nav">
    <router-link to="/about">About</router-link> |
    <router-link to="/samples">Samples</router-link> |
    <router-link to="/starting-materials">Starting Materials</router-link>
  </div>
  <div id="tableContainer" class="container">
    <div class="row">
      <div class="col-sm-10 mx-auto mb-3">
        <button class="btn btn-default" @click="modalIsOpen = true">Add a sample</button>
      </div>
    </div>
    <div class="row">
      <div class="col-sm-10 mx-auto">
        <SampleTable></SampleTable>
      </div>
    </div>
  </div>

  <form @submit.prevent="submitForm">
    <Modal v-model="modalIsOpen">
      <template v-slot:header> Add new sample </template>

      <template v-slot:body>
        <div class="form-row">
          <div class="form-group col-md-8">
            <label for="sample-id" class="col-form-label">Sample ID:</label>
            <input v-model="item_id" type="text" class="form-control" id="sample-id" required />
            <div class="form-error" v-html="sampleIDValidationMessage"></div>
          </div>
          <div class="form-group col-md-4">
            <label for="date" class="col-form-label">Date Created:</label>
            <input type="date" v-model="date" class="form-control" id="date" required />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group col-md-12">
            <label for="name">Sample Name:</label>
            <input id="name" type="text" v-model="name" class="form-control" />
          </div>
        </div>
      </template>
    </Modal>
  </form>
</template>

<script>
import SampleTable from "@/components/SampleTable.vue";
import Modal from "@/components/Modal.vue";
import { createNewSample } from "@/server_fetch_utils.js";

export default {
  name: "Samples",
  data() {
    return {
      item_id: null,
      date: new Date().toISOString().split("T")[0], // todo: add time zone support...
      name: "",
      modalIsOpen: false,
      taken_item_ids: [],
    };
  },
  computed: {
    sampleIDValidationMessage() {
      if (this.item_id == null) {
        return "";
      } // Don't throw an error before the user starts typing

      if (this.taken_item_ids.includes(this.item_id)) {
        return `<a href='edit/${this.item_id}'>${this.item_id}</a> already in use.`;
      }
      if (/\s/.test(this.item_id)) {
        return "ID cannot have any spaces";
      }
      if (this.item_id.length < 1 || this.item_id.length > 40) {
        return "ID must be between 1 and 40 characters in length";
      }
      return "";
    },
  },
  methods: {
    // this function is passed to the modal to be used on
    async submitForm() {
      console.log("new sample form submit triggered");

      await createNewSample(this.item_id, this.date, this.name)
        .then(() => {
          this.modalIsOpen = false;
          document.getElementById(this.item_id).scrollIntoView({ behavior: "smooth" });
        })
        .catch((error) => {
          if (error == "item_id_validation_error") {
            this.taken_item_ids.push(this.item_id);
          } else {
            alert("Error with creating new sample: " + error);
          }
        });
    },
  },
  components: {
    SampleTable,
    Modal,
  },
};
</script>

<style scoped>
.form-error {
  color: red;
}

/* This uses a vue "deep selector" to apply it to the v-html */
.form-error >>> a {
  color: #820000;
  font-weight: 600;
}
.fade {
  opacity: 0;
  transition: opacity 0.15s linear;
}
.fade.show {
  opacity: 1;
}

#tableContainer.overlay:after {
  content: "";
  display: block;
  position: fixed; /* could also be absolute */
  top: 0;
  left: 0;
  height: 100%;
  width: 100%;
  z-index: 10;
  background-color: rgba(0, 0, 0, 0.2);
}
</style>
