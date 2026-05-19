import { useSelector, useDispatch } from 'react-redux';
import { updateFormField } from '../store/crmSlice';

/**
 * FormPanel — AI-Primary, User-Editable CRM form.
 * 
 * Primary interaction: Chat (AI populates via LLM tools)
 * Secondary interaction: Manual form edits (user can refine)
 * 
 * Philosophy: AI leads, user refines. Not locked; not free-for-all.
 */

function ComplianceBadge({ value }) {
  if (!value || value === 'Pending') {
    return (
      <span className="text-xs italic" style={{ color: 'var(--color-text-muted)' }}>
        Pending
      </span>
    );
  }

  const colors = {
    Compliant: { bg: 'var(--color-success-bg)', color: 'var(--color-success)', border: '#a7f3d0' },
    'Non-Compliant': { bg: 'var(--color-danger-bg)', color: 'var(--color-danger)', border: '#fecaca' },
    'Needs Review': { bg: 'var(--color-warning-bg)', color: 'var(--color-warning)', border: '#fde68a' },
  };
  const c = colors[value] || colors['Needs Review'];

  return (
    <span
      className="px-3 py-1 rounded-full text-xs font-semibold"
      style={{ background: c.bg, color: c.color, border: `1px solid ${c.border}` }}
    >
      {value}
    </span>
  );
}

function FieldHighlight({ isUpdated, children }) {
  return (
    <div
      className={`transition-all duration-300 ${isUpdated ? 'field-updated' : ''}`}
      style={{ borderRadius: '8px', padding: '2px' }}
    >
      {children}
    </div>
  );
}

function FieldLabel({ children }) {
  return (
    <label className="text-xs font-medium mb-1 block" style={{ color: 'var(--color-text-secondary)' }}>
      {children}
    </label>
  );
}

function inputStyles(multiline = false, isEditable = false) {
  return {
    background: isEditable ? 'var(--color-surface)' : 'var(--color-surface-light)',
    border: isEditable ? '1px solid var(--color-primary)' : '1px solid var(--color-border)',
    color: 'var(--color-text-primary)',
    cursor: isEditable ? 'text' : 'default',
    minHeight: multiline ? '68px' : undefined,
    transition: 'all 0.2s ease',
  };
}

function FormInput({ label, value, placeholder = '', type = 'text', fieldKey = null, onChangeField = null }) {
  const isEditable = fieldKey && onChangeField;
  
  return (
    <>
      <FieldLabel>{label}</FieldLabel>
      <input
        type={type}
        value={value || ''}
        placeholder={placeholder}
        className="w-full rounded-lg px-3 py-2 text-sm outline-none transition-all duration-200"
        style={inputStyles(false, isEditable)}
        onChange={(e) => isEditable && onChangeField(fieldKey, e.target.value)}
        disabled={!isEditable}
        title={isEditable ? "Editable field (AI-populated or manual)" : "Waiting for AI input"}
      />
    </>
  );
}

function FormTextarea({ label, value, placeholder = '', fieldKey = null, onChangeField = null }) {
  const isEditable = fieldKey && onChangeField;
  
  return (
    <>
      <FieldLabel>{label}</FieldLabel>
      <textarea
        value={value || ''}
        placeholder={placeholder}
        rows={3}
        className="w-full rounded-lg px-3 py-2 text-sm outline-none resize-none transition-all duration-200"
        style={inputStyles(true, isEditable)}
        onChange={(e) => isEditable && onChangeField(fieldKey, e.target.value)}
        disabled={!isEditable}
        title={isEditable ? "Editable field (AI-populated or manual)" : "Waiting for AI input"}
      />
    </>
  );
}

function FormSelect({ label, value, options, fieldKey = null, onChangeField = null }) {
  const isEditable = fieldKey && onChangeField;
  
  return (
    <>
      <FieldLabel>{label}</FieldLabel>
      <select
        value={value || ''}
        className="w-full rounded-lg px-3 py-2 text-sm outline-none transition-all duration-200"
        style={inputStyles(false, isEditable)}
        onChange={(e) => isEditable && onChangeField(fieldKey, e.target.value)}
        disabled={!isEditable}
        title={isEditable ? "Editable field (AI-populated or manual)" : "Waiting for AI input"}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </>
  );
}

function FollowUpToggle({ checked, fieldKey = null, onChangeField = null }) {
  const isEditable = fieldKey && onChangeField;
  
  return (
    <label className="flex items-center gap-2 text-sm cursor-pointer" style={{ color: 'var(--color-text-secondary)' }}>
      <input
        type="checkbox"
        checked={Boolean(checked)}
        className="w-4 h-4"
        onChange={(e) => isEditable && onChangeField(fieldKey, e.target.checked)}
        disabled={!isEditable}
        title={isEditable ? "Editable field" : "Waiting for AI input"}
      />
      Follow-up required
    </label>
  );
}

function AIFollowupSuggestions({ suggestions }) {
  if (!suggestions) return null;

  let items;
  try {
    items = typeof suggestions === 'string' ? JSON.parse(suggestions) : suggestions;
  } catch {
    return null;
  }

  if (!items.length) return null;

  return (
    <div className="mt-2 space-y-1.5" style={{ animation: 'fadeInUp 0.4s ease-out' }}>
      <label className="text-xs font-semibold" style={{ color: 'var(--color-primary)' }}>
        AI Suggested Follow-ups
      </label>
      {items.map((item, index) => (
        <div
          key={index}
          className="flex items-start gap-2 text-xs px-3 py-1.5 rounded-lg"
          style={{
            background: 'var(--color-primary-light)',
            color: 'var(--color-primary)',
            animation: `fadeInUp ${0.2 + index * 0.1}s ease-out`,
          }}
        >
          <span>&gt;</span>
          <span>{item}</span>
        </div>
      ))}
    </div>
  );
}

export default function FormPanel() {
  const dispatch = useDispatch();
  const {
    formData,
    updatedFieldKeys,
    activityLog,
    confidence,
  } = useSelector((state) => state.crm);

  const isUpdated = (key) => updatedFieldKeys.includes(key);
  
  const handleFieldChange = (fieldKey, value) => {
    dispatch(updateFormField({ fieldKey, value }));
  };

  return (
    <div className="h-full flex flex-col overflow-hidden" style={{ background: 'var(--color-background-alt)' }}>
      <div
        className="px-5 py-3 border-b flex items-center justify-between gap-3"
        style={{ borderColor: 'var(--color-border)' }}
      >
        <div>
          <h2 className="text-base font-bold" style={{ color: 'var(--color-text-primary)' }}>
            Log HCP Interaction
          </h2>
          <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
            AI-primary form (editable for refinement)
          </p>
        </div>
        <div className="flex items-center gap-2">
          {confidence && (
            <div
              className="px-2.5 py-1 rounded-lg text-xs font-medium"
              style={{
                background: 'var(--color-success-bg)',
                color: 'var(--color-success)',
                border: '1px solid #a7f3d0',
              }}
            >
              {Math.round(confidence * 100)}% confident
            </div>
          )}
          <span
            className="px-2.5 py-1 rounded-lg text-xs font-medium"
            style={{
              background: 'var(--color-info-bg)',
              color: 'var(--color-info)',
              border: '1px solid #bfdbfe',
            }}
          >
            AI Controlled
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
          <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-primary)' }}>
            Interaction Details
          </h3>

          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <FieldHighlight isUpdated={isUpdated('hcp_name')}>
                <FormInput
                  label="HCP Name"
                  value={formData.hcp_name}
                  placeholder="Dr. Rao"
                  fieldKey="hcp_name"
                  onChangeField={handleFieldChange}
                />
              </FieldHighlight>
              <FieldHighlight isUpdated={isUpdated('interaction_type')}>
                <FormSelect
                  label="Interaction Type"
                  value={formData.interaction_type}
                  options={[
                    { value: 'Meeting', label: 'Meeting' },
                    { value: 'Call', label: 'Call' },
                    { value: 'Email', label: 'Email' },
                    { value: 'Conference', label: 'Conference' },
                    { value: 'Other', label: 'Other' },
                  ]}
                  fieldKey="interaction_type"
                  onChangeField={handleFieldChange}
                />
              </FieldHighlight>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <FieldHighlight isUpdated={isUpdated('interaction_date')}>
                <FormInput
                  label="Date"
                  type="date"
                  value={formData.interaction_date}
                  fieldKey="interaction_date"
                  onChangeField={handleFieldChange}
                />
              </FieldHighlight>
              <FieldHighlight isUpdated={isUpdated('interaction_time')}>
                <FormInput
                  label="Time"
                  type="time"
                  value={formData.interaction_time}
                />
              </FieldHighlight>
            </div>

            <FieldHighlight isUpdated={isUpdated('attendees')}>
              <FormInput
                label="Attendees"
                value={formData.attendees}
                placeholder="Rep, MSL, nurse educator"
              />
            </FieldHighlight>

            <FieldHighlight isUpdated={isUpdated('topics_discussed')}>
              <FormTextarea
                label="Topics Discussed"
                value={formData.topics_discussed}
                placeholder="Key discussion points"
              />
            </FieldHighlight>
          </div>
        </div>

        <hr style={{ borderColor: 'var(--color-border)' }} />

        <div style={{ animation: 'fadeIn 0.4s ease-out' }}>
          <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-primary)' }}>
            Product, Materials, and Samples
          </h3>

          <div className="space-y-3">
            <FieldHighlight isUpdated={isUpdated('product_discussed')}>
              <FormInput
                label="Product Discussed"
                value={formData.product_discussed}
                placeholder="Product name"
                fieldKey="product_discussed"
                onChangeField={handleFieldChange}
              />
            </FieldHighlight>
            <FieldHighlight isUpdated={isUpdated('shared_materials')}>
              <FormInput
                label="Materials Shared"
                value={formData.shared_materials}
                placeholder="Brochure, study reprint, slide deck"
                fieldKey="shared_materials"
                onChangeField={handleFieldChange}
              />
            </FieldHighlight>
            <FieldHighlight isUpdated={isUpdated('samples_distributed')}>
              <FormInput
                label="Samples Distributed"
                value={formData.samples_distributed}
                placeholder="Sample details"
                fieldKey="samples_distributed"
                onChangeField={handleFieldChange}
              />
            </FieldHighlight>
          </div>
        </div>

        <hr style={{ borderColor: 'var(--color-border)' }} />

        <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
          <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-primary)' }}>
            Sentiment and Notes
          </h3>

          <div className="space-y-3">
            <FieldHighlight isUpdated={isUpdated('sentiment')}>
              <FormSelect
                label="Observed/Inferred HCP Sentiment"
                value={formData.sentiment}
                options={[
                  { value: '', label: 'Select sentiment' },
                  { value: 'Positive', label: 'Positive' },
                  { value: 'Neutral', label: 'Neutral' },
                  { value: 'Negative', label: 'Negative' },
                ]}
                fieldKey="sentiment"
                onChangeField={handleFieldChange}
              />
            </FieldHighlight>

            <FieldHighlight isUpdated={isUpdated('notes')}>
              <FormTextarea
                label="Notes"
                value={formData.notes}
                placeholder="Detailed field notes"
                fieldKey="notes"
                onChangeField={handleFieldChange}
              />
            </FieldHighlight>

            <FieldHighlight isUpdated={isUpdated('outcomes')}>
              <FormTextarea
                label="Outcomes"
                value={formData.outcomes}
                placeholder="Key outcomes or agreements"
                fieldKey="outcomes"
                onChangeField={handleFieldChange}
              />
            </FieldHighlight>
          </div>
        </div>

        <hr style={{ borderColor: 'var(--color-border)' }} />

        <div style={{ animation: 'fadeIn 0.6s ease-out' }}>
          <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-primary)' }}>
            Follow-up and Compliance
          </h3>

          <div className="space-y-3">
            <FieldHighlight isUpdated={isUpdated('follow_up_required')}>
              <FollowUpToggle
                checked={formData.follow_up_required}
                fieldKey="follow_up_required"
                onChangeField={handleFieldChange}
              />
            </FieldHighlight>

            <FieldHighlight isUpdated={isUpdated('next_action')}>
              <FormTextarea
                label="Next Action"
                value={formData.next_action}
                placeholder="Next steps or tasks"
                fieldKey="next_action"
                onChangeField={handleFieldChange}
              />
            </FieldHighlight>

            <FieldHighlight isUpdated={isUpdated('compliance_status')}>
              <FormSelect
                label="Compliance Status"
                value={formData.compliance_status}
                options={[
                  { value: '', label: 'Pending' },
                  { value: 'Pending', label: 'Pending' },
                  { value: 'Compliant', label: 'Compliant' },
                  { value: 'Needs Review', label: 'Needs Review' },
                  { value: 'Non-Compliant', label: 'Non-Compliant' },
                ]}
              />
              <div className="mt-2">
                <ComplianceBadge value={formData.compliance_status} />
              </div>
            </FieldHighlight>

            <FieldHighlight isUpdated={isUpdated('ai_followup_suggestions')}>
              <AIFollowupSuggestions suggestions={formData.ai_followup_suggestions} />
            </FieldHighlight>
          </div>
        </div>

        <hr style={{ borderColor: 'var(--color-border)' }} />

        <div style={{ animation: 'fadeIn 0.7s ease-out' }}>
          <h3 className="text-sm font-semibold mb-3" style={{ color: 'var(--color-text-primary)' }}>
            Summary
          </h3>
          <FieldHighlight isUpdated={isUpdated('summary')}>
            <FormTextarea
              label="Summary"
              value={formData.summary}
              placeholder="AI-generated summary"
            />
          </FieldHighlight>
        </div>

        {activityLog && activityLog.length > 0 && (
          <div
            className="p-4 rounded-xl"
            style={{
              background: 'var(--color-surface-light)',
              border: '1px solid var(--color-border)',
              animation: 'fadeInUp 0.4s ease-out',
            }}
          >
            <h3
              className="text-xs font-semibold uppercase tracking-wider mb-3"
              style={{ color: 'var(--color-text-muted)' }}
            >
              Activity Feed
            </h3>
            <div className="space-y-1.5">
              {activityLog.map((activity, index) => (
                <div
                  key={index}
                  className="flex items-start gap-2 text-xs"
                  style={{ animation: `fadeInUp ${0.2 + index * 0.1}s ease-out` }}
                >
                  <span style={{ color: 'var(--color-success)' }}>&#10003;</span>
                  <span style={{ color: 'var(--color-text-secondary)' }}>{activity}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
