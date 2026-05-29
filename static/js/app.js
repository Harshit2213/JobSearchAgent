// Populated progressively as phases are implemented.

const uploadForm = document.getElementById('upload-form');
const uploadResult = document.getElementById('upload-result');

uploadForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = new FormData(uploadForm);
  uploadResult.textContent = 'Analysing resume…';
  uploadResult.classList.remove('hidden');

  try {
    const res = await fetch('/api/upload-resume', { method: 'POST', body: data });
    const json = await res.json();
    if (!res.ok) {
      uploadResult.textContent = `Error: ${json.detail ?? res.statusText}`;
      return;
    }
    uploadResult.innerHTML = `<pre>${JSON.stringify(json, null, 2)}</pre>`;
  } catch (err) {
    uploadResult.textContent = `Network error: ${err.message}`;
  }
});
