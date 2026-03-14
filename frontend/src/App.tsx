import { ChatArea } from './components/ChatArea';
import { VTTMap } from './components/VTTMap';

function App() {
  return (
    <div className="h-screen w-screen flex bg-[var(--color-dark-bg)] text-[var(--color-dark-text)] overflow-hidden font-sans">
      <ChatArea />
      <VTTMap />
    </div>
  );
}

export default App;
