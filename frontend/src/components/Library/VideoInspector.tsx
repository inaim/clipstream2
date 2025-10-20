interface Props {
  video: any
}

export default function VideoInspector({ video }: Props) {
  return (
    <div className="mt-4 border-t pt-4">
      <h4 className="text-sm font-semibold text-gray-700 mb-2">Dev Inspector</h4>
      <div className="text-sm text-gray-600 mb-2">Celery Task: <code className="bg-gray-100 px-2 py-1 rounded">{video.processing_steps?.encoding?.task_id || '—'}</code></div>
      <div className="text-sm text-gray-600 mb-2">Channel: <code className="bg-gray-100 px-2 py-1 rounded">video:{video.id}:events</code></div>
      <div className="text-xs text-gray-500 mb-2">Raw state (expand for details)</div>
      <pre className="bg-black text-white text-xs p-3 rounded max-h-60 overflow-auto">{JSON.stringify(video, null, 2)}</pre>
    </div>
  )
}
