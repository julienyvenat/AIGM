import React, { useState, useRef, useEffect } from 'react';
import type { GameMessage } from '../hooks/useGameWebSocket';

export interface ChatPanelProps {
  messages: GameMessage[];
  sendMessage: (text: string) => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ messages, sendMessage }) => {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputText.trim()) {
      sendMessage(inputText);
      setInputText('');
    }
  };

  const renderMessage = (msg: GameMessage, index: number) => {
    const isUser = msg.sender === 'user';
    let bubbleClass = 'p-3 rounded-lg max-w-[80%] break-words ';
    let containerClass = `flex mb-4 ${isUser ? 'justify-end' : 'justify-start'}`;

    if (isUser) {
      bubbleClass += 'bg-gray-700 text-gray-100 rounded-br-none';
    } else {
      bubbleClass += 'rounded-bl-none border ';
      if (msg.category === 'ROLEPLAY') {
        bubbleClass += 'bg-blue-900/30 border-blue-700 text-blue-100 italic';
      } else if (msg.category === 'ACTION') {
        bubbleClass += 'bg-red-900/30 border-red-700 text-red-100 font-bold';
      } else if (msg.category === 'SYSTEM') {
        containerClass = 'flex mb-4 justify-center w-full';
        bubbleClass = 'text-sm text-gray-400 text-center bg-transparent border-none';
      } else {
        // Default narrator or other server messages
        bubbleClass += 'bg-gray-800 border-gray-600 text-gray-200';
      }
    }

    return (
      <div key={msg.id || index} className={containerClass}>
        <div className={bubbleClass}>
          {msg.message}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-gray-900 text-gray-100 rounded-lg overflow-hidden border border-gray-700 shadow-xl">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-10 italic">
            Aucun message pour le moment. L'aventure commence...
          </div>
        ) : (
          messages.map((msg, idx) => renderMessage(msg, idx))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="p-4 bg-gray-800 border-t border-gray-700 flex gap-2">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Que faites-vous ?"
          className="flex-1 bg-gray-700 text-gray-100 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all placeholder-gray-400"
          autoComplete="off"
        />
        <button
          type="submit"
          disabled={!inputText.trim()}
          className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-800"
        >
          Envoyer
        </button>
      </form>
    </div>
  );
};
