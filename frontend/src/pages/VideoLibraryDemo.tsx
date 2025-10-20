import { useState } from 'react'
import VideoDrawer from '../components/Library/VideoDrawer'

const mockVideos = [
  {
    id: 'video:1',
    title: 'Sample Processing Video',
    description: 'A demo video in processing',
    status: 'processing',
    visibility: 'private',
    processing_progress: 45,
    processing_steps: {
      queued: { status: 'done', ts: '2025-10-18T10:00:00Z' },
      encoding: { status: 'in_progress', ts: '2025-10-18T10:01:00Z', task_id: 'abc-123' }
    }
  },
  {
    id: 'video:2',
    title: 'Ready to Publish',
    description: 'Encoded and ready',
    status: 'processed',
    visibility: 'private',
    processing_progress: 100,
    cdn_url: '',
    processing_steps: { queued: { status: 'done' }, encoding: { status: 'done' }, upload: { status: 'done' } }
  },
  {
    id: 'video:3',
    title: 'Failed Encode',
    description: 'Encoding failed due to codec',
    status: 'failed',
    visibility: 'private',
    processing_progress: 10,
    processing_steps: { queued: { status: 'done' }, encoding: { status: 'failed', message: 'libaom error' } }
  }
]

export default function VideoLibraryDemo() {
  const [selected, setSelected] = useState<any | null>(null)
  const [open, setOpen] = useState(false)

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-6">Video Library Demo</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {mockVideos.map(v => (
          <div key={v.id} onClick={() => { setSelected(v); setOpen(true) }}>
            <div className="cursor-pointer">
              <div className="bg-gray-100 rounded-lg aspect-video flex items-center justify-center">Preview</div>
              <div className="mt-2">
                <h3 className="font-semibold">{v.title}</h3>
                <p className="text-sm text-gray-500">{v.status}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <VideoDrawer open={open} onClose={() => setOpen(false)} video={selected} />
    </div>
  )
}
