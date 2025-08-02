import { NextResponse } from "next/server"
import { updateRoles } from "@/lib/store"

export async function PUT(request: Request) {
  try {
    const body = await request.json()
    const { forgeId, roles } = body

    if (!forgeId) {
      return NextResponse.json({ error: "forgeId is required" }, { status: 400 })
    }

    if (!roles || !Array.isArray(roles)) {
      return NextResponse.json({ error: "Roles array is required" }, { status: 400 })
    }

    const state = await updateRoles(forgeId, roles)
    return NextResponse.json(state)
  } catch (error) {
    console.error("Error updating roles:", error)
    return NextResponse.json({ error: "Failed to update roles" }, { status: 500 })
  }
}
