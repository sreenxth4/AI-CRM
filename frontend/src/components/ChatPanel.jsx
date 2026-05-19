import { useState, useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { sendMessage } from '../store/crmSlice';

/**
 * ChatPanel — AI Assistant chat interface, clean light theme.
 * Matches the assignment example: right-side panel with chat input.
 */

const pipelineSteps = [
  'Analyzing interaction...',
  'Extracting entities...',
  'Routing tool...',
  'Updating CRM...',
  'Generating response...',
];

function PipelineAnimation() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const timers = pipelineSteps.map((_, i) =>
      setTimeout(() => setStep(i), i * 1200)
    );
    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <div className="flex items-start gap-3 mb-4" style={{ animation: 'fadeIn 0.3s ease-out' }}>
      <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
        style={{ background: 'var(--color-primary-light)', color: 'var(--color-primary)' }}>
        AI
      </div>
      <div className="px-4 py-3 rounded-xl space-y-2 min-w-52"
        style={{ background: 'var(--color-surface-light)', border: '1px solid var(--color-border)' }}>
        {pipelineSteps.map((label, i) => (
          <div key={i} className="flex items-center gap-2 text-xs transition-all duration-300"
            style={{
              opacity: i <= step ? 1 : 0.3,
              color: i < step ? 'var(--color-success)' : i === step ? 'var(--color-primary)' : 'var(--color-text-muted)',
            }}>
            {i < step ? (
              <span style={{ animation: 'checkmark 0.3s ease-out' }}>&#10003;</span>
            ) : i === step ? (
              <div className="w-3 h-3 border-2 rounded-full"
                style={{ borderColor: 'var(--color-primary)', borderTopColor: 'transparent', animation: 'spin 0.8s linear infinite' }} />
            ) : (
              <div className="w-3 h-3 rounded-full" style={{ background: 'var(--color-border)' }} />
            )}
            <span>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function MessageBubble({ msg }) {
  const isUser = msg.role === 'user';
  const time = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';

  if (isUser) {
    return (
      <div className="flex flex-col items-end mb-4" style={{ animation: 'slideInRight 0.3s ease-out' }}>
        <div className="max-w-md px-4 py-3 rounded-2xl rounded-br-md text-sm text-white"
          style={{ background: 'linear-gradient(135deg, #4f46e5, #7c3aed)' }}>
          {msg.content}
        </div>
        {time && <span className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>{time}</span>}
      </div>
    );
  }

  return (
    <div className="flex flex-col items-start mb-4" style={{ animation: 'slideInLeft 0.3s ease-out' }}>
      {/* Tool badge + confidence */}
      {(msg.toolUsed || msg.confidence) && (
        <div className="flex items-center gap-2 mb-1 ml-10">
          {msg.toolUsed && (
            <span className="text-xs px-2 py-0.5 rounded-full font-medium"
              style={{ background: 'var(--color-primary-light)', color: 'var(--color-primary)', border: '1px solid #c7d2fe' }}>
              🔧 {msg.toolUsed}
            </span>
          )}
          {msg.confidence && (
            <span className="text-xs px-2 py-0.5 rounded-full font-medium"
              style={{ background: 'var(--color-success-bg)', color: 'var(--color-success)', border: '1px solid #a7f3d0' }}>
              {Math.round(msg.confidence * 100)}%
            </span>
          )}
        </div>
      )}

      <div className="flex items-start gap-2">
        <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
          style={{ background: 'var(--color-primary-light)', color: 'var(--color-primary)' }}>
          AI
        </div>
        <div className="max-w-lg">
          <div className={`px-4 py-3 rounded-2xl rounded-bl-md text-sm ${msg.isError ? '' : ''}`}
            style={{
              background: msg.isError ? 'var(--color-danger-bg)' : 'var(--color-surface-light)',
              color: msg.isError ? 'var(--color-danger)' : 'var(--color-text-primary)',
              border: `1px solid ${msg.isError ? '#fecaca' : 'var(--color-border)'}`,
            }}>
            {msg.content}
          </div>

          {/* Activity Log */}
          {msg.activityLog && msg.activityLog.length > 0 && (
            <div className="mt-2 px-3 py-2 rounded-lg space-y-1"
              style={{ background: 'var(--color-surface-light)', border: '1px solid var(--color-border)' }}>
              {msg.activityLog.map((activity, idx) => (
                <div key={idx} className="flex items-start gap-2 text-xs"
                  style={{ animation: `fadeInUp ${0.1 + idx * 0.08}s ease-out` }}>
                  <span style={{ color: 'var(--color-success)' }}>&#10003;</span>
                  <span style={{ color: 'var(--color-text-secondary)' }}>{activity}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      {time && <span className="text-xs mt-1 ml-10" style={{ color: 'var(--color-text-muted)' }}>{time}</span>}
    </div>
  );
}

export default function ChatPanel() {
  const dispatch = useDispatch();
  const { chatHistory, isLoading, interactionId } = useSelector((state) => state.crm);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory, isLoading]);

  const handleSend = () => {
    if (!input.trim() || isLoading) return;
    const message = input.trim();
    setInput('');

    const conversationHistory = chatHistory
      .filter((m) => !m.isError)
      .map((m) => ({
        role: m.role,
        content: m.content,
      }));

    dispatch(sendMessage({ message, interactionId, conversationHistory }));
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickActions = [
    { label: 'Summarize', icon: '📝', msg: 'Generate a summary of this interaction.' },
    { label: 'Check Compliance', icon: '✅', msg: 'Check compliance for this interaction.' },
    { label: 'Suggest Follow-up', icon: '🎯', msg: 'What should I do next?' },
  ];

  const examplePrompts = [
    '"Met Dr. Smith today. Discussed CardioX. Sentiment was positive. Shared brochures."',
    '"Correction: it was Dr. Johnson and sentiment was negative."',
    '"What should I do next?"',
  ];

  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--color-background-alt)' }}>
      {/* Panel Header */}
      <div className="px-5 py-3 border-b flex items-center justify-between"
        style={{ borderColor: 'var(--color-border)' }}>
        <div>
          <h2 className="text-base font-bold" style={{ color: 'var(--color-text-primary)' }}>
            AI Assistant
          </h2>
          <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
            Log interaction via chat
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full" style={{ background: 'var(--color-success)' }}></div>
          <span className="text-xs" style={{ color: 'var(--color-success)' }}>Online</span>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-5 py-4">
        {chatHistory.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-4">
            {/* Welcome Card */}
            <div className="p-5 rounded-xl mb-4 max-w-sm"
              style={{ background: 'var(--color-surface-light)', border: '1px solid var(--color-border)' }}>
              <p className="text-sm mb-3" style={{ color: 'var(--color-text-secondary)' }}>
                Log interaction details here (e.g., "Met Dr. Smith, discussed Product X efficacy, positive sentiment, shared brochure") or ask for help.
              </p>
            </div>

            {/* Example Prompts */}
            <div className="space-y-2 w-full max-w-sm">
              {examplePrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => { setInput(prompt.replace(/"/g, '')); inputRef.current?.focus(); }}
                  className="w-full text-left px-4 py-2.5 rounded-lg text-xs transition-all duration-200 cursor-pointer"
                  style={{
                    background: 'var(--color-surface)',
                    color: 'var(--color-text-secondary)',
                    border: '1px solid var(--color-border)',
                  }}
                  onMouseOver={(e) => { e.currentTarget.style.borderColor = 'var(--color-primary)'; e.currentTarget.style.background = 'var(--color-primary-light)'; }}
                  onMouseOut={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; e.currentTarget.style.background = 'var(--color-surface)'; }}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {chatHistory.map((msg, idx) => (
              <MessageBubble key={idx} msg={msg} />
            ))}
            {isLoading && <PipelineAnimation />}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      {interactionId && !isLoading && (
        <div className="px-5 py-2 flex items-center justify-center gap-2 border-t"
          style={{ borderColor: 'var(--color-border)' }}>
          {quickActions.map((action) => (
            <button
              key={action.label}
              onClick={() => dispatch(sendMessage({
                message: action.msg,
                interactionId,
                conversationHistory: chatHistory.filter((m) => !m.isError).map((m) => ({ role: m.role, content: m.content })),
              }))}
              className="px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all duration-200 cursor-pointer"
              style={{
                background: 'var(--color-surface)',
                color: 'var(--color-text-secondary)',
                border: '1px solid var(--color-border)',
              }}
              onMouseOver={(e) => { e.currentTarget.style.borderColor = 'var(--color-primary)'; e.currentTarget.style.color = 'var(--color-primary)'; }}
              onMouseOut={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; e.currentTarget.style.color = 'var(--color-text-secondary)'; }}
            >
              <span>{action.icon}</span>
              {action.label}
            </button>
          ))}
        </div>
      )}

      {/* Input Area */}
      <div className="px-5 py-3 border-t" style={{ borderColor: 'var(--color-border)' }}>
        <div className="flex items-end gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe interaction..."
            disabled={isLoading}
            className="flex-1 px-4 py-2.5 rounded-lg text-sm outline-none transition-all duration-200"
            style={{
              background: 'var(--color-surface-light)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-primary)',
            }}
            onFocus={(e) => { e.target.style.borderColor = 'var(--color-primary)'; e.target.style.boxShadow = '0 0 0 3px rgba(79,70,229,0.1)'; }}
            onBlur={(e) => { e.target.style.borderColor = 'var(--color-border)'; e.target.style.boxShadow = 'none'; }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer flex items-center gap-2"
            style={{
              background: input.trim() && !isLoading ? 'linear-gradient(135deg, #4f46e5, #7c3aed)' : 'var(--color-border)',
              color: input.trim() && !isLoading ? 'white' : 'var(--color-text-muted)',
              border: 'none',
            }}
          >
            <span>&#9651;</span> Log
          </button>
        </div>
      </div>
    </div>
  );
}
