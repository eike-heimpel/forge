import { NextResponse } from "next/server"
import { addContribution } from "@/lib/store"

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { forgeId, authorId, text } = body

    if (!forgeId) {
      return NextResponse.json({ error: "forgeId is required" }, { status: 400 })
    }

    if (!authorId || !text) {
      return NextResponse.json({ error: "Author ID and text are required" }, { status: 400 })
    }

    const state = await addContribution(forgeId, { authorId, text })
    return NextResponse.json({ state })
  } catch (error) {
    console.error("Error adding contribution:", error)
    return NextResponse.json({ error: "Failed to add contribution" }, { status: 500 })
  }
}

