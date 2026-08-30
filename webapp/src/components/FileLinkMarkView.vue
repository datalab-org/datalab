<template>
  <a
    v-if="file"
    class="datalab-file-link"
    :href="mark.attrs.href"
    :title="file.fileName"
    target="_blank"
    rel="noopener noreferrer"
  >
    <font-awesome-icon icon="file" class="file-icon" fixed-width />
    <MarkViewContent as="span" class="file-name" />
  </a>
  <a
    v-else
    :href="mark.attrs.href"
    :target="mark.attrs.target"
    :rel="mark.attrs.rel"
    :class="mark.attrs.class"
  >
    <MarkViewContent as="span" />
  </a>
</template>

<script>
import { MarkViewContent, markViewProps } from "@tiptap/vue-3";
import { parseFileHref } from "@/editor/marks/DatalabFileLink";

export default {
  components: { MarkViewContent },

  // editor, mark, extension, inline, view, updateAttributes, HTMLAttributes
  props: markViewProps,

  computed: {
    file() {
      return parseFileHref(this.mark.attrs.href);
    },
  },
};
</script>

<style scoped>
/* Matches `.filelink` in FileList so an attached file reads the same way
   wherever it appears. */
.datalab-file-link {
  color: #004175;
  font-family: var(--font-monospace);
  display: inline-flex;
  align-items: baseline;
  gap: 0.25rem;
  max-width: 22em;
  vertical-align: bottom;
}

.datalab-file-link:hover {
  text-decoration: none;
}

.file-icon {
  color: #6c757d;
  flex-shrink: 0;
}

/* The filename is real, editable document text, so it can only be trimmed at
   the end; the full name is on the title attribute. */
.file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
