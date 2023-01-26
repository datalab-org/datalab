<template>
  <form class="modal-enclosure" @submit.prevent="submitForm">
    <Modal
      :modelValue="modelValue"
      @update:modelValue="$emit('update:modelValue', $event)"
      :disableSubmit="Boolean(sampleIDValidationMessage) || !Boolean(item_id)"
    >
      <template v-slot:header> Add new samples </template>

      <template v-slot:body>
        <div class="form-group row">
          <label for="batchSampleNRows" class="col-md-2 col-sm-4 col-5 col-form-label text-right">
            # of samples
          </label>
          <div class="col-sm-2 col-3">
            <input id="batchSampleNRows" v-model="nSamples" class="form-control" type="number" />
          </div>
        </div>
        <table class="table mb-2">
          <thead>
            <tr class="subheading">
              <th>item_id</th>
              <th>name</th>
              <th>copy from</th>
              <th>components</th>
              <th>date</th>
            </tr>
          </thead>
          <tr v-for="(row, index) in samples" :key="index">
            <td>{{ row[0] }}</td>
            <td>{{ row[1] }}</td>
            <td><ItemSelect /></td>
          </tr>
        </table>

        <!-- <label>Apply to all</label>
        <div class="row">
          <div class="col-md-4">
            <input
              v-model="item_id_prefix"
              type="text"
              class="form-control"
              id="sample-id-prefix"
            />
            <input v-model="starting_item_number" type="text" />
          </div>
          <div class="col-md-4">
            <ItemSelect
              aria-labelledby="copyFromSelectLabel"
              :modelValue="selectedItemToCopy"
              @update:modelValue="
                selectedItemToCopy = $event
                // setCopiedName();
              "
            />
          </div>
        </div> -->

        <!-- </div> -->

        <!--        <div class="form-row">
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
        <div class="form-row">
          <div class="col-md-12 form-group">
            <label id="copyFromSelectLabel">(Optional) Copy from:</label>
            <ItemSelect
              aria-labelledby="copyFromSelectLabel"
              :modelValue="selectedItemToCopy"
              @update:modelValue="
                selectedItemToCopy = $event;
                setCopiedName();
              "
            />
          </div>
        </div>
        <div class="form-row">
          <div class="col-md-12 form-group">
            <label id="startWithConstituentsLabel">(Optional) Start with constituents:</label>
            <ItemSelect
              aria-labelledby="startWithConstituentsLabel"
              multiple
              v-model="startingConstituents"
            />
          </div>
        </div> -->
      </template>
    </Modal>
  </form>
</template>

<script>
import Modal from "@/components/Modal.vue";
import ItemSelect from "@/components/ItemSelect.vue";
import { createNewSample } from "@/server_fetch_utils.js";
export default {
  name: "BatchCreateSampleModal",
  data() {
    return {
      item_id: null,
      date: new Date().toISOString().split("T")[0], // todo: add time zone support...     }
      // name: "",
      nSamples: 2,
      samples: [
        ["test1", "name of test1"],
        ["test2", "name of test2"],
      ],
      takenItemIds: [], // this holds ids that have been tried, whereas the computed takenSampleIds holds ids in the sample table
      selectedItemToCopy: null,
      startingConstituents: [],
    };
  },
  props: {
    modelValue: Boolean,
  },
  emits: ["update:modelValue"],
  computed: {
    takenSampleIds() {
      return this.$store.state.sample_list
        ? this.$store.state.sample_list.map((x) => x.item_id)
        : [];
    },
    sampleIDValidationMessage() {
      if (this.item_id == null) {
        return "";
      } // Don't throw an error before the user starts typing

      if (this.takenItemIds.includes(this.item_id) || this.takenSampleIds.includes(this.item_id)) {
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
    async submitForm() {
      console.log("new sample form submit triggered");

      const startingSynthesisBlock = this.startingConstituents.map((x) => ({
        item: x,
        quantity: null,
      }));

      await createNewSample(
        this.item_id,
        this.date,
        this.name,
        {
          synthesis_constituents: startingSynthesisBlock,
        },
        this.selectedItemToCopy && this.selectedItemToCopy.item_id
      )
        .then(() => {
          this.item_id = null;
          this.name = null;
          this.date = new Date().toISOString().split("T")[0]; // reset the date (is this the most user-friendly behavior?)

          this.$emit("update:modelValue", false); // close this modal
          document.getElementById(this.item_id).scrollIntoView({ behavior: "smooth" });
        })
        .catch((error) => {
          if (error.includes("item_id_validation_error")) {
            this.takenItemIds.push(this.item_id);
          } else {
            alert("Error with creating new sample: " + error);
          }
        });
    },
    setCopiedName() {
      if (!this.selectedItemToCopy) {
        this.name = "";
      }
      this.name = `COPY OF ${this.selectedItemToCopy.name}`;
    },
  },
  components: {
    Modal,
    ItemSelect,
  },
};
</script>

<style scoped>
.form-error {
  color: red;
}

:deep(.form-error a) {
  color: #820000;
  font-weight: 600;
}

.modal-enclosure >>> .modal-header {
  padding: 0.5rem 1rem;
}

.modal-enclosure >>> .modal-dialog {
  max-width: 1000px;
  min-height: 60vh;
  margin-top: 2.5vh;
  margin-bottom: 2.5vh;
}

.modal-enclosure >>> .modal-content {
  height: 60vh;
  /*overflow: scroll;*/
}
</style>
