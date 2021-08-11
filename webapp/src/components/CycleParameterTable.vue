<template>
  <div>
    <h1>My JSON</h1>

    <table>
      <tr v-for="(value, name) in jsondata['techniques'][0]['program']" :key="value.id">
        <td>{{ name }}</td>
        <td>{{ value["I"] }}</td>
        <td>{{ value["I.1"] }}</td>
        <!-- <td v-for="c in jsondata['techniques'][0]['program']" :key="c.id" > {{c}}</td> -->
      </tr>
    </table>
  </div>
</template>

<script>
import cycleDescriptionData from "@/myjson.json";
export default {
  name: "myJSON",
  data() {
    return {
      jsondata: cycleDescriptionData,

      userInput: this.jsondata,
    };
  },
};
</script>
