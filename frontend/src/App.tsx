import { Routes, Route, Link, Navigate } from 'react-router-dom';
import { Home } from './pages/Home';
import { Studio } from './pages/Studio';
import { Play } from './pages/Play';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks/useAuth';

function AppContent() {
  const { token, isLoading } = useAuth();

  return (
    <div className="h-screen flex flex-col bg-gray-900 text-gray-100 font-sans">
      {/* Global Header */}
      <header className="p-4 border-b border-gray-700 bg-gray-800 flex justify-between items-center shrink-0">
        <Link to="/" className="text-xl font-bold text-emerald-400 hover:text-emerald-300">
          RPG AI Game Master
        </Link>
        <nav className="flex gap-4 items-center">
          {token ? (
             <>
               <Link to="/dashboard" className="text-gray-300 hover:text-white font-medium">Dashboard</Link>
               <Link to="/studio" className="text-gray-300 hover:text-white font-medium">Studio Pro</Link>
             </>
          ) : (
             <>
               {!isLoading && <Link to="/login" className="text-gray-300 hover:text-white font-medium">Connexion</Link>}
             </>
          )}
        </nav>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 overflow-hidden">
        <Routes>
          {/* Root route redirects based on auth */}
          <Route path="/" element={
            isLoading ? <div className="p-8 text-center">Loading...</div> :
            token ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />
          } />

          <Route path="/login" element={
            token ? <Navigate to="/dashboard" replace /> : <Login />
          } />
          <Route path="/register" element={
            token ? <Navigate to="/dashboard" replace /> : <Register />
          } />

          {/* Protected Routes */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />

          <Route path="/studio" element={
            <ProtectedRoute>
              <Studio />
            </ProtectedRoute>
          } />

          <Route path="/play/:sessionId/:characterId" element={
            <ProtectedRoute>
              <Play />
            </ProtectedRoute>
          } />

          {/* Fallback for the old Home if needed temporarily or catch all */}
          <Route path="/lobby" element={<Home />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
