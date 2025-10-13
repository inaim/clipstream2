import { Check, X } from 'lucide-react';

interface PasswordStrengthProps {
  password: string;
}

export function PasswordStrength({ password }: PasswordStrengthProps) {
  const checks = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
  };

  const strength = Object.values(checks).filter(Boolean).length;
  const strengthPercentage = (strength / 5) * 100;

  const getStrengthColor = () => {
    if (strength <= 2) return 'bg-red-500';
    if (strength === 3) return 'bg-sunset-orange';
    if (strength === 4) return 'bg-neon-yellow';
    return 'bg-mint-green';
  };

  const getStrengthText = () => {
    if (strength <= 2) return 'Weak';
    if (strength === 3) return 'Fair';
    if (strength === 4) return 'Good';
    return 'Strong';
  };

  if (!password) return null;

  return (
    <div className="space-y-3">
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Password strength</span>
          <span className={`font-semibold ${strength >= 4 ? 'text-mint-green' : 'text-gray-600'}`}>
            {getStrengthText()}
          </span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${getStrengthColor()}`}
            style={{ width: `${strengthPercentage}%` }}
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <PasswordCheck met={checks.length} label="At least 8 characters" />
        <PasswordCheck met={checks.uppercase} label="One uppercase letter" />
        <PasswordCheck met={checks.lowercase} label="One lowercase letter" />
        <PasswordCheck met={checks.number} label="One number" />
        <PasswordCheck met={checks.special} label="One special character" />
      </div>
    </div>
  );
}

function PasswordCheck({ met, label }: { met: boolean; label: string }) {
  return (
    <div className={`flex items-center gap-2 text-sm transition-colors ${met ? 'text-mint-green' : 'text-gray-400'}`}>
      {met ? (
        <Check className="w-4 h-4" />
      ) : (
        <X className="w-4 h-4" />
      )}
      <span>{label}</span>
    </div>
  );
}
