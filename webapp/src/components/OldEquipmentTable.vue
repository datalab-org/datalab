<template>
  <div v-if="isEquipmentFetchError" class="alert alert-danger">
    <font-awesome-icon icon="exclamation-circle" />&nbsp;Server Error. Equipment list could not be
    retreived.
  </div>
  <table class="table table-hover table-sm" data-testid="equipment-table">
    <thead>
      <tr>
        <th scope="col">ID</th>
        <th scope="col">Name</th>
        <th class="text-center" scope="col">Date created</th>
        <th class="text-center" scope="col">Location</th>
        <th class="text-left" scope="col">Maintainers</th>

        <th scope="col"></th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="equipment in equipments"
        :id="equipment.item_id"
        :key="equipment.item_id"
        @click.exact="goToEditPage(equipment.item_id)"
        @click.meta="openEditPageInNewTab(equipment.item_id)"
        @click.ctrl="openEditPageInNewTab(equipment.item_id)"
      >
        <td align="left" class="table-item-id">
          <FormattedItemName
            :item_id="equipment.item_id"
            :item-type="equipment?.type"
            enable-modified-click
          />
        </td>
        <td align="left">{{ equipment.name }}</td>
        <td class="text-center">{{ $filters.IsoDatetimeToDate(equipment.date) }}</td>
        <td class="left">{{ equipment.location }}</td>
        <td align="center"><Creators :creators="equipment.creators" /></td>
        <td align="right">
          <button
            type="button"
            class="close"
            aria-label="delete"
            @click.stop="deleteEquipment(equipment)"
          >
            <span aria-hidden="true" style="color: grey">&times;</span>
          </button>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import FormattedItemName from "@/components/FormattedItemName";
import Creators from "@/components/Creators";
import { getEquipmentList, deleteEquipment } from "@/server_fetch_utils.js";
import { itemTypes } from "@/resources.js";

export default {
  components: {
    FormattedItemName,
    Creators,
  },
  data() {
    return {
      isEquipmentFetchError: false,
      itemTypes: itemTypes,
    };
  },
  computed: {
    equipments() {
      return this.$store.state.equipment_list;
    },
  },
  created() {
    this.getEquipment();
  },
  methods: {
    goToEditPage(item_id) {
      this.$router.push(`/edit/${item_id}`);
    },
    openEditPageInNewTab(item_id) {
      window.open(`/edit/${item_id}`, "_blank");
    },
    getEquipment() {
      getEquipmentList().catch(() => {
        this.isEquipmentFetchError = true;
      });
    },
    deleteEquipment(equipment) {
      if (confirm(`Are you sure you want to delete equipment "${equipment.item_id}"?`)) {
        console.log("deleting...");
        deleteEquipment(equipment.item_id);
      }
      console.log("delete cancelled...");
    },
  },
};
</script>

<style scoped>
.clickable {
  cursor: pointer;
}
</style>
