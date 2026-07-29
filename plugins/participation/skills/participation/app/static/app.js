// Shared helpers: toast messages and the native folder picker button.

function toast(message, isError) {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = message;
  el.classList.toggle('err', Boolean(isError));
  el.hidden = false;
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => { el.hidden = true; }, isError ? 7000 : 4000);
}

document.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-browse]');
  if (!button) return;
  event.preventDefault();

  const target = document.querySelector(button.dataset.browse);
  const label = button.textContent;
  button.disabled = true;
  button.textContent = 'Choose…';
  try {
    const response = await fetch('/api/browse-folder', { method: 'POST' });
    const data = await response.json();
    if (data.folder && target) {
      target.value = data.folder;
      target.dispatchEvent(new Event('input', { bubbles: true }));
    } else if (data.error) {
      toast(data.error + ' — type the path instead.', true);
    }
  } catch (err) {
    toast('Could not open the folder chooser — type the path instead.', true);
  } finally {
    button.disabled = false;
    button.textContent = label;
  }
});
