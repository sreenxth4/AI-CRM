import { configureStore } from '@reduxjs/toolkit';
import crmReducer from './crmSlice';

export const store = configureStore({
  reducer: {
    crm: crmReducer,
  },
});
