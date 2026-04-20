# AIGirl Roxy - Frontend

A modern, interactive AI companion platform built with React, TypeScript, and Vite. This frontend application provides a complete user experience for creating custom AI characters and engaging in real-time conversations.

## Features

- **Authentication System** - Firebase-based authentication with email/password
- **9-Step Character Wizard** - Comprehensive character creation with 40+ customization options
- **Real-time Chat Interface** - Beautiful messaging UI with typing indicators and suggestions
- **Character Management** - View, edit, and delete AI companions
- **User Profile** - Account settings and subscription management
- **Responsive Design** - Mobile-first approach with adaptive layouts
- **Type-Safe** - Full TypeScript coverage with strict mode

## Tech Stack

- **Framework**: React 19
- **Language**: TypeScript 5
- **Build Tool**: Vite 7
- **Routing**: React Router v7
- **State Management**: React Context API + TanStack Query v5
- **Styling**: Tailwind CSS v3
- **Forms**: React Hook Form + Zod
- **API Client**: Axios
- **Authentication**: Firebase Auth
- **Date Formatting**: date-fns
- **Icons**: Lucide React

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── auth/              # Authentication components
│   │   ├── character/         # Character wizard components
│   │   ├── chat/              # Chat interface components
│   │   ├── common/            # Reusable UI components
│   │   └── layout/            # Layout components
│   ├── contexts/              # React Context providers
│   │   ├── AuthContext.tsx
│   │   ├── ChatContext.tsx
│   │   └── CharacterWizardContext.tsx
│   ├── pages/                 # Page components
│   │   ├── LandingPage.tsx
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── ChatPage.tsx
│   │   ├── CreateCharacterPage.tsx
│   │   ├── MyCharactersPage.tsx
│   │   └── ProfilePage.tsx
│   ├── services/              # API and service layer
│   │   ├── api.ts
│   │   └── authService.ts
│   ├── types/                 # TypeScript type definitions
│   │   ├── index.ts
│   │   ├── character.ts
│   │   └── chat.ts
│   ├── utils/                 # Utility functions
│   ├── App.tsx                # Main application component
│   └── main.tsx               # Application entry point
├── public/                    # Static assets
├── .env.example               # Environment variable template
└── package.json
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Firebase project with Authentication enabled
- Backend API running (see backend README)

### Installation

1. **Clone the repository**
   ```bash
   cd aigirl/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your Firebase credentials:
   ```env
   VITE_FIREBASE_API_KEY=your_api_key
   VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
   VITE_FIREBASE_PROJECT_ID=your_project_id
   VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
   VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
   VITE_FIREBASE_APP_ID=your_app_id
   VITE_API_BASE_URL=http://localhost:8999/api
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```

   Application will be available at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

Build output will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Key Features Explained

### Character Creation Wizard

The 9-step wizard allows users to create highly customized AI companions:

1. **Style** - Choose between Realistic or Anime style
2. **Template** - Select a base character template
3. **Hair** - Customize hair style and color
4. **Face** - Choose eye and lip colors
5. **Personality** - Pick traits, relationship type, profession, hobbies, and backstory
6. **Voice** - Select voice profile
7. **Background & Boundaries** - Set content boundaries
8. **Scene** - Choose starting scene
9. **Confirm** - Review and create

Features:
- **Auto-save**: Wizard state persists in localStorage
- **Validation**: Each step validates before allowing progression
- **Randomization**: One-click randomize all or per-step
- **Preview**: Character summary before creation

### Chat Interface

Real-time chat features:

- **Message History**: Loads previous conversations from API
- **Typing Indicators**: Shows when AI is generating response
- **Suggestion Chips**: Quick conversation starters
- **Character Selector**: Sidebar to switch between characters
- **Mobile Responsive**: Slide-in sidebar on mobile devices
- **Auto-scroll**: Messages automatically scroll to bottom
- **Error Handling**: User-friendly error messages

### State Management

Three main contexts manage application state:

- **AuthContext**: User authentication, login/logout, session management
- **ChatContext**: Messages, character selection, chat sessions
- **CharacterWizardContext**: Wizard navigation, validation, data persistence

## API Integration

The frontend communicates with the backend via RESTful API:

**Base URL**: `VITE_API_BASE_URL` (default: `http://localhost:8999/api`)

**Authentication**: JWT tokens via Firebase, automatically injected in request headers

### Key Endpoints

- `POST /auth/register` - User registration
- `GET /auth/me` - Get current user
- `POST /characters` - Create character
- `GET /characters` - List user's characters
- `GET /characters/:id` - Get character details
- `DELETE /characters/:id` - Delete character
- `POST /chat/send` - Send message and get AI response
- `GET /chat/sessions` - Get chat history

## Development Guidelines

### Component Patterns

**Common UI Components** (Button, Input, Card):
```typescript
import { Button } from '@/components/common';

<Button variant="primary" loading={isLoading}>
  Submit
</Button>
```

**Using Context**:
```typescript
import { useAuth } from '@/contexts/AuthContext';

const { user, login, logout } = useAuth();
```

**Form Validation**:
```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  email: z.string().email(),
});

const { register, handleSubmit } = useForm({
  resolver: zodResolver(schema),
});
```

### Styling with Tailwind

**Glass Morphism**:
```typescript
<div className="glass-effect">Content</div>
```

**Gradient Text**:
```typescript
<span className="gradient-text">AIGirl</span>
```

**Primary Button**:
```typescript
<button className="btn-primary">Click Me</button>
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_FIREBASE_API_KEY` | Firebase API key | Required |
| `VITE_FIREBASE_AUTH_DOMAIN` | Firebase auth domain | Required |
| `VITE_FIREBASE_PROJECT_ID` | Firebase project ID | Required |
| `VITE_FIREBASE_STORAGE_BUCKET` | Firebase storage bucket | Required |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | Firebase sender ID | Required |
| `VITE_FIREBASE_APP_ID` | Firebase app ID | Required |
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8999/api` |

## Build Output

Production build statistics:
- **HTML**: ~0.46 KB (gzipped: 0.29 KB)
- **CSS**: ~28.71 KB (gzipped: 5.25 KB)
- **JavaScript**: ~565 KB (gzipped: 174.63 KB)

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari 14+, Chrome Mobile)

## Troubleshooting

**Build fails with TypeScript errors**:
- Ensure all imports use `type` keyword for type-only imports
- Check `verbatimModuleSyntax` compatibility

**Firebase authentication not working**:
- Verify `.env` file has correct Firebase credentials
- Check Firebase console for enabled authentication methods

**API requests failing**:
- Confirm backend server is running
- Verify `VITE_API_BASE_URL` points to correct backend URL
- Check browser console for CORS errors

## License

MIT
