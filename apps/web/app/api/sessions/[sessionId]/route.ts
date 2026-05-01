import { NextResponse } from "next/server";

import { getSession, startProcessing } from "../../../../lib/api";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ sessionId: string }> },
) {
  const { sessionId } = await params;

  try {
    const session = await getSession(sessionId);
    return NextResponse.json(session);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Session fetch failed";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}

export async function POST(
  _request: Request,
  { params }: { params: Promise<{ sessionId: string }> },
) {
  const { sessionId } = await params;

  try {
    const session = await startProcessing(sessionId);
    return NextResponse.json(session);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Processing start failed";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
