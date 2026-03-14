import React from 'react';

export const VTTMap: React.FC = () => {
  return (
    <div className="flex-grow bg-[var(--color-dark-bg)] flex items-center justify-center h-full relative overflow-hidden">
      <div className="absolute inset-0 bg-gray-900 opacity-20 pointer-events-none" style={{ backgroundImage: 'radial-gradient(#333 1px, transparent 1px)', backgroundSize: '20px 20px' }} />
      <div className="text-center z-10 p-8 border border-gray-700 bg-gray-800 rounded-lg shadow-xl shadow-black">
        <h1 className="text-3xl font-bold text-gray-300 mb-4">VTT Battle Map</h1>
        <p className="text-gray-500 max-w-md mx-auto">
          This area is reserved for the future virtual tabletop battle map. The map will be rendered here.
        </p>
      </div>
    </div>
  );
};
