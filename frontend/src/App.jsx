import Header from './components/Header';
import FormPanel from './components/FormPanel';
import ChatPanel from './components/ChatPanel';

/**
 * App — Split-screen layout.
 * Left 40%: Read-only CRM form (AI-controlled)
 * Right 60%: AI chat assistant for conversational extraction
 */
export default function App() {
  return (
    <div className="h-screen flex flex-col overflow-hidden" style={{ background: 'var(--color-background)' }}>
      <Header />
      <main className="flex-1 flex overflow-hidden">
        {/* Left Panel — CRM Form */}
        <div className="w-[40%] border-r overflow-hidden" style={{ borderColor: 'var(--color-border)' }}>
          <FormPanel />
        </div>
        {/* Right Panel — AI Chat */}
        <div className="w-[60%] overflow-hidden">
          <ChatPanel />
        </div>
      </main>
    </div>
  );
}
