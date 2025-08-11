(() => {
  const input = document.getElementById('file-input');
  const viewer = document.getElementById('viewer');

  input.addEventListener('change', async () => {
    const file = input.files[0];
    if (!file) {
      return;
    }

    const formData = new FormData();
    formData.append('file', file, file.name);

    try {
      const response = await fetch('/viewer', {
        method: 'POST',
        body: formData,
        credentials: 'include',
      });
      const html = await response.text();
      viewer.innerHTML = html;
    } catch (err) {
      viewer.innerHTML = '<p>Upload failed.</p>';
    }
  });
})();
