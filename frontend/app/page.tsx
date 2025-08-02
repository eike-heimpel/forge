"use client"

import { useState, useEffect, useMemo, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Loader2, Settings, Trash2, ChevronDown, ChevronUp, Eye, Paperclip, Send, Clock, RotateCcw, User, Copy, Check, MessageCircle, Bot } from "lucide-react"
import ReactMarkdown from "react-markdown"

// Interfaces matching lib/store.ts
interface Role {
  id: string
  name: string
  title: string
}

interface Contribution {
  id: string
  authorId: string
  authorName: string
  authorTitle: string
  text: string
  timestamp: string
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

interface ChatMessage {
  id: string
  author: 'user' | 'ai'
  content: string
  timestamp: string
}

interface RoleChat {
  roleId: string
  messages: ChatMessage[]
  lastBriefingId: string | null
}

interface AppState {
  roles: Role[]
  contributions: Contribution[]
  syntheses: Synthesis[]
  todos: Record<string, TodoItem[]>
  goal: string
}

// Generate random forge ID
function generateForgeId(): string {
  return Math.random().toString(36).substring(2, 8).toLowerCase()
}

// Loading component for Suspense fallback
function ForgeLoading() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="flex items-center gap-2">
        <Loader2 className="h-6 w-6 animate-spin" />
        <span>Loading Forge...</span>
      </div>
    </div>
  )
}

// Main Forge component that uses useSearchParams
function ForgeApp() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [forgeId, setForgeId] = useState<string>("")
  const [roles, setRoles] = useState<Role[]>([])
  const [selectedRoleId, setSelectedRoleId] = useState<string>("")
  const [contributions, setContributions] = useState<Contribution[]>([])
  const [syntheses, setSyntheses] = useState<Synthesis[]>([])
  const [todos, setTodos] = useState<Record<string, TodoItem[]>>({})
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [goal, setGoal] = useState<string>("")
  const [showSettings, setShowSettings] = useState<boolean>(false)
  const [isHistoryCollapsed, setIsHistoryCollapsed] = useState<boolean>(true)
  const [isInitialLoading, setIsInitialLoading] = useState<boolean>(true)
  const [isResetting, setIsResetting] = useState<boolean>(false)
  const [copySuccess, setCopySuccess] = useState<boolean>(false)
  const [isAddingContribution, setIsAddingContribution] = useState<boolean>(false)
  const [contributionSuccess, setContributionSuccess] = useState<boolean>(false)

  // New state for overall context
  const [overallContext, setOverallContext] = useState<string>("")
  const [showOverallContext, setShowOverallContext] = useState<boolean>(false)

  // New chat-specific state
  const [roleChats, setRoleChats] = useState<Record<string, RoleChat>>({})
  const [chatMessage, setChatMessage] = useState("")
  const [isSendingMessage, setIsSendingMessage] = useState(false)
  const [showAiResponse, setShowAiResponse] = useState(true)

  // Clear success state when user starts typing again
  useEffect(() => {
    if (chatMessage && contributionSuccess) {
      setContributionSuccess(false)
    }
  }, [chatMessage, contributionSuccess])

  // Handle forge ID from URL parameters
  useEffect(() => {
    const urlForgeId = searchParams.get('id')

    if (!urlForgeId) {
      // No forge ID in URL, generate one and redirect
      const newForgeId = generateForgeId()
      router.push(`/?id=${newForgeId}`)
      return
    }

    // Set forge ID from URL
    setForgeId(urlForgeId)
  }, [searchParams, router])

  // Load initial state from server
  useEffect(() => {
    if (!forgeId) return // Wait for forge ID to be set

    const loadState = async () => {
      try {
        const response = await fetch(`/api/state?forgeId=${forgeId}`)
        if (response.ok) {
          const state: AppState = await response.json()
          setRoles(state.roles)
          setContributions(state.contributions)
          setSyntheses(state.syntheses)
          setTodos(state.todos || {})
          setGoal(state.goal)
        }
      } catch (error) {
        console.error("Error loading state:", error)
      } finally {
        setIsInitialLoading(false)
      }
    }
    loadState()
  }, [forgeId])

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))

    if (diffInMinutes < 1) return "Just now"
    if (diffInMinutes < 60) return `${diffInMinutes} minutes ago`
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)} hours ago`
    return `${Math.floor(diffInMinutes / 1440)} days ago`
  }

  // Replace the old handleAddContribution with new chat functionality
  const handleSendMessage = async (isQuestion: boolean) => {
    if (!chatMessage.trim() || !selectedRoleId || !forgeId || isSendingMessage) return

    setIsSendingMessage(true)

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          forgeId,
          roleId: selectedRoleId,
          message: chatMessage.trim(),
          isQuestion
        })
      })

      if (!response.ok) throw new Error("Failed to send message")

      const data = await response.json()

      // For now, we'll need to refresh the state to get updated contributions
      // In a full implementation, you might want to add polling here too
      try {
        const stateResponse = await fetch(`/api/state?forgeId=${forgeId}`)
        if (stateResponse.ok) {
          const newState = await stateResponse.json()
          setContributions(newState.contributions)
          setRoleChats(prev => ({
            ...prev,
            [selectedRoleId]: newState.roleChats?.find((rc: any) => rc.roleId === selectedRoleId) || { roleId: selectedRoleId, messages: [] }
          }))
        }
      } catch (stateError) {
        console.error("Error refreshing state:", stateError)
      }

      // Clear input
      setChatMessage("")

      // Show success feedback briefly
      setContributionSuccess(true)
      setTimeout(() => setContributionSuccess(false), 1000)

      // If there's an AI response, make sure it's visible
      if (data.aiResponse) {
        setShowAiResponse(true)
      }

    } catch (error) {
      console.error("Error sending message:", error)
    } finally {
      setIsSendingMessage(false)
    }
  }

  const handleSynthesize = async () => {
    if (contributions.length === 0 || !goal.trim() || !forgeId) return
    setIsLoading(true)

    try {
      const response = await fetch("/api/synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ forgeId })
      })

      if (!response.ok) throw new Error("Failed to generate synthesis")
      const data = await response.json()

      // Start polling for the specific synthesis to complete
      const pollForCompletion = async () => {
        let attempts = 0
        const maxAttempts = 20 // Poll for up to 1 minute (3s * 20)
        const targetSynthesisId = data.synthesisId

        const poll = async (): Promise<void> => {
          if (attempts >= maxAttempts) {
            console.log("Polling timeout - synthesis may still be processing")
            setIsLoading(false)
            return
          }

          try {
            const stateResponse = await fetch(`/api/state?forgeId=${forgeId}`)
            if (stateResponse.ok) {
              const newState = await stateResponse.json()

              // Check if our specific synthesis is complete
              const targetSynthesis = newState.syntheses.find((s: Synthesis) => s.id === targetSynthesisId)
              const targetTodos = targetSynthesis ? newState.todos[targetSynthesisId] : null

              if (targetSynthesis && targetTodos && targetTodos.length > 0) {
                // Our synthesis is complete with todos
                setSyntheses(newState.syntheses)
                setTodos(newState.todos)
                setOverallContext(targetSynthesis.content)
                setIsLoading(false)
                return // Stop polling
              }
            }
          } catch (error) {
            console.error("Error polling for synthesis completion:", error)
          }

          attempts++
          setTimeout(poll, 3000) // Poll every 3 seconds
        }

        // Start polling immediately
        poll()
      }

      pollForCompletion()

    } catch (error) {
      console.error("Error synthesizing conversation:", error)
      setIsLoading(false)
    }
  }

  const handleReset = async () => {
    if (!forgeId) return
    setIsResetting(true)
    try {
      const response = await fetch("/api/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ forgeId })
      })

      if (response.ok) {
        const data = await response.json()
        setRoles(data.state.roles)
        setContributions(data.state.contributions)
        setSyntheses(data.state.syntheses)
        setTodos(data.state.todos || {})
        setGoal(data.state.goal)
        setSelectedRoleId("")
        setChatMessage("")
        setIsHistoryCollapsed(true)
        setShowSettings(false)
      }
    } catch (error) {
      console.error("Error resetting application:", error)
    } finally {
      setIsResetting(false)
    }
  }

  const handleRoleChange = (id: string, field: "name" | "title", value: string) => {
    const updatedRoles = roles.map((role) => (role.id === id ? { ...role, [field]: value } : role))
    setRoles(updatedRoles)
  }

  const handleSaveRoles = async () => {
    if (!forgeId) return
    try {
      const response = await fetch("/api/roles", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ forgeId, roles }),
      })
      if (response.ok) {
        const updatedState: AppState = await response.json()
        setRoles(updatedState.roles)
        // Auto-collapse settings after successful save
        setShowSettings(false)
      }
    } catch (error) {
      console.error("Error updating roles:", error)
    }
  }

  const handleAddRole = () => {
    const newId = `role_${Date.now()}`
    setRoles([...roles, { name: "", title: "", id: newId }])
  }

  const handleRemoveRole = (id: string) => {
    setRoles(roles.filter((role) => role.id !== id))
  }

  const handleGoalChange = async (newGoal: string) => {
    setGoal(newGoal)
    if (!forgeId) return
    try {
      await fetch("/api/goal", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ forgeId, goal: newGoal }),
      })
    } catch (error) {
      console.error("Error updating goal:", error)
    }
  }

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href)
      setCopySuccess(true)
      setTimeout(() => setCopySuccess(false), 2000)
    } catch (error) {
      console.error("Failed to copy link:", error)
    }
  }

  const latestSynthesis = useMemo(() => (syntheses.length > 0 ? syntheses[syntheses.length - 1] : null), [syntheses])

  const userBriefing = useMemo(() => {
    if (!selectedRoleId || syntheses.length === 0) return null
    const latestSynthesis = syntheses[syntheses.length - 1]
    const briefing = todos[latestSynthesis.id]?.find(b => b.roleId === selectedRoleId)
    return briefing?.briefing || null
  }, [selectedRoleId, syntheses, todos])

  // Get current role chat
  const currentRoleChat = useMemo(() => {
    return selectedRoleId ? roleChats[selectedRoleId] : null
  }, [selectedRoleId, roleChats])

  // Activity feed combining contributions and syntheses
  const activityFeed = useMemo(() => {
    const activities = [
      ...contributions.map(c => ({
        id: c.id,
        type: 'contribution' as const,
        timestamp: c.timestamp,
        author: c.authorName,
        data: c
      })),
      ...syntheses.map(s => ({
        id: s.id,
        type: 'synthesis' as const,
        timestamp: s.timestamp,
        author: 'AI',
        data: s
      }))
    ]
    return activities.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  }, [contributions, syntheses])

  if (isInitialLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex items-center gap-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Loading Forge session{forgeId ? ` ${forgeId}` : ''}...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-start justify-center p-4">
      <Card className="w-full max-w-4xl shadow-lg">
        <CardHeader className="pb-4">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-3">
              <img
                src="/favicon.png"
                alt="Forge logo"
                className="w-8 h-8 rounded-lg"
              />
              <div>
                <CardTitle className="text-xl font-bold">Forge</CardTitle>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-sm text-gray-600">Goal:</span>
                  <span className="text-sm font-medium">{goal}</span>
                  <Badge variant="secondary" className="bg-green-100 text-green-700 text-xs">
                    Active
                  </Badge>
                </div>
                {forgeId && (
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-sm text-gray-600">Session:</span>
                    <code className="text-sm font-mono bg-gray-100 px-2 py-0.5 rounded text-gray-800">{forgeId}</code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleCopyLink}
                      className="h-6 px-2 text-xs"
                    >
                      {copySuccess ? (
                        <>
                          <Check className="h-3 w-3 mr-1" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="h-3 w-3 mr-1" />
                          Copy Link
                        </>
                      )}
                    </Button>
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="ghost" size="icon" disabled={isResetting}>
                    {isResetting ? <Loader2 className="h-5 w-5 animate-spin" /> : <RotateCcw className="h-5 w-5" />}
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Reset Forge Session</AlertDialogTitle>
                    <AlertDialogDescription>
                      This will permanently delete all contributions and syntheses.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={handleReset} className="bg-red-600 hover:bg-red-700">
                      Reset
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
              <Button variant="ghost" size="icon" onClick={() => setShowSettings(!showSettings)}>
                <Settings className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {showSettings && (
            <div className="space-y-4 p-4 border rounded-lg bg-gray-50">
              <h3 className="text-lg font-semibold">Settings</h3>
              <div className="space-y-2">
                <Label htmlFor="goal-input">Session Goal</Label>
                <Input id="goal-input" value={goal} onChange={(e) => handleGoalChange(e.target.value)} />
              </div>
              <h4 className="font-semibold">Manage Roles</h4>
              {roles.map((role) => (
                <div key={role.id} className="flex items-center gap-2">
                  <Input
                    placeholder="Name"
                    value={role.name}
                    onChange={(e) => handleRoleChange(role.id, "name", e.target.value)}
                  />
                  <Input
                    placeholder="Title"
                    value={role.title}
                    onChange={(e) => handleRoleChange(role.id, "title", e.target.value)}
                  />
                  <Button variant="ghost" size="icon" onClick={() => handleRemoveRole(role.id)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              <div className="flex gap-2">
                <Button onClick={handleAddRole} variant="outline">Add Role</Button>
                <Button onClick={handleSaveRoles}>Save Changes</Button>
              </div>
            </div>
          )}

          {/* User View Selector */}
          <div className="p-4 border rounded-lg bg-yellow-50 border-yellow-200">
            <div className="flex items-center gap-2">
              <User className="h-5 w-5 text-yellow-700" />
              <Label htmlFor="role-selector" className="font-semibold text-yellow-800">Viewing as:</Label>
            </div>
            <Select value={selectedRoleId} onValueChange={setSelectedRoleId}>
              <SelectTrigger id="role-selector">
                <SelectValue placeholder="Select your role to see your view..." />
              </SelectTrigger>
              <SelectContent>
                {roles.map((role) => (
                  <SelectItem key={role.id} value={role.id}>
                    {`${role.name} - ${role.title}`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-yellow-600 mt-2">Select your role to see your personalized summary and to-dos, and to contribute.</p>
          </div>

          {/* Contributor-Specific View */}
          {selectedRoleId && (
            <>
              {/* Overall Context Section - only show if there's content */}
              {overallContext && (
                <Collapsible open={showOverallContext} onOpenChange={setShowOverallContext}>
                  <CollapsibleTrigger asChild>
                    <Button variant="outline" className="w-full justify-between">
                      <span className="flex items-center gap-2">
                        <Eye className="h-4 w-4" />
                        Overall Team Context & Facilitator Notes
                      </span>
                      {showOverallContext ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </Button>
                  </CollapsibleTrigger>
                  <CollapsibleContent className="space-y-2 mt-2">
                    <div className="prose prose-sm max-w-none p-4 border rounded-lg bg-gray-50 border-gray-200">
                      <ReactMarkdown>{overallContext}</ReactMarkdown>
                    </div>
                  </CollapsibleContent>
                </Collapsible>
              )}

              {userBriefing && (
                <div className="space-y-3">
                  <h3 className="font-semibold flex items-center gap-2">
                    <User className="h-4 w-4" />
                    Your Briefing
                  </h3>
                  <div className="prose prose-sm max-w-none p-4 border rounded-lg bg-blue-50 border-blue-200">
                    <ReactMarkdown>{userBriefing}</ReactMarkdown>
                  </div>
                </div>
              )}

              {/* Chat Section */}
              <div className="space-y-4">
                {/* Chat History */}
                {currentRoleChat && currentRoleChat.messages.length > 1 && (
                  <Collapsible open={showAiResponse} onOpenChange={setShowAiResponse}>
                    <CollapsibleTrigger asChild>
                      <Button variant="outline" className="w-full justify-between">
                        <span className="flex items-center gap-2">
                          <MessageCircle className="h-4 w-4" />
                          Questions & Answers ({Math.floor(currentRoleChat.messages.length / 2)} conversations)
                        </span>
                        {showAiResponse ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      </Button>
                    </CollapsibleTrigger>
                    <CollapsibleContent className="space-y-2 mt-2">
                      <div className="border rounded-lg p-4 bg-gray-50 max-h-64 overflow-y-auto space-y-3">
                        {currentRoleChat.messages.map((message) => (
                          <div
                            key={message.id}
                            className={`flex gap-3 ${message.author === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                          >
                            <div className={`p-2 rounded-lg max-w-xs ${message.author === 'user'
                              ? 'bg-blue-600 text-white ml-auto'
                              : 'bg-white border border-gray-200'
                              }`}>
                              <div className="flex items-center gap-1 mb-1">
                                {message.author === 'ai' ? (
                                  <Bot className="h-3 w-3 text-gray-500" />
                                ) : (
                                  <User className="h-3 w-3" />
                                )}
                                <span className="text-xs opacity-75">
                                  {message.author === 'ai' ? 'AI Facilitator' : roles.find(r => r.id === selectedRoleId)?.name}
                                </span>
                              </div>
                              <div className="text-sm">
                                {message.author === 'ai' ? (
                                  <div className="prose prose-xs max-w-none">
                                    <ReactMarkdown>{message.content}</ReactMarkdown>
                                  </div>
                                ) : (
                                  message.content
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CollapsibleContent>
                  </Collapsible>
                )}

                {/* Chat Input */}
                <div className={`space-y-4 p-4 border rounded-lg transition-colors duration-300 ${contributionSuccess ? 'bg-green-50 border-green-200' : 'bg-white'
                  }`}>
                  <Label htmlFor="chat-input" className="flex items-center gap-2">
                    <MessageCircle className="h-4 w-4" />
                    Chat with your facilitator
                  </Label>
                  <Textarea
                    id="chat-input"
                    placeholder="Ask questions, share updates, or request clarification about your briefing..."
                    value={chatMessage}
                    onChange={(e) => setChatMessage(e.target.value)}
                    rows={3}
                    className={contributionSuccess ? "border-green-300 focus:border-green-400" : ""}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                        e.preventDefault()
                        handleSendMessage(false) // Default to "Add Context"
                      }
                    }}
                  />
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-500">
                      {currentRoleChat?.messages.length ?
                        `${Math.floor(currentRoleChat.messages.length / 2)} Q&A conversations` :
                        'Add context or ask your AI facilitator'
                      }
                    </span>
                    <div className="flex gap-2">
                      <Button
                        onClick={() => handleSendMessage(false)}
                        disabled={!chatMessage.trim() || isSendingMessage}
                        variant="outline"
                        size="sm"
                      >
                        {isSendingMessage ? (
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        ) : (
                          <Paperclip className="h-4 w-4 mr-2" />
                        )}
                        Add Context
                      </Button>
                      <Button
                        onClick={() => handleSendMessage(true)}
                        disabled={!chatMessage.trim() || isSendingMessage}
                        className={contributionSuccess ? "bg-green-600 hover:bg-green-700" : ""}
                      >
                        {contributionSuccess ? (
                          <Check className="h-4 w-4 mr-2" />
                        ) : isSendingMessage ? (
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        ) : (
                          <MessageCircle className="h-4 w-4 mr-2" />
                        )}
                        {contributionSuccess ? "Sent!" : isSendingMessage ? "Sending..." : "Ask Question"}
                      </Button>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500">
                    <strong>Add Context:</strong> Share updates or info (no AI response) • <strong>Ask Question:</strong> Get help from your facilitator • <strong>Tip:</strong> Cmd/Ctrl + Enter adds context
                  </p>
                </div>
              </div>
            </>
          )}

          {/* Synthesize Button */}
          <div className="flex flex-col items-center pt-4 space-y-3">
            <Button onClick={handleSynthesize} disabled={isLoading || contributions.length === 0}>
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Running AI Synthesis...</span>
                </div>
              ) : (
                "Run AI Synthesis"
              )}
            </Button>
          </div>

          {/* Activity Feed */}
          {activityFeed.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-gray-600 flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Recent Activity
              </h3>
              <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
                {activityFeed.slice(0, 10).map((activity) => (
                  <Badge
                    key={activity.id}
                    variant={activity.type === 'synthesis' ? 'default' : 'secondary'}
                    className="text-xs flex items-center gap-1 animate-in fade-in-50 duration-300"
                  >
                    {activity.type === 'synthesis' ? (
                      <>
                        <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                        AI Synthesis
                      </>
                    ) : (
                      <>
                        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        {activity.author}
                      </>
                    )}
                    <span className="opacity-70">
                      {formatTimeAgo(activity.timestamp)}
                    </span>
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* History Section */}
          <Collapsible open={!isHistoryCollapsed} onOpenChange={(open) => setIsHistoryCollapsed(!open)}>
            <CollapsibleTrigger asChild>
              <Button variant="link" className="p-0 text-sm">
                {isHistoryCollapsed ? <ChevronDown className="h-4 w-4 mr-1" /> : <ChevronUp className="h-4 w-4 mr-1" />}
                Toggle Full History
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-4 mt-2">
              {contributions.map((c) => (
                <div key={c.id} className="p-3 bg-gray-100 rounded-lg">
                  <p className="text-xs text-gray-500">{c.authorName} at {formatTimeAgo(c.timestamp)}</p>
                  <p className="text-sm">{c.text}</p>
                </div>
              ))}
            </CollapsibleContent>
          </Collapsible>
        </CardContent>
      </Card>
    </div>
  )
}

export default function Forge() {
  return (
    <Suspense fallback={<ForgeLoading />}>
      <ForgeApp />
    </Suspense>
  )
}