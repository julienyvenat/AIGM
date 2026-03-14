import React, { useState, useRef, useEffect } from 'react';
import { useGameWebSocket } from '../hooks/useGameWebSocket';

export const ChatArea: React.FC = () => {
  const { messages, isConnected, error, sendMessage } = useGameWebSocket();
  const [inputValue, setInputValue] = useState('');
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    sendMessage({
      type: 'user_message',
      payload: inputValue,
      sender: 'User',
      timestamp: Date.now(),
    });

    setInputValue('');
  };

  useEffect(() => {
    // Scroll to bottom on new message
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-full w-[400px] border-r border-gray-700 bg-[var(--color-dark-panel)] text-gray-200">
      <div className="flex-none p-4 border-b border-gray-700 bg-gray-900">
        <h2 className="text-xl font-bold">RPG Chat & Logs</h2>
        <div className="flex items-center text-sm mt-1">
          <div className={`w-2 h-2 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className={isConnected ? 'text-green-400' : 'text-red-400'}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
          {error && <span className="ml-2 text-red-500 text-xs">- {error}</span>}
        </div>
      </div>

      <div className="flex-grow overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`p-3 rounded-lg ${msg.sender === 'User' ? 'bg-blue-900 ml-8' : 'bg-gray-800 mr-8'}`}>
            <div className="text-xs text-gray-400 mb-1">{msg.sender || 'System'}</div>
            <div className="text-gray-200 break-words">{typeof msg.payload === 'string' ? msg.payload : JSON.stringify(msg.payload || msg)}</div>
          </div>
        ))}
        <div ref={endOfMessagesRef} />
      </div>

      <form onSubmit={handleSend} className="flex-none p-4 border-t border-gray-700 bg-gray-900 flex space-x-2">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Type your action or message..."
          disabled={!isConnected}
          className="flex-grow bg-gray-800 text-gray-200 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!isConnected || !inputValue.trim()}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </form>
    </div>
  );
};
