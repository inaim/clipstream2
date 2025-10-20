async function fetchContent() {
  try {
    const res = await fetch('/api/content');
    const json = await res.json();
    const cacheStatus = res.headers.get('X-Cache-Status') || res.headers.get('x-cache-status') || 'unknown';

    document.getElementById('result').innerText = `status: ${res.status}\ncache: ${cacheStatus}\n${JSON.stringify(json, null, 2)}`;
  } catch (err) {
    document.getElementById('result').innerText = 'Fetch error: ' + err;
  }
}

fetchContent();
setInterval(fetchContent, 3000);
