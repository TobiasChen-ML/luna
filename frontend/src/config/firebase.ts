import { initializeApp } from 'firebase/app';
import { getAuth, connectAuthEmulator } from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication
export const auth = getAuth(app);
if (import.meta.env.VITE_USE_AUTH_EMULATOR === 'true') {
  connectAuthEmulator(auth, import.meta.env.VITE_AUTH_EMULATOR_URL || 'http://localhost:9099');
}

export default app;
