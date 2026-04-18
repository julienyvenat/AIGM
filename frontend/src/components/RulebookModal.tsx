import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type {  GameSystem  } from '../types';

interface RulebookModalProps {
  system: GameSystem;
  onClose: () => void;
}

export const RulebookModal = ({ system, onClose }: RulebookModalProps) => {
  return (
    <div className="fixed inset-0 bg-black/80 flex justify-end z-[100]">
      {/* Overlay to click to close */}
      <div className="absolute inset-0 cursor-pointer" onClick={onClose} />

      <div className="relative w-full max-w-2xl bg-gray-900 border-l border-gray-700 h-full flex flex-col transform transition-transform duration-300 translate-x-0 overflow-hidden shadow-2xl">
        <div className="flex justify-between items-center p-4 border-b border-gray-700 bg-gray-800">
          <h2 className="text-xl font-bold text-emerald-400">Règles : {system.name}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors p-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>

        <div className="p-4 bg-gray-800 border-b border-gray-700 flex items-center gap-3">
          <div className="bg-emerald-900/50 p-2 rounded-lg border border-emerald-500 text-emerald-400">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2l8 4-8 4-8-4 8-4z"/><path d="M4 10v6l8 4 8-4v-6"/><path d="M12 22V10"/></svg>
          </div>
          <div>
            <span className="text-xs text-gray-400 uppercase tracking-wider block">Système de dés</span>
            <span className="font-bold text-gray-200">{system.dice_system}</span>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar text-gray-300">
          <div className="prose prose-invert prose-emerald max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {system.rules_summary}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
};
