import { useState } from 'react';

import type { Character } from '../types';

interface CharacterManagerProps {
  character: Character;
  onComplete: (updatedCharacter: Character) => void;
}

export function CharacterManager({ character, onComplete }: CharacterManagerProps) {
  const [description, setDescription] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImageUrl, setGeneratedImageUrl] = useState<string | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  const handleGenerate = async () => {
    if (!description.trim()) return;
    setIsGenerating(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/characters/generate-portrait`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description }),
      });
      const data = await response.json();
      if (data.reference_portrait_url) {
        setGeneratedImageUrl(data.reference_portrait_url);
      }
    } catch (error) {
      console.error('Failed to generate portrait:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleValidate = async () => {
    if (!generatedImageUrl) return;
    setIsValidating(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/characters/${character.id}/set-reference`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reference_portrait_url: generatedImageUrl }),
      });
      const data = await response.json();
      if (data.status === 'success') {
        onComplete({ ...character, reference_portrait_url: data.reference_portrait_url });
      }
    } catch (error) {
      console.error('Failed to validate portrait:', error);
    } finally {
      setIsValidating(false);
    }
  };

  const handleStartAdventure = () => {
    if (character.reference_portrait_url) {
        onComplete(character);
    }
  };

  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-gray-900/80 backdrop-blur-sm">
      <div className="bg-gray-800 border-2 border-amber-900/50 rounded-lg shadow-[0_0_40px_rgba(0,0,0,0.8)] w-full max-w-4xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-gray-900 border-b border-gray-700 p-4 text-center">
          <h2 className="text-2xl font-serif font-bold text-amber-500">Profil du Héros</h2>
        </div>

        <div className="flex flex-1 p-6 gap-8">
          {/* Left Column: Stats */}
          <div className="w-1/3 flex flex-col gap-4 border-r border-gray-700 pr-6">
            <h3 className="text-xl font-bold text-gray-200 mb-2">{character.name}</h3>

            <div className="bg-gray-900/50 p-4 rounded-md border border-gray-700">
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Points de Vie (HP)</span>
                <span className="text-emerald-400 font-bold">{character.hp} / {character.max_hp}</span>
              </div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Classe d'Armure (AC)</span>
                <span className="text-blue-400 font-bold">{character.armor_class}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Vitesse</span>
                <span className="text-amber-400 font-bold">{character.speed} ft.</span>
              </div>
            </div>

            {character.reference_portrait_url && !generatedImageUrl && (
                <div className="mt-4 flex flex-col items-center">
                    <span className="text-sm text-gray-400 mb-2">Portrait Actuel :</span>
                    <img
                        src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${character.reference_portrait_url}`}
                        alt="Portrait Actuel"
                        className="w-48 h-48 object-cover rounded-md border-2 border-gray-600 shadow-lg"
                    />
                </div>
            )}
          </div>

          {/* Right Column: Generation */}
          <div className="w-2/3 flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <label htmlFor="description" className="text-sm font-medium text-gray-300">
                Générer votre visage
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Décrivez l'apparence de votre personnage (ex: Un rôdeur humain, grand, cheveux bruns longs, regard perçant, avec une cicatrice sur la joue gauche...)"
                className="w-full h-24 px-3 py-2 bg-gray-700 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500 text-sm resize-none"
              />
              <button
                onClick={handleGenerate}
                disabled={isGenerating || !description.trim()}
                className="self-end px-4 py-2 bg-gray-600 hover:bg-gray-500 disabled:opacity-50 text-white rounded-md transition-colors text-sm font-medium"
              >
                {isGenerating ? 'Génération en cours...' : 'Générer'}
              </button>
            </div>

            {generatedImageUrl && (
              <div className="mt-4 flex flex-col items-center gap-4 bg-gray-900/30 p-4 rounded-lg border border-gray-700">
                <img
                  src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${generatedImageUrl}`}
                  alt="Portrait généré"
                  className="w-64 h-64 object-cover rounded-md border-2 border-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.3)]"
                />
                <button
                  onClick={handleValidate}
                  disabled={isValidating}
                  className="px-6 py-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white font-bold rounded-md transition-colors shadow-lg"
                >
                  {isValidating ? 'Validation...' : 'Valider ce portrait'}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="bg-gray-900 border-t border-gray-700 p-6 flex justify-center">
          <button
            onClick={handleStartAdventure}
            disabled={!character.reference_portrait_url && !generatedImageUrl}
            className={`px-8 py-3 rounded-md font-bold text-lg transition-all shadow-lg ${
                character.reference_portrait_url || generatedImageUrl
                ? 'bg-gradient-to-r from-amber-600 to-yellow-500 hover:from-amber-500 hover:to-yellow-400 text-gray-900 shadow-[0_0_20px_rgba(245,158,11,0.5)]'
                : 'bg-gray-700 text-gray-500 cursor-not-allowed'
            }`}
          >
            Commencer l'aventure
          </button>
        </div>
      </div>
    </div>
  );
}
