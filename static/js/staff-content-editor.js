document.addEventListener('DOMContentLoaded', () => {
  const title = document.querySelector('#id_title, #id_name');
  const slug = document.querySelector('#id_slug');
  if (!title || !slug) return;

  let slugWasEdited = Boolean(slug.value);
  slug.addEventListener('input', () => { slugWasEdited = true; });
  title.addEventListener('input', () => {
    if (slugWasEdited) return;
    slug.value = title.value
      .toLowerCase()
      .normalize('NFKD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
  });
});
