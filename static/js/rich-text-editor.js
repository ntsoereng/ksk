document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.rich-text-widget').forEach((widget) => {
    const source = document.getElementById(widget.dataset.textareaId);
    const editor = widget.querySelector('.rich-text-editor');
    if (!source || !editor) return;
    const form = editor.closest('form');
    source.style.display = 'none';
    const sync = () => { source.value = editor.innerHTML; };
    let savedRange = null;
    const rememberSelection = () => {
      const selection = window.getSelection();
      if (selection.rangeCount && editor.contains(selection.anchorNode)) {
        savedRange = selection.getRangeAt(0).cloneRange();
      }
    };
    const restoreSelection = () => {
      editor.focus();
      const selection = window.getSelection();
      const range = savedRange && editor.contains(savedRange.commonAncestorContainer)
        ? savedRange : document.createRange();
      if (range !== savedRange) {
        range.selectNodeContents(editor);
        range.collapse(false);
      }
      selection.removeAllRanges();
      selection.addRange(range);
      return range;
    };
    ['keyup', 'mouseup', 'input', 'focusout'].forEach((name) => editor.addEventListener(name, rememberSelection));
    widget.querySelectorAll('[data-command]').forEach((button) => {
      button.addEventListener('mousedown', (event) => event.preventDefault());
      button.addEventListener('click', () => {
        restoreSelection();
        const command = button.dataset.command;
        let value = button.dataset.value || null;
        if (command === 'createLink') {
          value = window.prompt('Enter a full URL (https://...) or email link (mailto:...)');
          if (!value) return;
          if (!/^(https?:\/\/|mailto:)/i.test(value)) return;
        }
        document.execCommand(command, false, value);
        rememberSelection();
        sync();
      });
    });

    const toggle = widget.querySelector('[data-image-toggle]');
    const panel = widget.querySelector('.rich-text-image-panel');
    const insert = widget.querySelector('[data-image-insert]');
    const status = widget.querySelector('.rich-text-status');
    const fileInput = widget.querySelector('[data-image-file]');
    const urlInput = widget.querySelector('[data-image-url]');
    toggle.addEventListener('mousedown', rememberSelection);
    toggle.addEventListener('click', () => {
      panel.hidden = !panel.hidden;
      toggle.setAttribute('aria-expanded', String(!panel.hidden));
      if (!panel.hidden) fileInput.focus();
    });

    let uploading = false;
    insert.addEventListener('click', async () => {
      if (uploading) return;
      const file = fileInput.files[0];
      let url = urlInput.value.trim();
      if (file && url) {
        status.textContent = 'Choose a file or enter a URL, then try again.';
        return;
      }
      const alt = widget.querySelector('[data-image-alt]').value.trim();
      if (!alt) {
        status.textContent = 'Add an image description for visitors using screen readers.';
        widget.querySelector('[data-image-alt]').focus();
        return;
      }
      if (file && file.size > 8 * 1024 * 1024) {
        status.textContent = 'Images must be 8 MB or smaller.';
        return;
      }
      uploading = true;
      insert.disabled = true;
      try {
        if (file) {
          status.textContent = 'Uploading image…';
          const body = new FormData();
          body.append('image', file);
          const response = await fetch(widget.dataset.uploadUrl, {
            method: 'POST', body, credentials: 'same-origin',
            headers: { 'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value },
          });
          if (response.redirected) throw new Error('Your session has expired. Sign in again before uploading.');
          let result;
          try { result = await response.json(); }
          catch { throw new Error('The upload could not be completed. Please try again.'); }
          if (!response.ok) throw new Error(result.error || 'You do not have permission to upload this image.');
          url = result.url;
        }
        if (!url || !(/^(https?:\/\/|\/(?!\/))/i.test(url)) || /[\\\x00-\x20]/.test(url)) {
          throw new Error('Choose an image or enter a valid https:// image URL.');
        }
        const image = document.createElement('img');
        image.src = url;
        image.alt = alt;
        image.loading = 'lazy';
        const figure = document.createElement('figure');
        figure.append(image);
        const caption = widget.querySelector('[data-image-caption]').value.trim();
        if (caption) {
          const text = document.createElement('figcaption');
          text.textContent = caption;
          figure.append(text);
        }
        const range = restoreSelection();
        range.deleteContents();
        // Split a text paragraph instead of nesting a figure inside it.
        let block = range.startContainer.nodeType === Node.ELEMENT_NODE
          ? range.startContainer : range.startContainer.parentElement;
        block = block.closest('p,h2,h3,blockquote,figure');
        if (block && editor.contains(block)) {
          const tail = document.createRange();
          tail.selectNodeContents(block);
          tail.setStart(range.startContainer, range.startOffset);
          const following = document.createElement('p');
          following.append(tail.extractContents());
          if (!following.textContent && !following.querySelector('img')) following.append(document.createElement('br'));
          block.after(figure, following);
          range.setStart(following, 0);
        } else {
          range.insertNode(figure);
          const following = document.createElement('p');
          following.append(document.createElement('br'));
          figure.after(following);
          range.setStart(following, 0);
        }
        range.collapse(true);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        rememberSelection();
        sync();
        fileInput.value = '';
        urlInput.value = '';
        widget.querySelector('[data-image-alt]').value = '';
        widget.querySelector('[data-image-caption]').value = '';
        status.textContent = 'Image inserted. Save the content to keep your changes.';
      } catch (error) {
        status.textContent = error.message || 'Image insertion failed. Please try again.';
      } finally {
        uploading = false;
        insert.disabled = false;
      }
    });
    editor.addEventListener('input', sync);
    form.addEventListener('submit', (event) => {
      if (uploading) {
        event.preventDefault();
        status.textContent = 'Wait for the image upload to finish before saving.';
      }
      sync();
    });
  });
});
