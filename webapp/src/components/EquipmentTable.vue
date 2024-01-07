<template>
  <div v-if="isEquipmentFetchError" class="alert alert-danger">
    <font-awesome-icon icon="exclamation-circle" />&nbsp;Server Error. Equipment list could not be
    retreived.
  </div>
  <table class="table table-hover table-sm" data-testid="equipment-table">
    <thead>
      <tr>
        <th scope="col">ID</th>
        <th scope="col">Type</th>
        <th scope="col">Name</th>
        <th class="text-center" scope="col">Date created</th>
        <th class="text-center" scope="col">Location</th>
        <th class="text-center" scope="col"># of blocks</th>
        <th scope="col"></th>
      </tr>
    </thead>
    <tbody>
      <tr
        :id="equipment.item_id"
        v-for="equipment in equipments"
        :key="equipment.item_id"
        v-on:click.exact="goToEditPage(equipment.item_id)"
        v-on:click.meta="openEditPageInNewTab(equipment.item_id)"
        v-on:click.ctrl="openEditPageInNewTab(equipment.item_id)"
      >
        <td align="left" class="table-item-id">
          <FormattedItemName
            :item_id="equipment.item_id"
            :itemType="equipment?.type"
            enableModifiedClick
          />
        </td>
        <td align="center">{{ itemTypes[equipment.type].display }}</td>
        <td align="left">{{ equipment.name }}</td>
        <td class="text-center">{{ $filters.IsoDatetimeToDate(equipment.date) }}</td>
        <td class="left">{{ equipment.location }}</td>
        <td align="center"><Creators :creators="equipment.creators" /></td>
        <td class="text-right">{{ equipment.nblocks }}</td>
        <td align="right">
          <!--           <button
            type="button"
            class="close"
            @click.stop="deleteEquipment(equipment)"
            aria-label="delete"
          >
            <span aria-hidden="true" style="color: grey">&times;</span>
          </button> -->
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import FormattedItemName from "@/components/FormattedItemName";
import Creators from "@/components/Creators";
import { getEquipmentList } from "@/server_fetch_utils.js"; // deleteEquipment
import { itemTypes } from "@/resources.js";

export default {
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
    // deleteEquipment(equipment) {
    //   if (confirm(`Are you sure you want to delete equipment "${equipment.item_id}"?`)) {
    //     console.log("deleting...");
    //     deleteEquipment(equipment.item_id);
    //   }
    //   console.log("delete cancelled...");
    // },
  },
  created() {
    this.getEquipment();
  },
  components: {
    FormattedItemName,
    Creators,
  },
};
</script>

<style scoped>
.clickable {
  cursor: pointer;
}
</style>
