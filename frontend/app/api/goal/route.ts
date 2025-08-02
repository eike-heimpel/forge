import { NextResponse } from "next/server"
import { updateGoal } from "@/lib/store"

export async function PUT(request: Request) {
  try {
    const body = await request.json()
    const { forgeId, goal } = body

    if (!forgeId) {
      return NextResponse.json({ error: "forgeId is required" }, { status: 400 })
    }

    if (!goal) {
      return NextResponse.json({ error: "Goal is required" }, { status: 400 })
    }

    const state = await updateGoal(forgeId, goal)
    return NextResponse.json(state)
  } catch (error) {
    console.error("Error updating goal:", error)
    return NextResponse.json({ error: "Failed to update goal" }, { status: 500 })
  }
}
