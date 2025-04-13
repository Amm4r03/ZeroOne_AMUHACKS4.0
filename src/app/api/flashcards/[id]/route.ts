import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
import { prisma } from "@/lib/db";

export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { userId } = await auth();
    if (!userId) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      );
    }

    const flashcardSet = await prisma.flashcardSet.findUnique({
      where: {
        id: params.id,
        userId,
      },
      include: {
        flashcards: true,
      },
    });

    if (!flashcardSet) {
      return NextResponse.json(
        { error: "Flashcard set not found" },
        { status: 404 }
      );
    }

    return NextResponse.json(flashcardSet);
  } catch (error) {
    console.error("Error fetching flashcard set:", error);
    return NextResponse.json(
      { error: "Failed to fetch flashcard set" },
      { status: 500 }
    );
  }
}