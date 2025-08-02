import { NextResponse } from "next/server"
import { getAppState } from "@/lib/store"

export async function GET(request: Request) {
  try {
    const url = new URL(request.url)
    const forgeId = url.searchParams.get('forgeId')

    if (!forgeId) {
      return NextResponse.json({ error: "forgeId parameter is required" }, { status: 400 })
    }

    const state = await getAppState(forgeId)
    return NextResponse.json(state)
  } catch (error) {
    console.error("Error getting state:", error)
    return NextResponse.json({ error: "Failed to get state" }, { status: 500 })
  }
}
