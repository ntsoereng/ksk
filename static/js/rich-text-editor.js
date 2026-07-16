document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.rich-text-widget').forEach((widget) => {
    const source = document.getElementById(widget.dataset.textareaId);
    const editor = widget.querySelector('.rich-text-editor');
    if (!source || !editor) return;

    source.style.display = 'none';
    const sync = () => { source.value = editor.innerHTML; };

    widget.querySelectorAll('[data-command]').forEach((button) => {
      button.addEventListener('click', () => {
        editor.focus();
        const command = button.dataset.command;
        let value = button.dataset.value || null;
        if (command === 'createLink') {
          value = window.prompt('Enter a full URL (https://...) or email link (mailto:...)');
          if (!value) return;
        }
        document.execCommand(command, false, value);
        sync();
      });
    });

    editor.addEventListener('input', sync);
    editor.closest('form').addEventListener('submit', sync);
  });
});
