import React from 'react';

interface SceneViewerProps {
  imageUrl: string;
  onClose: () => void;
}

export const SceneViewer: React.FC<SceneViewerProps> = ({ imageUrl, onClose }) => {
  return (
    <div className="absolute inset-0 bg-black/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center p-8 animate-in fade-in duration-300">
      <div className="relative max-w-full max-h-full flex flex-col items-center">
        <button
          onClick={onClose}
          className="absolute -top-12 right-0 bg-gray-800 hover:bg-gray-700 text-gray-200 p-2 rounded-full shadow-lg transition-colors border border-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          title="Fermer la vision"
          aria-label="Fermer la vision"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <img
          src={imageUrl}
          alt="Vision du Maître de Jeu"
          className="max-w-full max-h-[85vh] object-contain border-4 border-stone-600 rounded-lg shadow-2xl"
        />

        <div className="mt-4 text-emerald-400 font-medium italic animate-pulse">
          Une vision vous a été partagée...
        </div>
      </div>
    </div>
  );
};
