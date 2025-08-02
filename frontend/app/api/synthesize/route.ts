import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const { forgeId } = await request.json()

    if (!forgeId) {
      return NextResponse.json({ error: "forgeId is required" }, { status: 400 })
    }

    // Call FastAPI service
    const response = await fetch(`${process.env.FORGE_AI_SERVICE_URL}/api/synthesize`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${process.env.FORGE_AI_API_KEY}`
      },
      body: JSON.stringify({
        forge_id: forgeId
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: "Unknown error" }))
      return NextResponse.json(
        { error: "FastAPI service error", details: errorData },
        { status: response.status }
      )
    }

    const data = await response.json()

    return NextResponse.json({
      success: true,
      synthesisId: data.synthesis_id,
      message: data.message
    })

  } catch (error) {
    console.error("Synthesis proxy error:", error)
    return NextResponse.json(
      {
        error: "Failed to call synthesis service",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    )
  }
}