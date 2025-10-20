import React, { useEffect, useRef } from 'react';

interface Props {
  open: boolean;
  title?: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onCancel: () => void;
  onConfirm: () => void;
}

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  onCancel,
  onConfirm,
}: Props) {
  const dialogRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (!open) return;
      if (e.key === 'Escape') onCancel();
      if (e.key === 'Enter') onConfirm();
    }
    if (open) {
      document.addEventListener('keydown', onKey);
      // save focus
      const active = document.activeElement as HTMLElement | null;
      // focus the dialog
      setTimeout(() => dialogRef.current?.focus(), 0);
      return () => {
        document.removeEventListener('keydown', onKey);
        active?.focus();
      };
    }
  }, [open, onCancel, onConfirm]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        aria-describedby="confirm-desc"
        ref={dialogRef}
        tabIndex={-1}
        className="bg-white rounded-lg shadow-lg w-full max-w-md p-6 mx-4"
      >
        {title && (
          <h3 id="confirm-title" className="text-lg font-semibold text-gray-900 mb-2">
            {title}
          </h3>
        )}
        <p id="confirm-desc" className="text-sm text-gray-700 mb-6">
          {message}
        </p>

        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 rounded bg-red-600 text-white hover:bg-red-700"
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
