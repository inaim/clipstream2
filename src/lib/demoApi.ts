export async function uploadViaBackend(file: File, title: string) {
  const API_BASE = ((import.meta as any).env.VITE_BACKEND_URL || (import.meta as any).env.VITE_API_BASE_URL || 'http://localhost:8000') as string;
  const token = localStorage.getItem('clipstream_token');
  const fd = new FormData();
  fd.append('file', file);
  fd.append('title', title);

  const res = await fetch(`${API_BASE}/api/upload`, {
    method: 'POST',
    body: fd,
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || 'Upload failed');
  }
  const data = await res.json();
  // get playback url
  const playRes = await fetch(`${API_BASE}/api/playback/${data.video_id}`);
  if (!playRes.ok) {
    const txt = await playRes.text();
    throw new Error(txt || 'Playback URL fetch failed');
  }
  const playJson = await playRes.json();
  return { ...data, playback_url: playJson.playback_url };
}

export async function getPlaybackUrl(videoId: number) {
  const API_BASE = ((import.meta as any).env.VITE_BACKEND_URL || (import.meta as any).env.VITE_API_BASE_URL || 'http://localhost:8000') as string;
  const res = await fetch(`${API_BASE}/api/playback/${videoId}`);
  if (!res.ok) throw new Error('Playback URL fetch failed');
  return (await res.json()).playback_url;
}
