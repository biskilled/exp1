/**
 * Shared markdown renderer — used by summary.js and prompts.js.
 * Pure JS, no external libraries.
 */

export function renderMd(text) {
  if (!text) return '';

  const esc = s => String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Protect fenced code blocks
  const codeBlocks = [];
  text = text.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    const i = codeBlocks.length;
    codeBlocks.push(
      `<pre><code${lang ? ` class="lang-${lang}"` : ''}>${esc(code.trim())}</code></pre>`
    );
    return `\x00CODEBLOCK${i}\x00`;
  });

  // Protect inline code
  const inlineCode = [];
  text = text.replace(/`([^`\n]+)`/g, (_, c) => {
    const i = inlineCode.length;
    inlineCode.push(`<code>${esc(c)}</code>`);
    return `\x00INLINE${i}\x00`;
  });

  // Escape everything else
  text = esc(text);

  // Headings
  text = text
    .replace(/^#{6} (.+)$/gm, '<h6>$1</h6>')
    .replace(/^#{5} (.+)$/gm, '<h5>$1</h5>')
    .replace(/^#{4} (.+)$/gm, '<h4>$1</h4>')
    .replace(/^### (.+)$/gm,  '<h3>$1</h3>')
    .replace(/^## (.+)$/gm,   '<h2>$1</h2>')
    .replace(/^# (.+)$/gm,    '<h1>$1</h1>');

  // Horizontal rules
  text = text.replace(/^---+$/gm, '<hr>');

  // Blockquotes
  text = text.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');

  // Bold + italic combined
  text = text
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    .replace(/\*\*(.+?)\*\*/g,     '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,         '<em>$1</em>')
    .replace(/__(.+?)__/g,         '<strong>$1</strong>')
    .replace(/_(.+?)_/g,           '<em>$1</em>');

  // Strikethrough
  text = text.replace(/~~(.+?)~~/g, '<del>$1</del>');

  // Task list checkboxes (before regular lists)
  text = text
    .replace(/^- \[x\] (.+)$/gim, '<li class="task-done">$1</li>')
    .replace(/^- \[ \] (.+)$/gim, '<li class="task-todo">$1</li>');

  // Unordered lists
  text = text.replace(/^[-*] (.+)$/gm, '<li>$1</li>');

  // Ordered lists
  text = text.replace(/^\d+\. (.+)$/gm, '<li class="ol">$1</li>');

  // Links
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener">$1</a>');

  // Images
  text = text.replace(/!\[([^\]]*)\]\(([^)]+)\)/g,
    '<img src="$2" alt="$1" style="max-width:100%;border-radius:var(--radius)">');

  // Wrap consecutive <li> runs in <ul>/<ol>
  text = text.replace(/((<li class="ol">.*<\/li>\n?)+)/g, '<ol>$1</ol>');
  text = text.replace(/((<li(?! class="ol")>.*<\/li>\n?)+)/g, '<ul>$1</ul>');

  // Paragraphs (blank-line separated, not headings/hr/lists/blockquotes/pre)
  const lines = text.split('\n');
  const out = [];
  let inPara = false;

  for (const line of lines) {
    const isBlock = /^<(h[1-6]|hr|ul|ol|li|blockquote|pre|div)/.test(line) || line === '';
    if (isBlock) {
      if (inPara) { out.push('</p>'); inPara = false; }
      out.push(line);
    } else {
      if (!inPara) { out.push('<p>'); inPara = true; }
      else out.push('<br>');
      out.push(line);
    }
  }
  if (inPara) out.push('</p>');
  text = out.join('\n');

  // Restore code blocks
  text = text.replace(/\x00CODEBLOCK(\d+)\x00/g, (_, i) => codeBlocks[i]);
  text = text.replace(/\x00INLINE(\d+)\x00/g,    (_, i) => inlineCode[i]);

  return text;
}

/**
 * YAML syntax highlighter — returns HTML with span-coloured tokens.
 * No external library; handles keys, strings, numbers, booleans, comments, list markers.
 */
export function highlightYaml(text) {
  const esc = s => String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  return text.split('\n').map(line => {
    // Full-line comment
    if (/^\s*#/.test(line)) {
      return `<span class="yl-comment">${esc(line)}</span>`;
    }

    // Key: value  (or  key:)
    const kvMatch = line.match(/^(\s*)([\w.-]+)(\s*:\s?)(.*)/);
    if (kvMatch) {
      const [, indent, key, colon, rest] = kvMatch;
      return `${esc(indent)}<span class="yl-key">${esc(key)}</span><span class="yl-colon">${esc(colon)}</span>${_valHtml(rest, esc)}`;
    }

    // List item  - value  OR  - name: value
    const listMatch = line.match(/^(\s*)(- ?)(.*)/);
    if (listMatch) {
      const [, indent, dash, rest] = listMatch;
      // Inline key-value after dash
      const kv2 = rest.match(/^([\w.-]+)(\s*:\s?)(.*)/);
      if (kv2) {
        const [, k, c, v] = kv2;
        return `${esc(indent)}<span class="yl-bullet">${esc(dash)}</span><span class="yl-key">${esc(k)}</span><span class="yl-colon">${esc(c)}</span>${_valHtml(v, esc)}`;
      }
      return `${esc(indent)}<span class="yl-bullet">${esc(dash)}</span>${_valHtml(rest, esc)}`;
    }

    return esc(line);
  }).join('\n');
}

function _valHtml(val, esc) {
  if (!val) return '';
  const v = val.trim();
  // Inline comment
  const commentIdx = val.indexOf(' #');
  if (commentIdx > 0) {
    const main = val.slice(0, commentIdx);
    const comment = val.slice(commentIdx);
    return `${_valHtml(main, esc)}<span class="yl-comment">${esc(comment)}</span>`;
  }
  // Quoted string
  if (/^(['"]).*\1$/.test(v)) return `<span class="yl-string">${esc(val)}</span>`;
  // Double-quoted
  if (v.startsWith('"')) return `<span class="yl-string">${esc(val)}</span>`;
  // Number
  if (/^-?\d+(\.\d+)?$/.test(v)) return `<span class="yl-number">${esc(val)}</span>`;
  // Boolean / null
  if (/^(true|false|yes|no|null|~)$/i.test(v)) return `<span class="yl-bool">${esc(val)}</span>`;
  // Block scalar indicator
  if (/^[|>][-+]?$/.test(v)) return `<span class="yl-scalar">${esc(val)}</span>`;
  // Array  [...]
  if (v.startsWith('[')) return `<span class="yl-array">${esc(val)}</span>`;
  // Plain string
  return `<span class="yl-plain">${esc(val)}</span>`;
}

/**
 * Validate YAML text. Returns { ok: true } or { ok: false, message, line }.
 * Uses a very lightweight structural check — good enough for workflow YAML.
 */
export function validateYaml(text) {
  const lines = text.split('\n');
  const indentStack = [0];

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const trimmed = raw.trimEnd();
    if (!trimmed || /^\s*#/.test(trimmed)) continue;

    // Check for tab characters
    if (/\t/.test(raw)) {
      return { ok: false, message: 'Tab characters not allowed in YAML — use spaces', line: i + 1 };
    }

    // Detect unclosed quotes
    const singleQuotes = (trimmed.match(/(?<!\\)'/g) || []).length;
    const doubleQuotes = (trimmed.match(/(?<!\\)"/g) || []).length;
    if (singleQuotes % 2 !== 0) {
      return { ok: false, message: 'Unclosed single quote', line: i + 1 };
    }
    if (doubleQuotes % 2 !== 0) {
      return { ok: false, message: 'Unclosed double quote', line: i + 1 };
    }

    // Detect duplicate colon in key (e.g.  key:: value)
    if (/^\s*[\w.-]+::/.test(trimmed)) {
      return { ok: false, message: 'Invalid key — double colon', line: i + 1 };
    }
  }
  return { ok: true };
}
