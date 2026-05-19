import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { saveInteraction, sendChatMessage } from '../services/api';

/**
 * CRM Redux Slice — manages form state, chat history, and AI interactions.
 * 
 * The form is AI-controlled; chat extraction drives all updates.
 */

// Async thunk — sends message to backend and processes structured response
export const sendMessage = createAsyncThunk(
  'crm/sendMessage',
  async ({ message, interactionId, conversationHistory }, { rejectWithValue }) => {
    try {
      const response = await sendChatMessage(message, interactionId, conversationHistory);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to process message');
    }
  }
);

export const saveStructuredInteraction = createAsyncThunk(
  'crm/saveStructuredInteraction',
  async ({ formData, interactionId }, { rejectWithValue }) => {
    try {
      const response = await saveInteraction(formData, interactionId);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to save interaction');
    }
  }
);

const initialFormData = {
  hcp_name: '',
  interaction_type: 'Meeting',
  interaction_date: '',
  interaction_time: '',
  attendees: '',
  topics_discussed: '',
  product_discussed: '',
  sentiment: '',
  follow_up_required: false,
  notes: '',
  shared_materials: '',
  samples_distributed: '',
  outcomes: '',
  next_action: '',
  summary: '',
  compliance_status: '',
  ai_followup_suggestions: '',
};

const crmSlice = createSlice({
  name: 'crm',
  initialState: {
    formData: { ...initialFormData },
    interactionId: null,
    chatHistory: [],
    isLoading: false,
    error: null,
    lastToolUsed: null,
    confidence: null,
    activityLog: [],
    updatedFieldKeys: [],
    saveStatus: 'idle',
    saveError: null,
  },
  reducers: {
    resetForm: (state) => {
      state.formData = { ...initialFormData };
      state.interactionId = null;
      state.chatHistory = [];
      state.lastToolUsed = null;
      state.confidence = null;
      state.activityLog = [];
      state.updatedFieldKeys = [];
      state.error = null;
      state.saveStatus = 'idle';
      state.saveError = null;
    },
    clearUpdatedKeys: (state) => {
      state.updatedFieldKeys = [];
    },
    updateFormField: (state, action) => {
      const { field, value } = action.payload;
      if (field in state.formData) {
        state.formData[field] = value;
        state.updatedFieldKeys = state.updatedFieldKeys.filter((key) => key !== field);
        state.saveStatus = 'idle';
        state.saveError = null;
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state, action) => {
        state.isLoading = true;
        state.error = null;
        state.updatedFieldKeys = [];
        state.chatHistory.push({
          role: 'user',
          content: action.meta.arg.message,
          timestamp: new Date().toISOString(),
        });
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.isLoading = false;
        const data = action.payload;

        state.chatHistory.push({
          role: 'assistant',
          content: data.reply,
          timestamp: new Date().toISOString(),
          toolUsed: data.tool_used,
          confidence: data.confidence,
          activityLog: data.activity_log,
        });

        if (data.updated_fields) {
          const changedKeys = [];
          Object.entries(data.updated_fields).forEach(([key, value]) => {
            if (value !== null && value !== undefined && key in state.formData) {
              if (state.formData[key] !== value) {
                changedKeys.push(key);
              }
              state.formData[key] = value;
            }
          });
          state.updatedFieldKeys = changedKeys;
        }

        if (data.interaction_id) {
          state.interactionId = data.interaction_id;
        }
        state.lastToolUsed = data.tool_used || null;
        state.confidence = data.confidence || null;
        state.activityLog = data.activity_log || [];
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload || 'An error occurred';
        state.chatHistory.push({
          role: 'assistant',
          content: `Error: ${action.payload || 'Failed to process your message. Please try again.'}`,
          timestamp: new Date().toISOString(),
          isError: true,
        });
      })
      .addCase(saveStructuredInteraction.pending, (state) => {
        state.saveStatus = 'saving';
        state.saveError = null;
      })
      .addCase(saveStructuredInteraction.fulfilled, (state, action) => {
        const data = action.payload;
        state.saveStatus = 'saved';
        state.saveError = null;
        state.interactionId = data.id || state.interactionId;
        const changedKeys = [];

        Object.entries(data).forEach(([key, value]) => {
          if (key in state.formData && value !== null && value !== undefined) {
            if (state.formData[key] !== value) {
              changedKeys.push(key);
            }
            state.formData[key] = value;
          }
        });

        state.updatedFieldKeys = changedKeys;
        state.activityLog = [
          data.id ? `Saved structured interaction #${data.id}` : 'Saved structured interaction',
        ];
        state.lastToolUsed = 'manual_form';
        state.confidence = null;
      })
      .addCase(saveStructuredInteraction.rejected, (state, action) => {
        state.saveStatus = 'error';
        state.saveError = action.payload || 'Failed to save interaction';
      });
  },
});

export const { resetForm, clearUpdatedKeys, updateFormField } = crmSlice.actions;
export default crmSlice.reducer;
