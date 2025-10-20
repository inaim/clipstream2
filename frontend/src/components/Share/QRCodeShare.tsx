import { QRCodeSVG } from 'qrcode.react';
import { X, Download, Copy, Check } from 'lucide-react';
import { useState } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';

interface QRCodeShareProps {
  videoId: string;
  videoTitle: string;
  onClose: () => void;
}

export function QRCodeShare({ videoId, videoTitle, onClose }: QRCodeShareProps) {
  const { t } = useLanguage();
  const [copied, setCopied] = useState(false);
  const videoUrl = `${window.location.origin}/video/${videoId}`;

  const handleCopyUrl = async () => {
    await navigator.clipboard.writeText(videoUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadQR = () => {
    const svg = document.getElementById('qr-code-svg');
    if (!svg) return;

    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();

    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx?.drawImage(img, 0, 0);
      const pngFile = canvas.toDataURL('image/png');

      const downloadLink = document.createElement('a');
      downloadLink.download = `clipstream-${videoId}.png`;
      downloadLink.href = pngFile;
      downloadLink.click();
    };

    img.src = 'data:image/svg+xml;base64,' + btoa(svgData);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-md w-full p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">{t('share.shareVideo')}</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition"
          >
            <X className="w-6 h-6 text-gray-600" />
          </button>
        </div>

        <div className="space-y-4">
          <div className="bg-white p-6 rounded-2xl border-2 border-gray-200 flex justify-center">
            <QRCodeSVG
              id="qr-code-svg"
              value={videoUrl}
              size={240}
              level="H"
              includeMargin
              fgColor="#000000"
              bgColor="#FFFFFF"
            />
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-600 mb-1">{t('share.scanToWatch')}</p>
            <p className="text-lg font-semibold text-gray-900 truncate">{videoTitle}</p>
          </div>

          <div className="space-y-2">
            <button
              onClick={handleDownloadQR}
              className="w-full py-3 bg-gradient-cyber text-white rounded-xl font-semibold hover:opacity-90 transition flex items-center justify-center gap-2"
            >
              <Download className="w-5 h-5" />
              Download QR Code
            </button>

            <button
              onClick={handleCopyUrl}
              className="w-full py-3 bg-gray-100 text-gray-900 rounded-xl font-semibold hover:bg-gray-200 transition flex items-center justify-center gap-2"
            >
              {copied ? (
                <>
                  <Check className="w-5 h-5 text-mint-green" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="w-5 h-5" />
                  Copy Link
                </>
              )}
            </button>
          </div>

          <div className="p-4 bg-gray-50 rounded-xl">
            <p className="text-xs text-gray-500 break-all">{videoUrl}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
