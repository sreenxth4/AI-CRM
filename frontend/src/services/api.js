import axios from 'axios';

/**
 * API Service Layer — Axios calls to FastAPI backend.
 * 
 * Uses Vite proxy (/api → localhost:8000) so no CORS issues in dev.
 */

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Send a chat message to the LangGraph AI agent.
 */
export async function sendChatMessage(message, interactionId = null, conversationHistory = null) {
  const response = await api.post('/chat', {
    message,
    interaction_id: interactionId,
    conversation_history: conversationHistory,
  });
  return response.data;
}

/**
 * Get all logged interactions.
 */
export async function getInteractions() {
  const response = await api.get('/interactions');
  return response.data;
}

/**
 * Create or update an interaction from structured manual form input.
 */
export async function saveInteraction(formData, interactionId = null) {
  const payload = {
    hcp_name: formData.hcp_name,
    interaction_type: formData.interaction_type,
    interaction_date: formData.interaction_date,
    interaction_time: formData.interaction_time,
    attendees: formData.attendees,
    topics_discussed: formData.topics_discussed,
    product_discussed: formData.product_discussed,
    sentiment: formData.sentiment,
    follow_up_required: formData.follow_up_required,
    notes: formData.notes,
    shared_materials: formData.shared_materials,
    samples_distributed: formData.samples_distributed,
    outcomes: formData.outcomes,
    next_action: formData.next_action,
    summary: formData.summary,
    compliance_status: formData.compliance_status,
    ai_followup_suggestions: formData.ai_followup_suggestions,
  };

  const response = interactionId
    ? await api.put(`/interactions/${interactionId}`, payload)
    : await api.post('/interactions', payload);
  return response.data;
}

/**
 * Get a single interaction by ID.
 */
export async function getInteraction(id) {
  const response = await api.get(`/interactions/${id}`);
  return response.data;
}
