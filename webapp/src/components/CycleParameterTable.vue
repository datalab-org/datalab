<template>
  <div>
    <h1>My JSON</h1>
    
      <table>
      <tr v-for="b in Object.keys(jsondata['myfile'])" :key="b.id" class="weather-data">
         <td>{{b}}</td> 
      </tr>
     <tr v-for="a in jsondata['myfile']" :key="a.id" class="weather-data">
        <td>{{a}}</td> 

      </tr>


    </table>


  </div>
</template>



<script>
import cycleDescriptionData from '@/myjson.json'
export default {
  name: 'myJSON',
  data() {
      return {
          jsondata: cycleDescriptionData,
          validKeys: [ "Number of linked techniques " ],
          userInput: this.jsondata
      };
  },
  methods:{
    techniqueRemover(){
      validKeys = [ "Number of linked techniques " ];
      userInput = this.jsondata

      Object.keys(userInput).forEach((key) => validKeys.includes(key) || delete userInput[key]);
    }
  },
  beforeMount(){
    this.jsondata = this.techniqueRemover()
  }

};
</script>

<style scoped>
table {
	display: table;
}
table tr {
	display: table-cell;
}
table tr td {
	display: block;
}
</style>