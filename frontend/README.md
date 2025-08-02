# 🔨 Forge - v0.1

**Collaborative synthesis and decision-making tool**

Forge transforms team discussions into actionable insights. Team members contribute from their unique role perspectives, and AI creates personalized briefings and action items for each participant.

---

## ✨ Features

### 🎯 **Role-Based Collaboration**
- **Multi-perspective input**: Each team member contributes from their specific role (Product Lead, Consultant, etc.)
- **Personalized briefings**: AI generates custom summaries and action items for each role
- **Context-aware**: AI understands team dynamics and individual responsibilities

### 🤖 **AI-Powered Synthesis**
- **Smart progression**: Chained AI calls with live progress tracking
- **Two-phase process**: Overall synthesis → Individual role briefings
- **Timeout-resistant**: Built for serverless deployment with step-by-step processing

### 🔗 **Session Management**
- **URL-based sessions**: Each forge gets a unique ID (e.g., `/?id=abc123`)
- **Shareable links**: Copy link to invite team members
- **Persistent storage**: MongoDB-backed state that survives server restarts

### 📈 **Real-Time Feedback**
- **Activity feed**: Live timeline of contributions and AI syntheses
- **Progress indicators**: Visual feedback for AI processing steps
- **Optimistic updates**: Instant UI feedback with server sync

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- MongoDB database
- OpenRouter API key

### 1. Clone & Install
```bash
git clone <your-repo>
cd forge-poc
npm install
```

### 2. Environment Setup
Create `.env.local`:
```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/forge-test
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=google/gemini-2.0-flash-exp
```

### 3. Run Development Server
```bash
npm run dev
```

Visit `http://localhost:3000` → Auto-generates forge session → Start collaborating!

---

## 📖 How to Use

### **Creating a Session**
1. Visit the app → Automatically get a unique forge ID
2. Bookmark the URL or copy the session link
3. Share with team members

### **Contributing**
1. Select your role from the dropdown
2. Add your thoughts, context, or questions
3. Click "Add to Forge" → See instant feedback + activity timeline

### **AI Synthesis**
1. Click "Run AI Synthesis" when ready
2. Watch live progress: *"Generating synthesis... (1/4)"*
3. AI creates personalized briefings for each role
4. Review your custom action items and context

### **Settings**
- Modify team roles and titles
- Update session goals
- Reset session (clears all data)

---

## 🏗️ Tech Stack

- **Frontend**: Next.js 15, React 19, TypeScript
- **UI**: Tailwind CSS, shadcn/ui components
- **Database**: MongoDB with connection pooling
- **AI**: OpenRouter API (Gemini 2.0 Flash)
- **Deployment**: Vercel-optimized (serverless functions)

---

## 🌐 Deployment

### Vercel (Recommended)
1. Connect your GitHub repo to Vercel
2. Add environment variables in Vercel dashboard:
   - `MONGO_URI`
   - `OPENROUTER_API_KEY`
   - `OPENROUTER_MODEL` (optional)
3. Deploy!

### MongoDB Setup
- Use MongoDB Atlas (cloud) or your own instance
- Database: `forge-test`
- Collection: `forge-test1`
- No schema setup needed - documents auto-create

---

## 🔧 API Routes

- `GET /api/state?forgeId=xyz` - Load forge session
- `POST /api/contributions` - Add team member contribution
- `POST /api/synthesize` - Run AI synthesis (supports chaining)
- `POST /api/reset` - Reset forge session
- `PUT /api/roles` - Update team roles
- `PUT /api/goal` - Update session goal

---

## 💡 Use Cases

### **Product Planning**
- **Roles**: Product Manager, Engineer, Designer
- **Goal**: "Define Q2 feature priorities"
- **Output**: Role-specific action items and technical considerations

### **Research Synthesis**
- **Roles**: Researcher, Analyst, Stakeholder
- **Goal**: "Synthesize user interview findings"
- **Output**: Personalized insights and next steps per role

### **Decision Making**
- **Roles**: Decision maker, Subject experts, Implementers
- **Goal**: "Choose technical architecture approach"
- **Output**: Context-aware recommendations for each perspective

---

## 🔐 Privacy & Data

- **Session isolation**: Each forge ID is completely separate
- **No authentication**: URL-based access (bookmark to retain access)
- **Data persistence**: All contributions and syntheses stored in MongoDB
- **Reset available**: Clear all session data anytime

---

## 🤝 Contributing

This is a PoC built for exploration and demonstration. Feel free to:
- Fork and experiment
- Suggest improvements
- Report issues
- Extend functionality

---

## 📄 License

MIT License - See LICENSE file for details

---

**Built with ❤️ for better team collaboration**
