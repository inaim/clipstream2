import { useState } from 'react';
import { X, Gift, Heart, Star, Sparkles, Trophy, Crown } from 'lucide-react';
import { surreal } from '../../lib/surrealdb';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';

interface GiftModalProps {
  recipientId: string;
  recipientName: string;
  videoId?: string;
  onClose: () => void;
  onSuccess?: () => void;
}

const GIFT_TYPES = [
  { id: 'rose', nameKey: 'gift.rose', icon: Heart, cost: 10, color: 'text-red-500' },
  { id: 'star', nameKey: 'gift.star', icon: Star, cost: 50, color: 'text-yellow-500' },
  { id: 'sparkle', nameKey: 'gift.sparkle', icon: Sparkles, cost: 100, color: 'text-blue-500' },
  { id: 'trophy', nameKey: 'gift.trophy', icon: Trophy, cost: 500, color: 'text-orange-500' },
  { id: 'crown', nameKey: 'gift.crown', icon: Crown, cost: 1000, color: 'text-purple-500' },
];

export function GiftModal({ recipientId, recipientName, videoId, onClose, onSuccess }: GiftModalProps) {
  const { t } = useLanguage();
  const { user } = useAuth();
  const [selectedGift, setSelectedGift] = useState(GIFT_TYPES[0]);
  const [quantity, setQuantity] = useState(1);
  const [message, setMessage] = useState('');
  const [balance, setBalance] = useState<number | null>(null);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  useState(() => {
    loadBalance();
  });

  const loadBalance = async () => {
    if (!user) return;

    const { data } = await surreal
      .from('virtual_currency')
      .select('balance')
      .eq('user_id', user.id)
      .maybeSingle();

    setBalance(data?.balance || 0);
  };

  const totalCost = selectedGift.cost * quantity;

  const handleSend = async () => {
    if (!user || balance === null || totalCost > balance) {
      setError(t('gift.insufficientBalance'));
      return;
    }

    setSending(true);
    setError('');

    try {
      const { error: deductError } = await surreal
        .from('virtual_currency')
        .update({
          balance: balance - totalCost,
          lifetime_spent: await surreal.rpc('increment_spent', { amount: totalCost }),
        })
        .eq('user_id', user.id);

      if (deductError) throw deductError;

      const { error: giftError } = await surreal
        .from('gifts')
        .insert({
          sender_id: user.id,
          recipient_id: recipientId,
          video_id: videoId || null,
          gift_type: selectedGift.id,
          amount: quantity,
          message: message.trim() || null,
        });

      if (giftError) throw giftError;

      const { error: creditError } = await surreal
        .from('virtual_currency')
        .update({
          balance: await surreal.rpc('increment_balance', { amount: Math.floor(totalCost * 0.7) }),
        })
        .eq('user_id', recipientId);

      if (creditError) throw creditError;

      // Record in contribution ledger:
      // - watch_contribution: $WATCH points awarded (tracks creator's revenue share)
      // - settlement_currency: actual payout will be in TrustedCrypto
      const { error: ledgerError } = await surreal
        .from('creator_partnership_ledger')
        .insert({
          creator_id: recipientId,
          transaction_type: 'revenue',
          amount: totalCost,
          source: 'gifting',
          settlement_currency: 'trustedcrypto',
          watch_contribution: Math.floor(totalCost * 0.8), // $WATCH points = 80% of gift value
          trustedcrypto_settled: false,
          metadata: {
            gift_type: selectedGift.id,
            quantity,
            sender_id: user.id,
            video_id: videoId,
          },
        });

      onSuccess?.();
      onClose();
    } catch (err: any) {
      setError(err.message || t('gift.failedToSendGift'));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 rounded-2xl w-full max-w-lg">
        <div className="border-b border-gray-800 p-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Gift className="w-6 h-6" />
              Send a Gift
            </h2>
            <p className="text-sm text-gray-400">to {recipientName}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-800 rounded-full transition active:scale-95"
          >
            <X className="w-6 h-6 text-white" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">Your Balance</span>
              <span className="text-xl font-bold text-white">{balance?.toLocaleString() || 0} coins</span>
            </div>
            <button className="w-full py-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg text-sm font-semibold hover:opacity-90 transition active:scale-95">
              Buy More Coins
            </button>
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-500 text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-3">
              Choose Gift
            </label>
            <div className="grid grid-cols-3 gap-3">
              {GIFT_TYPES.map((gift) => {
                const Icon = gift.icon;
                return (
                  <button
                    key={gift.id}
                    onClick={() => setSelectedGift(gift)}
                    className={`p-4 rounded-xl border-2 transition active:scale-95 ${
                      selectedGift.id === gift.id
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-gray-700 bg-gray-800 hover:border-gray-600'
                    }`}
                  >
                    <Icon className={`w-8 h-8 mx-auto mb-2 ${gift.color}`} />
                    <div className="text-white text-sm font-semibold">{gift.name}</div>
                    <div className="text-gray-400 text-xs">{gift.cost} coins</div>
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Quantity
            </label>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setQuantity(Math.max(1, quantity - 1))}
                className="w-10 h-10 bg-gray-800 text-white rounded-lg font-bold hover:bg-gray-700 transition active:scale-95"
              >
                -
              </button>
              <input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                className="flex-1 px-4 py-2 bg-gray-800 text-white text-center rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                min="1"
              />
              <button
                onClick={() => setQuantity(quantity + 1)}
                className="w-10 h-10 bg-gray-800 text-white rounded-lg font-bold hover:bg-gray-700 transition active:scale-95"
              >
                +
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Message (Optional)
            </label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Add a personal message..."
              rows={3}
              className="w-full px-4 py-3 bg-gray-800 text-white rounded-lg outline-none focus:ring-2 focus:ring-blue-500 transition resize-none"
              maxLength={200}
            />
          </div>

          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-center justify-between text-white">
              <span className="font-semibold">Total Cost:</span>
              <span className="text-2xl font-bold">{totalCost.toLocaleString()} coins</span>
            </div>
            <p className="text-xs text-gray-400 mt-2">
              Creator receives 70% ({Math.floor(totalCost * 0.7).toLocaleString()} coins)
            </p>
          </div>

          <button
            onClick={handleSend}
            disabled={sending || balance === null || totalCost > balance}
            className="w-full py-4 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-xl font-bold text-lg hover:shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
          >
            {sending ? t('gift.sending') : `${t('gift.sendGift')} (${totalCost} coins)`}
          </button>
        </div>
      </div>
    </div>
  );
}
