import React from 'react'
import { X, Clock, Cpu, CheckCircle, AlertCircle } from 'lucide-react'
import VideoInspector from './VideoInspector'
import useVideo from '../../hooks/useVideo'

type Step = {
  key: string
  label: string
  status: 'pending' | 'in_progress' | 'done' | 'failed'
  ts?: string
}

type Video = Record<string, any>

interface Props {
  open: boolean
  onClose: () => void
  video: Video | null
}

export default function VideoDrawer({ open, onClose, video }: Props) {
  if (!open || !video) return null

  // support passing either the full video object or an id string
  const videoId = typeof video === 'string' ? video : video?.id
  const live = useVideo(videoId)
  const merged = { ...(typeof video === 'object' && video ? video : {}), ...(live || {}) }

  const v = merged

  const steps: Step[] = [
    { key: 'queued', label: 'Queued', status: v.processing_steps?.queued?.status || 'done', ts: v.processing_steps?.queued?.ts },
    { key: 'encoding', label: 'Encoding', status: v.processing_steps?.encoding?.status || (v.status === 'processing' ? 'in_progress' : 'done'), ts: v.processing_steps?.encoding?.ts },
    { key: 'upload', label: 'Uploading', status: v.processing_steps?.upload?.status || 'pending', ts: v.processing_steps?.upload?.ts },
    { key: 'finalize', label: 'Finalizing', status: v.processing_steps?.finalize?.status || 'pending', ts: v.processing_steps?.finalize?.ts }
  ]

  const statusColor = (s: string) => {
    switch (s) {
      case 'uploading':
      case 'processing':
        return 'text-orange-600'
      case 'processed':
      case 'active':
        return 'text-green-600'
      case 'failed':
        return 'text-red-600'
      default:
        return 'text-gray-700'
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1 bg-black/40" onClick={onClose} />
      <aside className="w-full max-w-3xl bg-white h-full shadow-2xl overflow-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <div>
            <h3 className="text-lg font-semibold">{v.title}</h3>
            <p className="text-sm text-gray-500">{v.visibility || 'private'} · {v.status}</p>
          </div>
          <div>
            <button onClick={onClose} className="p-2 rounded-md hover:bg-gray-100">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="col-span-1">
            <div className="aspect-video bg-black rounded-lg overflow-hidden flex items-center justify-center">
              {v.cdn_url ? (
                <video src={v.cdn_url} controls className="w-full h-full object-contain" />
              ) : (
                <div className="text-white text-sm">Preview not available</div>
              )}
            </div>

            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600">Progress</div>
                <div className={`text-sm font-medium ${statusColor(v.status)}`}>{v.status}</div>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                <div className="h-3 bg-blue-600" style={{ width: `${v.processing_progress || 0}%` }} />
              </div>
            </div>
          </div>

          <div className="col-span-2">
            <div className="mb-4">
              <h4 className="text-sm font-semibold text-gray-700">Processing Steps</h4>
              <div className="mt-3 space-y-3">
                {steps.map(s => (
                  <div key={s.key} className="flex items-start gap-3">
                    <div className="w-8">
                      {s.status === 'pending' && <Clock className="w-5 h-5 text-gray-400" />}
                      {s.status === 'in_progress' && <Cpu className="w-5 h-5 text-orange-500" />}
                      {s.status === 'done' && <CheckCircle className="w-5 h-5 text-green-500" />}
                      {s.status === 'failed' && <AlertCircle className="w-5 h-5 text-red-500" />}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <div className="font-medium text-gray-800">{s.label}</div>
                        <div className="text-xs text-gray-400">{s.ts || ''}</div>
                      </div>
                      <div className="text-sm text-gray-500 mt-1">{v.processing_steps?.[s.key]?.message || ''}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="mb-4">
              <h4 className="text-sm font-semibold text-gray-700">Actions</h4>
              <div className="mt-3 flex gap-3">
                <button className="px-4 py-2 bg-green-600 text-white rounded-md">Publish</button>
                <button className="px-4 py-2 bg-gray-100 rounded-md">Retry</button>
                <button className="px-4 py-2 bg-red-50 text-red-600 rounded-md">Delete</button>
              </div>
            </div>

            <VideoInspector video={v} />
          </div>
        </div>
      </aside>
    </div>
  )
}
