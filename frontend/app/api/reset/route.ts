import { NextResponse } from "next/server"
import { resetAppState } from "@/lib/store"

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { forgeId } = body

    if (!forgeId) {
      return NextResponse.json({ error: "forgeId is required" }, { status: 400 })
    }

    const state = await resetAppState(forgeId)
    return NextResponse.json({
      message: "Application state reset successfully",
      state,
    })
  } catch (error) {
    console.error("Error resetting state:", error)
    return NextResponse.json({ error: "Failed to reset state" }, { status: 500 })
  }
}
