import { useDispatch, useSelector } from 'react-redux';
import { resetForm } from '../store/crmSlice';

/**
 * Header — App branding, clean professional light theme.
 */
export default function Header() {
  const dispatch = useDispatch();
  const interactionId = useSelector((state) => state.crm.interactionId);

  return (
    <header className="flex items-center justify-between px-6 py-3 border-b"
      style={{ background: 'var(--color-glass)', borderColor: 'var(--color-border)', boxShadow: '0 8px 24px rgba(15, 23, 42, 0.35)' }}>
      
      {/* Logo & Brand */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl flex items-center justify-center text-lg font-bold text-white"
          style={{ background: 'linear-gradient(135deg, #4f46e5, #7c3aed)' }}>
          ⚕
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight" style={{ color: 'var(--color-text-primary)' }}>
            AI-CRM
            <span className="text-sm font-normal ml-2" style={{ color: 'var(--color-text-muted)' }}>
              HCP Module
            </span>
          </h1>
        </div>
      </div>

      {/* Center — Status */}
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: 'var(--color-success)' }}></div>
        <span className="text-xs font-medium" style={{ color: 'var(--color-text-secondary)' }}>
          LangGraph Agent Active
        </span>
          <span className="text-xs px-2 py-0.5 rounded-full font-medium"
            style={{ background: 'var(--color-info-bg)', color: 'var(--color-info)', border: '1px solid var(--color-info-border)' }}>
            llama-3.1-8b
          </span>
      </div>

      {/* Right — Actions */}
      <div className="flex items-center gap-3">
        {interactionId && (
          <span className="text-xs px-2.5 py-1 rounded-lg font-medium"
            style={{ background: 'var(--color-surface-light)', color: 'var(--color-text-secondary)', border: '1px solid var(--color-border)' }}>
            ID: #{interactionId}
          </span>
        )}
        <button
          onClick={() => dispatch(resetForm())}
          className="px-4 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer"
          style={{
            background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
            color: 'white',
            border: 'none',
            boxShadow: '0 1px 3px rgba(79, 70, 229, 0.3)',
          }}
          onMouseOver={(e) => { e.target.style.opacity = '0.9'; e.target.style.transform = 'translateY(-1px)'; }}
          onMouseOut={(e) => { e.target.style.opacity = '1'; e.target.style.transform = 'translateY(0)'; }}
        >
          + New Interaction
        </button>
      </div>
    </header>
  );
}
