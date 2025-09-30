import { Extension } from "@tiptap/core";

const convertDocToMarkdown = (doc) => {
  let markdown = "";

  const processNode = (node, depth = 0) => {
    switch (node.type) {
      case "heading": {
        const level = node.attrs?.level || 1;
        markdown += "#".repeat(level) + " ";
        if (node.content) {
          node.content.forEach((child) => processNode(child, depth));
        }
        markdown += "\n";
        break;
      }

      case "paragraph": {
        if (node.content) {
          node.content.forEach((child) => {
            if (child.type === "hardBreak") {
              markdown += "  \n";
            } else {
              processNode(child, depth);
            }
          });
        }

        markdown += "\n";
        break;
      }

      case "hardBreak": {
        markdown += "  \n";
        break;
      }

      case "bulletList": {
        if (node.content) {
          node.content.forEach((item) => {
            markdown += "  ".repeat(depth) + "- ";
            if (item.content) {
              item.content.forEach((child) => {
                if (child.type === "paragraph" && child.content) {
                  child.content.forEach((c) => processNode(c, depth + 1));
                } else {
                  processNode(child, depth + 1);
                }
              });
            }
            markdown += "\n";
          });
        }
        markdown += "\n";
        break;
      }

      case "orderedList": {
        if (node.content) {
          node.content.forEach((item, index) => {
            markdown += "  ".repeat(depth) + `${index + 1}. `;
            if (item.content) {
              item.content.forEach((child) => {
                if (child.type === "paragraph" && child.content) {
                  child.content.forEach((c) => processNode(c, depth + 1));
                } else {
                  processNode(child, depth + 1);
                }
              });
            }
            markdown += "\n";
          });
        }
        markdown += "\n";
        break;
      }

      case "listItem": {
        if (node.content) {
          node.content.forEach((child) => processNode(child, depth));
        }
        break;
      }

      case "text": {
        let text = node.text || "";

        const marks = node.marks || [];

        let hasColor = false;
        let colorValue = null;

        marks.forEach((mark) => {
          if (mark.type === "textStyle" && mark.attrs?.color) {
            hasColor = true;
            colorValue = mark.attrs.color;
          }
        });

        marks.forEach((mark) => {
          switch (mark.type) {
            case "bold":
              text = `**${text}**`;
              break;
            case "italic":
              text = `*${text}*`;
              break;
            case "strike":
              text = `~~${text}~~`;
              break;
            case "underline":
              text = `<u>${text}</u>`;
              break;
            case "link":
              text = `[${text}](${mark.attrs.href})`;
              break;
          }
        });

        if (hasColor && colorValue) {
          text = `<span style="color: ${colorValue}">${text}</span>`;
        }

        markdown += text;
        break;
      }

      case "horizontalRule": {
        markdown += "\n---\n\n";
        break;
      }

      case "blockMath": {
        markdown += `$$\n${node.attrs?.latex || ""}\n$$\n\n`;
        break;
      }

      case "inlineMath": {
        markdown += `$${node.attrs?.latex || ""}$`;
        break;
      }

      case "span": {
        if (node.attrs?.["data-type"] === "inline-math") {
          let prefix = "";
          let suffix = "";

          if (node.attrs?.style) {
            prefix = `<span style="${node.attrs.style}">`;
            suffix = `</span>`;
          }

          markdown += `${prefix}$${node.attrs["data-latex"] || ""}$${suffix}`;
        } else {
          if (node.content) {
            node.content.forEach((child) => processNode(child, depth));
          }
        }
        if (node.attrs?.["data-type"] === "inline-math") {
          markdown += `$${node.attrs["data-latex"] || ""}$`;
        } else if (node.content) {
          node.content.forEach((child) => processNode(child, depth));
        }
        break;
      }

      case "table": {
        markdown += tableToMarkdown(node);
        break;
      }

      case "mermaid": {
        markdown += `\`\`\`mermaid\n${node.attrs?.code || ""}\n\`\`\`\n\n`;
        break;
      }

      case "crossreference": {
        const itemId = node.attrs?.itemId || "";
        const name = node.attrs?.name || "";
        const itemType = node.attrs?.itemType || "";
        const chemform = node.attrs?.chemform || "";
        markdown += `@[${itemId}](${name}){type=${itemType} chemform="${chemform}"}`;
        break;
      }

      case "image": {
        const src = node.attrs?.src || "";
        const alt = node.attrs?.alt || "";
        markdown += `![${alt}](${src})`;
        break;
      }

      default:
        if (node.content) {
          node.content.forEach((child) => processNode(child, depth));
        }
        break;
    }
  };

  if (doc.content) {
    doc.content.forEach((node) => processNode(node));
  }

  return markdown.trim();
};

const tableToMarkdown = (tableNode) => {
  let markdown = "";

  const tableAttrs = {
    style: tableNode.attrs?.style || null,
    colgroup: [],
  };

  if (tableNode.content) {
    tableNode.content.forEach((child) => {
      if (child.type === "colgroup" && child.content) {
        child.content.forEach((col) => {
          tableAttrs.colgroup.push(col.attrs?.style || null);
        });
      }
    });
  }

  let maxCols = tableAttrs.colgroup.length || 0;
  const rows = [];

  if (tableNode.content) {
    tableNode.content.forEach((row) => {
      if (row.type !== "tableRow") return;

      const cells = [];
      let colCount = 0;
      let isHeaderRow = false;

      if (row.content) {
        row.content.forEach((cell) => {
          let cellText = "";
          const colspan = cell.attrs?.colspan || 1;
          const rowspan = cell.attrs?.rowspan || 1;

          const isHeader = cell.type === "tableHeader";
          if (isHeader) isHeaderRow = true;

          if (cell.content) {
            cell.content.forEach((paragraph) => {
              if (paragraph.content) {
                paragraph.content.forEach((child) => {
                  if (child.type === "text") {
                    let text = child.text || "";
                    if (child.marks) {
                      child.marks.forEach((mark) => {
                        switch (mark.type) {
                          case "bold":
                            text = `**${text}**`;
                            break;
                          case "italic":
                            text = `*${text}*`;
                            break;
                        }
                      });
                    }
                    cellText += text;
                  }
                });
              }
            });
          }

          cells.push({
            content: cellText.trim() !== "" ? cellText : "",
            isHeader: isHeader,
            colspan: colspan,
            rowspan: rowspan,
          });
          colCount += colspan;
        });
      }

      rows.push({
        cells,
        isHeaderRow,
      });
      maxCols = Math.max(maxCols, colCount);
    });
  }

  markdown += `<!-- TABLE_ATTRS: ${JSON.stringify(tableAttrs)} -->\n`;

  if (rows.length > 0) {
    const headerCells = rows[0].cells.map((cell) => {
      const marker = cell.isHeader ? "TH:" : "TD:";
      return marker + (cell.content || "");
    });
    markdown += "| " + headerCells.join(" | ") + " |\n";

    markdown += "| " + rows[0].cells.map(() => "---").join(" | ") + " |\n";

    if (tableAttrs.colgroup.length === 0 && maxCols > 0) {
      tableAttrs.colgroup = Array(maxCols).fill("min-width: 25px;");
    }

    for (let i = 1; i < rows.length; i++) {
      const bodyCells = rows[i].cells.map((cell) => {
        const marker = cell.isHeader ? "TH:" : "TD:";
        return marker + (cell.content || "");
      });
      markdown += "| " + bodyCells.join(" | ") + " |\n";
    }
  }

  return markdown + "\n";
};

const parseMarkdownToHTML = (markdown) => {
  let html = markdown;

  html = html.replace(/(\$[^$\n]+\$)\n/g, "$1__PRESERVE_NEWLINE__");

  html = html.replace(/__BLOCK_SEPARATOR__/g, "<p></p>");

  html = html.replace(/__EMPTY_CELL__/g, "");

  html = html.replace(/ {2}\n/g, "<br>");

  html = html.replace(/^\s*(\|.*\|)\s*$/gm, "$1");
  const codeBlocks = [];

  html = html.replace(/```mermaid\n([\s\S]*?)```/g, (match, code) => {
    const index = codeBlocks.length;
    let decodedCode = code.replace(/&gt;/g, ">").replace(/&lt;/g, "<").replace(/&amp;/g, "&");
    decodedCode = decodedCode.replace(/<p><\/p>/g, "").trim();
    codeBlocks.push(`<div data-type="mermaid" code="${escapeAttr(decodedCode)}"></div>`);
    return `__CODE_BLOCK_${index}__`;
  });

  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const index = codeBlocks.length;
    codeBlocks.push(`<pre><code>${escapeHtml(code)}</code></pre>`);
    return `__CODE_BLOCK_${index}__`;
  });

  html = html.replace(/\$\$\n?([\s\S]*?)\n?\$\$/g, (match, latex) => {
    const index = codeBlocks.length;
    const safeLatex = latex || "";
    codeBlocks.push(`<div data-type="blockMath" data-latex="${escapeAttr(safeLatex)}"></div>`);
    return `__CODE_BLOCK_${index}__\n`;
  });

  const inlineMaths = [];

  html = html.replace(/<span style="([^"]+)">\$([^$\n]+)\$<\/span>/g, (match, style, latex) => {
    const index = inlineMaths.length;
    inlineMaths.push(
      `<span style="${style}"><span data-latex="${escapeAttr(
        latex,
      )}" data-type="inline-math"></span></span>`,
    );
    return `__INLINE_MATH_${index}__`;
  });

  html = html.replace(/\$([^$\n]+)\$/g, (match, latex) => {
    const index = inlineMaths.length;
    inlineMaths.push(`<span data-latex="${escapeAttr(latex)}" data-type="inline-math"></span>`);
    return `__INLINE_MATH_${index}__`;
  });

  html = html.replace(/^#{6} (.*?)$/gm, "<h6>$1</h6>");
  html = html.replace(/^#{5} (.*?)$/gm, "<h5>$1</h5>");
  html = html.replace(/^#{4} (.*?)$/gm, "<h4>$1</h4>");
  html = html.replace(/^#{3} (.*?)$/gm, "<h3>$1</h3>");
  html = html.replace(/^#{2} (.*?)$/gm, "<h2>$1</h2>");
  html = html.replace(/^# (.*?)$/gm, "<h1>$1</h1>");

  html = html.replace(/^---$/gm, "<hr>");

  const tableRegex = /<!-- TABLE_ATTRS: (.+?) -->\n\|(.*)\|\n\|[-:\s|]+\|\n((?:\|.*\|\n?)*)/gm;
  html = html.replace(tableRegex, (match, attrsJson, header, body) => {
    let tableAttrs = {};
    try {
      tableAttrs = JSON.parse(attrsJson);
    } catch (e) {
      tableAttrs = { style: "min-width: 75px;", colgroup: [] };
    }

    let colgroupHtml = "";
    if (tableAttrs.colgroup && tableAttrs.colgroup.length > 0) {
      colgroupHtml = "<colgroup>";
      tableAttrs.colgroup.forEach((style) => {
        colgroupHtml += style ? `<col style="${style}">` : "<col>";
      });
      colgroupHtml += "</colgroup>";
    }

    const headerCells = header
      .split("|")
      .filter((c) => c !== "")
      .map((c) => {
        const content = c.trim();
        const isHeader = content.startsWith("TH:");
        const cellContent = content.replace(/^(TH:|TD:)/, "");
        const tag = isHeader ? "th" : "td";
        return `<${tag} colspan="1" rowspan="1"><p>${
          cellContent ? parseInlineMarkdown(cellContent) : ""
        }</p></${tag}>`;
      })
      .join("");

    let bodyHtml = "";
    if (body.trim()) {
      const bodyRows = body
        .trim()
        .split("\n")
        .map((row) => {
          const cells = row
            .split("|")
            .filter((c) => c !== "")
            .map((c) => {
              const content = c.trim();
              const isHeader = content.startsWith("TH:");
              const cellContent = content.replace(/^(TH:|TD:)/, "");
              const tag = isHeader ? "th" : "td";
              return `<${tag} colspan="1" rowspan="1"><p>${
                cellContent ? parseInlineMarkdown(cellContent) : ""
              }</p></${tag}>`;
            })
            .join("");
          return `<tr>${cells}</tr>`;
        })
        .join("");
      bodyHtml = bodyRows;
    }

    const styleAttr = tableAttrs.style ? ` style="${tableAttrs.style}"` : "";
    return `<table${styleAttr}>${colgroupHtml}<tbody><tr>${headerCells}</tr>${bodyHtml}</tbody></table>`;
  });

  const simpleTabelRegex = /^\|(.*)\|\n\|[-:\s|]+\|\n((?:\|.*\|\n?)*)/gm;
  html = html.replace(simpleTabelRegex, (match, header, body) => {
    const defaultStyle = "min-width: 75px;";
    const defaultColStyle = "min-width: 25px;";

    const colCount = header.split("|").filter((c) => c !== "").length;

    let colgroupHtml = "<colgroup>";
    for (let i = 0; i < colCount; i++) {
      colgroupHtml += `<col style="${defaultColStyle}">`;
    }
    colgroupHtml += "</colgroup>";

    const headerCells = header
      .split("|")
      .filter((c) => c !== "")
      .map((c) => {
        const content = c.trim();
        return `<th colspan="1" rowspan="1"><p>${
          content ? parseInlineMarkdown(content) : ""
        }</p></th>`;
      })
      .join("");

    let bodyHtml = "";
    if (body.trim()) {
      const bodyRows = body
        .trim()
        .split("\n")
        .map((row) => {
          const cells = row
            .split("|")
            .filter((c) => c !== "")
            .map((c) => {
              const content = c.trim();
              return `<td colspan="1" rowspan="1"><p>${
                content ? parseInlineMarkdown(content) : ""
              }</p></td>`;
            })
            .join("");
          return `<tr>${cells}</tr>`;
        })
        .join("");
      bodyHtml = bodyRows;
    }

    return `<table style="${defaultStyle}">${colgroupHtml}<tbody><tr>${headerCells}</tr>${bodyHtml}</tbody></table>`;
  });

  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

  html = html.replace(/(?<!\*)\*(?!\*)([^*]+)\*(?!\*)/g, "<em>$1</em>");

  html = html.replace(/~~([^~]+)~~/g, "<s>$1</s>");

  html = html.replace(/<u>([^<]+)<\/u>/g, "<u>$1</u>");

  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img alt="$1" src="$2">');
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');

  html = html.replace(/__BLOCK_SEPARATOR__/g, "<p></p>");

  html = html.replace(
    /@\[(.*?)\]\((.*?)\)\{type=(.*?)\s+chemform="(.*?)"\}/g,
    '<span data-type="crossreference" data-item-id="$1" data-item-type="$3" data-name="$2" data-chemform="$4"></span>',
  );

  html = html.replace(/__PRESERVE_NEWLINE__/g, "\n");

  const lines = html.split("\n");
  const processedLines = [];
  let inList = false;
  let listType = null;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const bulletMatch = line.match(/^(\s*)-\s(.*)$/);
    const orderedMatch = line.match(/^(\s*)\d+\.\s(.*)$/);

    if (bulletMatch) {
      if (!inList || listType !== "ul") {
        if (inList) processedLines.push(`</${listType}>`);
        processedLines.push("<ul>");
        inList = true;
        listType = "ul";
      }
      processedLines.push(`<li><p>${bulletMatch[2]}</p></li>`);
    } else if (orderedMatch) {
      if (!inList || listType !== "ol") {
        if (inList) processedLines.push(`</${listType}>`);
        processedLines.push("<ol>");
        inList = true;
        listType = "ol";
      }
      processedLines.push(`<li><p>${orderedMatch[2]}</p></li>`);
    } else {
      if (inList) {
        processedLines.push(`</${listType}>`);
        inList = false;
        listType = null;
      }

      const trimmed = line.trim();
      if (trimmed === "") {
        if (i > 0 && !lines[i - 1].includes("__INLINE_MATH_")) {
          processedLines.push("<p></p>");
        }
        continue;
      } else if (trimmed === "__EMPTY_PARAGRAPH__") {
        processedLines.push("<p></p>");
        continue;
      } else if (
        !trimmed.match(/^<[^>]+>/) &&
        !trimmed.match(/^__CODE_BLOCK_\d+__$/) &&
        !trimmed.match(/^__INLINE_MATH_\d+__$/) &&
        !trimmed.match(/^<!--/) &&
        !trimmed.startsWith("<span") &&
        !trimmed.startsWith("<strong")
      ) {
        processedLines.push(`<p>${trimmed}</p>`);
      } else if (/^<span|^<strong|^\$/.test(trimmed)) {
        processedLines.push(`<p>${trimmed}</p>`);
      } else if (trimmed.includes("__INLINE_MATH_")) {
        processedLines.push(`<p>${trimmed}</p>`);
      } else if (!trimmed.startsWith("<!--")) {
        processedLines.push(trimmed);
      }
    }
  }

  if (inList) {
    processedLines.push(`</${listType}>`);
  }

  html = processedLines.join("\n");

  inlineMaths.forEach((math, index) => {
    html = html.replace(`__INLINE_MATH_${index}__`, math);
  });

  codeBlocks.forEach((block, index) => {
    html = html.replace(`__CODE_BLOCK_${index}__`, block);
  });

  return html;
};

const parseInlineMarkdown = (text) => {
  let parsed = text;

  const maths = [];
  parsed = parsed.replace(/\$([^$\n]+)\$/g, (match, latex) => {
    const index = maths.length;
    maths.push(`<span data-latex="${escapeAttr(latex)}" data-type="inline-math"></span>`);
    return `__MATH_${index}__`;
  });

  parsed = parsed.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  parsed = parsed.replace(/(?<!\*)\*(?!\*)([^*]+)\*(?!\*)/g, "<em>$1</em>");

  maths.forEach((math, index) => {
    parsed = parsed.replace(`__MATH_${index}__`, math);
  });

  return parsed;
};

const escapeHtml = (text) => {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
};

const escapeAttr = (text) => {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
};

export const MarkdownToggle = Extension.create({
  name: "markdownToggle",

  addStorage() {
    return {
      markdownMode: false,
      markdownContent: "",
    };
  },

  addCommands() {
    return {
      toggleMarkdownView:
        () =>
        ({ editor, commands }) => {
          const storage = editor.storage.markdownToggle;

          if (!storage.markdownMode) {
            storage.markdownContent = convertDocToMarkdown(editor.getJSON());
            storage.markdownMode = true;
          } else {
            commands.setContent(parseMarkdownToHTML(storage.markdownContent));
            storage.markdownMode = false;
          }
          return true;
        },

      updateMarkdownContent:
        (content) =>
        ({ editor }) => {
          editor.storage.markdownToggle.markdownContent = content;
          return true;
        },

      isInMarkdownMode:
        () =>
        ({ editor }) => {
          return editor.storage.markdownToggle.markdownMode;
        },

      getMarkdownContent:
        () =>
        ({ editor }) => {
          return editor.storage.markdownToggle.markdownContent;
        },
    };
  },
});
