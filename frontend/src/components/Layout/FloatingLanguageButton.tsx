import { TikTokLanguageSelector } from './TikTokLanguageSelector';

interface FloatingLanguageButtonProps {
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  className?: string;
}

export function FloatingLanguageButton({ 
  position = 'bottom-right',
  className = ''
}: FloatingLanguageButtonProps) {
  const getPositionStyles = () => {
    switch (position) {
      case 'bottom-left':
        return 'bottom-20 left-4';
      case 'top-right':
        return 'top-20 right-4';
      case 'top-left':
        return 'top-20 left-4';
      default:
        return 'bottom-20 right-4';
    }
  };

  return (
    <div className={`fixed ${getPositionStyles()} z-40 ${className}`}>
      <TikTokLanguageSelector 
        variant="floating" 
        showText={false}
      />
    </div>
  );
}
