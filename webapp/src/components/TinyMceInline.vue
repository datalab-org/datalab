<template>
  <editor
    v-model="content"
    :init="{
      inline: true,
      menubar: false,
      placeholder: 'Add a description',
      toolbar_location: 'bottom',
      plugins: 'hr image link lists charmap table emoticons',
      table_default_styles: {
        width: '50%',
        'margin-left': '1rem',
      },
      contextmenu: false,
      toolbar:
        'bold italic underline strikethrough superscript subscript forecolor backcolor removeformat |     alignleft aligncenter alignright | bullist numlist indent outdent | headergroup insertgroup | table',
      toolbar_groups: {
        formatgroup: {
          icon: 'format',
          tooltip: 'Formatting',
          items:
            'bold italic underline strikethrough | forecolor backcolor | superscript subscript | removeformat',
        },
        headergroup: {
          icon: 'paragraph',
          tooltip: 'Header styles',
          items: 'h1 h2 h3 h4 h5 h6',
        },
        paragraphgroup: {
          icon: 'paragraph',
          tooltip: 'Paragraph format',
          items: 'h1 h2 h3 | bullist numlist | alignleft aligncenter alignright | indent outdent',
        },
        insertgroup: {
          icon: 'plus',
          tooltip: 'Insert',
          items: 'link image emoticons charmap hr',
        },
      },
      skin: false, // important so that skin is loaded correctly, oddly
      content_css: false, // ^ same
    }"
    @change="$emit('update:modelValue', content)"
    @save-content="$emit('update:modelValue', content)"
  />
</template>

<script>
export default {
  props: ["modelValue", "placeholder"],
  emits: ["update:modelValue"],
  data: function () {
    return {
      content: this.modelValue,
    };
  },
  watch: {
    modelValue() {
      this.content = this.modelValue;
    },
  },
};
</script>

<style scoped>
.mce-content-body {
  margin: 10px;
  border: 1px solid transparent;
  border-radius: 0.25rem;
}
.mce-content-body:hover {
  border: 1px solid #ccc;
  border-radius: 0.25rem;
}

/* styles for the tables.. but they don't work in scoped*/
/*table {
  width: 50%;
  margin-left: 1rem;
}
tbody tr:first-child {
  font-weight: 600;
  background-color: #edfff5;
}*/
</style>
