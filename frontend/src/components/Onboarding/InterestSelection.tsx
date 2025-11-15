import React, { useState } from 'react';
import {
  Music,
  Gamepad2,
  Dumbbell,
  Utensils,
  Plane,
  Palette,
  BookOpen,
  Tv,
  Laptop,
  Heart,
  Laugh,
  Car,
  Home,
  Sparkles,
  TrendingUp,
  Users,
} from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';

export interface Interest {
  id: string;
  name: string;
  icon: React.ReactNode;
  color: string;
}

const interests: Interest[] = [
  { id: 'music', name: 'Music', icon: <Music />, color: 'from-purple-500 to-pink-500' },
  { id: 'gaming', name: 'Gaming', icon: <Gamepad2 />, color: 'from-blue-500 to-cyan-500' },
  { id: 'sports', name: 'Sports', icon: <Dumbbell />, color: 'from-green-500 to-emerald-500' },
  { id: 'food', name: 'Food', icon: <Utensils />, color: 'from-orange-500 to-red-500' },
  { id: 'travel', name: 'Travel', icon: <Plane />, color: 'from-sky-500 to-blue-500' },
  { id: 'art', name: 'Art', icon: <Palette />, color: 'from-pink-500 to-rose-500' },
  { id: 'education', name: 'Education', icon: <BookOpen />, color: 'from-indigo-500 to-purple-500' },
  { id: 'entertainment', name: 'Entertainment', icon: <Tv />, color: 'from-red-500 to-pink-500' },
  { id: 'technology', name: 'Technology', icon: <Laptop />, color: 'from-cyan-500 to-blue-500' },
  { id: 'lifestyle', name: 'Lifestyle', icon: <Heart />, color: 'from-rose-500 to-pink-500' },
  { id: 'comedy', name: 'Comedy', icon: <Laugh />, color: 'from-yellow-500 to-orange-500' },
  { id: 'automotive', name: 'Automotive', icon: <Car />, color: 'from-gray-600 to-gray-800' },
  { id: 'home', name: 'Home & Garden', icon: <Home />, color: 'from-green-600 to-teal-500' },
  { id: 'beauty', name: 'Beauty', icon: <Sparkles />, color: 'from-purple-400 to-pink-400' },
  { id: 'business', name: 'Business', icon: <TrendingUp />, color: 'from-blue-600 to-indigo-600' },
  { id: 'community', name: 'Community', icon: <Users />, color: 'from-teal-500 to-cyan-500' },
];

interface InterestSelectionProps {
  onComplete: (selectedInterests: string[]) => void;
  onSkip?: () => void;
}

export const InterestSelection: React.FC<InterestSelectionProps> = ({ onComplete, onSkip }) => {
  const [selectedInterests, setSelectedInterests] = useState<string[]>([]);
  const { t } = useLanguage();

  const toggleInterest = (interestId: string) => {
    setSelectedInterests((prev) =>
      prev.includes(interestId)
        ? prev.filter((id) => id !== interestId)
        : [...prev, interestId]
    );
  };

  const handleContinue = () => {
    onComplete(selectedInterests);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-3">
            What are you interested in?
          </h1>
          <p className="text-lg text-gray-600">
            Select your interests to personalize your feed. Choose at least 3.
          </p>
        </div>

        {/* Interest Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mb-8">
          {interests.map((interest) => {
            const isSelected = selectedInterests.includes(interest.id);
            return (
              <button
                key={interest.id}
                onClick={() => toggleInterest(interest.id)}
                className={`
                  relative p-6 rounded-2xl transition-all duration-300 transform
                  ${
                    isSelected
                      ? `bg-gradient-to-br ${interest.color} text-white scale-105 shadow-xl`
                      : 'bg-white text-gray-700 hover:shadow-lg hover:scale-102'
                  }
                  border-2 ${isSelected ? 'border-transparent' : 'border-gray-200'}
                `}
              >
                {/* Checkmark */}
                {isSelected && (
                  <div className="absolute top-2 right-2 w-6 h-6 bg-white rounded-full flex items-center justify-center">
                    <svg
                      className="w-4 h-4 text-green-500"
                      fill="none"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path d="M5 13l4 4L19 7"></path>
                    </svg>
                  </div>
                )}

                {/* Icon */}
                <div className="flex flex-col items-center space-y-3">
                  <div className={`w-12 h-12 ${isSelected ? 'text-white' : 'text-gray-600'}`}>
                    {interest.icon}
                  </div>
                  <span className="font-semibold text-sm text-center">{interest.name}</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Selected Count */}
        <div className="text-center mb-6">
          <p className="text-gray-600">
            {selectedInterests.length} selected
            {selectedInterests.length < 3 && (
              <span className="text-orange-500 ml-2">
                (Select at least 3 to continue)
              </span>
            )}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          {onSkip && (
            <button
              onClick={onSkip}
              className="px-8 py-3 rounded-full border-2 border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 transition"
            >
              Skip for now
            </button>
          )}
          <button
            onClick={handleContinue}
            disabled={selectedInterests.length < 3}
            className={`
              px-12 py-3 rounded-full font-semibold transition-all duration-300
              ${
                selectedInterests.length >= 3
                  ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white hover:shadow-lg hover:scale-105'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }
            `}
          >
            Continue
          </button>
        </div>

        {/* Info */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            You can always change your interests later in settings
          </p>
        </div>
      </div>
    </div>
  );
};
