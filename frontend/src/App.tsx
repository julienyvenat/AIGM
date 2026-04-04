import { Routes, Route, Link } from 'react-router-dom';
import { Home } from './pages/Home';
import { Studio } from './pages/Studio';
import { Play } from './pages/Play';

function App() {
  return (
    <div className="h-screen flex flex-col bg-gray-900 text-gray-100 font-sans">
      {/* Global Header */}
      <header className="p-4 border-b border-gray-700 bg-gray-800 flex justify-between items-center shrink-0">
        <Link to="/" className="text-xl font-bold text-emerald-400 hover:text-emerald-300">
          RPG AI Game Master
        </Link>
        <nav className="flex gap-4">
          <Link to="/" className="text-gray-300 hover:text-white font-medium">Lobby</Link>
          <Link to="/studio" className="text-gray-300 hover:text-white font-medium">Studio Pro</Link>
        </nav>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 overflow-hidden">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/studio" element={<Studio />} />
          <Route path="/play/:universeId" element={<Play />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
