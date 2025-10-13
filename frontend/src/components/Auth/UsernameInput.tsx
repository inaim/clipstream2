import { useState, useEffect } from 'react';

interface UsernameInputProps {
  value: string;
  onChange: (value: string) => void;
  className?: string;
}

// Lightweight username input without external service checks.
// Keeps the same API but only performs client-side validation.
export function UsernameInput({ value, onChange, className = '' }: UsernameInputProps) {
  const [local, setLocal] = useState(value);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLocal(value);
  }, [value]);

  useEffect(() => {
    if (!local) {
      setError(null);
      return;
    }
    const cleaned = local.toLowerCase().replace(/[^a-z0-9._]/g, '');
    if (cleaned.length < 3) {
      setError('Username must be at least 3 characters');
    } else if (cleaned.length > 30) {
      setError('Username too long');
    } else {
      setError(null);
    }
  }, [local]);

  return (
    <div className="space-y-2">
      <input
        type="text"
        value={local}
        onChange={(e) => {
          const cleaned = e.target.value.toLowerCase().replace(/[^a-z0-9._]/g, '');
          setLocal(cleaned);
          onChange(cleaned);
        }}
        placeholder="username"
        className={className}
      />

      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
}
