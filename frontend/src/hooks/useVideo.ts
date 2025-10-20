import { useEffect, useState } from 'react'

export default function useVideo(videoId: string | undefined | null) {
  const [video, setVideo] = useState<Record<string, any> | null>(null)

  useEffect(() => {
    if (!videoId) return

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'

    let es: EventSource | null = null

    const fetchOnce = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/videos/${videoId}`)
        if (res.ok) {
          const data = await res.json()
          setVideo(data)
        }
      } catch (err) {
        console.warn('useVideo fetch error', err)
      }
    }

    fetchOnce()

    const channelUrl = `${API_BASE}/api/videos/${videoId}/events`
    try {
      es = new EventSource(channelUrl)
      es.onmessage = (ev) => {
        try {
          const payload = JSON.parse(ev.data)
          if (payload.video_id && payload.video_id === videoId) {
            setVideo(prev => ({ ...(prev || {}), ...payload }))
          }
        } catch (e) {
          // ignore non-json keep-alives
        }
      }
      es.onerror = () => {
        if (es) {
          es.close()
          es = null
        }
      }
    } catch (e) {
      // SSE not available in this environment
    }

    const poll = setInterval(() => fetchOnce(), 5000)
    return () => {
      if (es) es.close()
      clearInterval(poll)
    }
  }, [videoId])

  return video
}
