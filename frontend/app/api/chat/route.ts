import { NextResponse } from "next/server"

export async function POST(request: Request) {
    try {
        const { forgeId, roleId, message, isQuestion = false } = await request.json()

        if (!forgeId || !roleId || !message) {
            return NextResponse.json({ error: "forgeId, roleId, and message are required" }, { status: 400 })
        }

        // Debug logging
        console.log("🔍 Chat Debug Info:")
        console.log("- FORGE_AI_SERVICE_URL:", process.env.FORGE_AI_SERVICE_URL)
        console.log("- FORGE_AI_API_KEY:", process.env.FORGE_AI_API_KEY ? "SET" : "NOT SET")
        console.log("- Request body:", { forgeId, roleId, message, isQuestion })

        const fastApiUrl = `${process.env.FORGE_AI_SERVICE_URL}/api/chat`
        console.log("- Full URL:", fastApiUrl)

        // Call FastAPI service
        const response = await fetch(fastApiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${process.env.FORGE_AI_API_KEY}`
            },
            body: JSON.stringify({
                forge_id: forgeId,
                role_id: roleId,
                message: message,
                is_question: isQuestion
            })
        })

        console.log("- FastAPI Response Status:", response.status)
        console.log("- FastAPI Response Headers:", Object.fromEntries(response.headers.entries()))

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: "Unknown error" }))
            console.error("❌ FastAPI Error:", errorData)
            return NextResponse.json(
                { error: "FastAPI service error", details: errorData },
                { status: response.status }
            )
        }

        const data = await response.json()
        console.log("✅ FastAPI Success:", data)

        return NextResponse.json({
            success: true,
            message: data.message,
            aiResponse: data.ai_response,
            isQuestion
        })

    } catch (error) {
        console.error("💥 Chat proxy error:", error)
        return NextResponse.json(
            {
                error: "Failed to call chat service",
                details: error instanceof Error ? error.message : "Unknown error",
            },
            { status: 500 },
        )
    }
} 