import { MongoClient, Db } from 'mongodb'

export interface Role {
  name: string
  title: string
  id: string
}

export interface ChatMessage {
  id: string
  author: 'user' | 'ai'
  content: string
  timestamp: string
}

export interface RoleChat {
  roleId: string
  messages: ChatMessage[]
  lastBriefingId: string | null // Which briefing this chat is attached to
}

interface Contribution {
  role: string
  text: string
  id: string
  timestamp: string
  authorId: string
  authorName: string
  authorTitle: string
}

interface Synthesis {
  id: string
  content: string
  timestamp: string
  sourceContributions: string[]
}

interface TodoItem {
  roleId: string
  briefing: string
}

interface AppState {
  roles: Role[]
  contributions: Contribution[]
  syntheses: Synthesis[]
  todos: Record<string, TodoItem[]>
  roleChats: RoleChat[]
  goal: string
}

// MongoDB document interface
interface AppStateDocument extends AppState {
  _id: string
}

// MongoDB connection
let client: MongoClient | null = null
let db: Db | null = null

async function connectToMongo(): Promise<Db> {
  if (db) return db

  if (!process.env.MONGO_URI) {
    throw new Error('MONGO_URI environment variable is not set')
  }

  client = new MongoClient(process.env.MONGO_URI)
  await client.connect()
  db = client.db('forge-test')
  return db
}

const getInitialState = (): AppState => ({
  roles: [
    { name: "Konrad", title: "Product Lead", id: "1" },
    { name: "Eike", title: "General Consultant", id: "2" },
  ],
  contributions: [],
  syntheses: [],
  todos: {},
  roleChats: [],
  goal: "Create MVP scope for new product idea",
})

// MongoDB operations
async function readState(forgeId: string): Promise<AppState> {
  try {
    const database = await connectToMongo()
    const collection = database.collection<AppStateDocument>('forge-test1')

    const doc = await collection.findOne({ _id: `forge-${forgeId}` })
    if (doc) {
      const { _id, ...state } = doc
      return state
    }

    // If no document exists, create initial state
    const initialState = getInitialState()
    const docToInsert: AppStateDocument = { _id: `forge-${forgeId}`, ...initialState }
    await collection.insertOne(docToInsert as any)
    return initialState
  } catch (error) {
    console.error('Error reading state from MongoDB, returning initial state:', error)
    return getInitialState()
  }
}

async function writeState(forgeId: string, state: AppState): Promise<void> {
  try {
    const database = await connectToMongo()
    const collection = database.collection<AppStateDocument>('forge-test1')

    const docToWrite: AppStateDocument = { _id: `forge-${forgeId}`, ...state }
    await collection.replaceOne(
      { _id: `forge-${forgeId}` },
      docToWrite as any,
      { upsert: true }
    )
  } catch (error) {
    console.error('Error writing state to MongoDB:', error)
  }
}

export async function getAppState(forgeId: string): Promise<AppState> {
  return await readState(forgeId)
}

export async function addContribution(forgeId: string, contribution: { authorId: string, text: string }): Promise<AppState> {
  const appState = await readState(forgeId)
  const author = appState.roles.find(r => r.id === contribution.authorId)
  if (!author) {
    throw new Error("Role not found")
  }

  const newContribution: Contribution = {
    id: Date.now().toString(),
    timestamp: new Date().toISOString(),
    authorId: contribution.authorId,
    authorName: author.name,
    authorTitle: author.title,
    text: contribution.text,
    role: `${author.name} - ${author.title}`,
  }

  appState.contributions.push(newContribution)
  await writeState(forgeId, appState)
  return appState
}

export async function addSynthesis(forgeId: string, synthesis: Synthesis): Promise<AppState> {
  const appState = await readState(forgeId)
  appState.syntheses.push(synthesis)
  await writeState(forgeId, appState)
  return appState
}

export async function addTodos(forgeId: string, synthesisId: string, briefings: TodoItem[]): Promise<AppState> {
  const appState = await readState(forgeId)
  if (!appState.todos) {
    appState.todos = {}
  }
  appState.todos[synthesisId] = briefings
  await writeState(forgeId, appState)
  return appState
}

export async function updateRoles(forgeId: string, roles: Role[]): Promise<AppState> {
  const appState = await readState(forgeId)
  appState.roles = roles
  await writeState(forgeId, appState)
  return appState
}

export async function updateGoal(forgeId: string, goal: string): Promise<AppState> {
  const appState = await readState(forgeId)
  appState.goal = goal
  await writeState(forgeId, appState)
  return appState
}

export async function resetAppState(forgeId: string): Promise<AppState> {
  const initialState = getInitialState()
  await writeState(forgeId, initialState)
  return initialState
}

export async function addChatMessage(
  forgeId: string,
  roleId: string,
  message: string,
  author: 'user' | 'ai',
  briefingId?: string
): Promise<{ appState: AppState; roleChat: RoleChat }> {
  const appState = await readState(forgeId)

  // Find or create role chat
  let roleChat = appState.roleChats.find(rc => rc.roleId === roleId)
  if (!roleChat) {
    roleChat = {
      roleId,
      messages: [],
      lastBriefingId: briefingId || null
    }
    appState.roleChats.push(roleChat)
  }

  // Add new message
  const newMessage: ChatMessage = {
    id: Date.now().toString(),
    author,
    content: message,
    timestamp: new Date().toISOString()
  }

  roleChat.messages.push(newMessage)

  // Update briefing ID if provided
  if (briefingId) {
    roleChat.lastBriefingId = briefingId
  }

  await writeState(forgeId, appState)
  return { appState, roleChat }
}

export async function getRoleChat(forgeId: string, roleId: string): Promise<RoleChat | null> {
  const appState = await readState(forgeId)
  return appState.roleChats.find(rc => rc.roleId === roleId) || null
}

export async function clearRoleChat(forgeId: string, roleId: string): Promise<AppState> {
  const appState = await readState(forgeId)
  const chatIndex = appState.roleChats.findIndex(rc => rc.roleId === roleId)
  if (chatIndex >= 0) {
    appState.roleChats.splice(chatIndex, 1)
  }
  await writeState(forgeId, appState)
  return appState
}