import { Extension } from "@tiptap/core";
import { Plugin } from "@tiptap/pm/state";
import { FILE_DRAG_MIME, datalabFileUrl, isImageFileName, parseFileHref } from "@/editor/files.js";

/**
 * Handles a file dragged or pasted out of an item's file list.
 *
 * Dragging an anchor does not populate `dataTransfer.files`, so without this the
 * drop falls through to ProseMirror's default text handling: the filename lands
 * as plain text and `autolink` turns something like `results.24.nc` into a link
 * to `http://results.24.nc`. See datalab#2048.
 *
 * Images are inserted as image nodes so they are resizable; anything else
 * becomes a link, which the file-link mark view renders as a file badge.
 */

function readDraggedFile(dataTransfer) {
  if (!dataTransfer) return null;

  // Set explicitly by the file list, so no URL parsing is needed.
  const payload = dataTransfer.getData(FILE_DRAG_MIME);
  if (payload) {
    try {
      const { file_id: fileId, name: fileName } = JSON.parse(payload);
      if (fileId) return { fileId, fileName };
    } catch {
      // Fall through to the URL forms below.
    }
  }

  // A link dragged or pasted from anywhere, including another deployment.
  for (const type of ["text/uri-list", "text/plain"]) {
    const file = parseFileHref(dataTransfer.getData(type));
    if (file) return file;
  }

  return null;
}

function fileToNode(schema, { fileId, fileName }) {
  const src = datalabFileUrl(fileId, fileName);

  if (isImageFileName(fileName) && schema.nodes.image) {
    return schema.nodes.image.create({ src, alt: fileName, fileId, fileName });
  }

  const mark = schema.marks.link.create({
    href: src,
    target: "_blank",
    rel: "noopener noreferrer",
  });
  return schema.text(fileName || src, [mark]);
}

export const DatalabFileDrop = Extension.create({
  name: "datalabFileDrop",

  addProseMirrorPlugins() {
    return [
      new Plugin({
        props: {
          handleDOMEvents: {
            drop: (view, event) => {
              // Real file drops are handled by the image drag/drop plugin.
              if (event.dataTransfer?.files?.length) return false;

              const file = readDraggedFile(event.dataTransfer);
              if (!file) return false;

              event.preventDefault();

              const coordinates = view.posAtCoords({
                left: event.clientX,
                top: event.clientY,
              });
              if (!coordinates) return false;

              view.dispatch(
                view.state.tr.insert(coordinates.pos, fileToNode(view.state.schema, file)),
              );
              return true;
            },

            paste: (view, event) => {
              if (event.clipboardData?.files?.length) return false;

              const file = readDraggedFile(event.clipboardData);
              if (!file) return false;

              event.preventDefault();
              view.dispatch(
                view.state.tr.replaceSelectionWith(fileToNode(view.state.schema, file), false),
              );
              return true;
            },
          },
        },
      }),
    ];
  },
});
