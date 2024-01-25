<template>
  <editor
    v-model="content"
    @change="$emit('update:modelValue', content)"
    @SaveContent="$emit('update:modelValue', content)"
    :init="{
      inline: true,
      menubar: false,
      placeholder: 'Add a description',
      toolbar_location: 'bottom',
      plugins: 'hr image link lists charmap table emoticons code',
      table_default_styles: {
        width: '50%',
        'margin-left': '1rem',
      },
      toolbar:
        'bold italic underline strikethrough superscript subscript forecolor backcolor removeformat |     alignleft aligncenter alignright | bullist numlist indent outdent | headergroup insertgroup | table | code',
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
      setup: editorSetupFunction,
      extended_valid_elements: 'item-reference[*]',
      custom_elements: 'item-reference',
    }"
  />
</template>

<script>
import tinymce from "tinymce/tinymce";
// import FormattedItemName from "@/components/FormattedItemName.vue";

export default {
  data: function () {
    return {
      content: this.modelValue,
    };
  },
  methods: {
    editorSetupFunction(editor) {
      var specialChars = [
        { text: "exclamation mark", value: "!" },
        { text: "at", value: "@" },
        { text: "hash", value: "#" },
        { text: "dollars", value: "$" },
        { text: "percent sign", value: "%" },
        { text: "caret", value: "^" },
        { text: "ampersand", value: "&" },
        { text: "asterisk", value: "*" },
      ];

      var onAction = function (autocompleteApi, rng, value) {
        // const formattedItemName = createApp(FormattedItemName, {
        //   item_id: "test",
        //   itemType: "samples",
        //   name: value,
        //   chemform: "H2O",
        //   enableClick: true,
        //   enableModifiedClick: true,
        // });
        // formattedItemName.mount(rng.startContainer);
        editor.selection.setRng(rng);
        console.log(value);
        editor.insertContent(
          "<item-reference item_id='test_id' chemform='H2O' item-type='samples'></item-reference>",
        );
        // editor.insertContent(value);
        // autocompleteApi.hide();
      };

      var getMatchedChars = function (pattern) {
        return specialChars.filter(function (char) {
          return char.text.indexOf(pattern) !== -1;
        });
      };

      editor.ui.registry.addAutocompleter("specialchars", {
        ch: "@",
        minChars: 1,
        columns: "auto",
        onAction: onAction,
        fetch: function (pattern) {
          return new tinymce.util.Promise(function (resolve) {
            var results = getMatchedChars(pattern).map(function (char) {
              return {
                type: "autocompleteitem",
                value: char.value,
                text: char.text,
                icon: char.value,
              };
            });
            resolve(results);
          });
        },
      });
    },
  },
  props: ["modelValue", "placeholder"],
  emits: ["update:modelValue"],
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
