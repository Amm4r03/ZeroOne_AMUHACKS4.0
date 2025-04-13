import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
import { prisma } from "@/lib/db";

export async function POST(
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

    // First, check if this flashcard belongs to the user
    const flashcard = await prisma.flashcard.findUnique({
      where: {
        id: params.id,
      },
      include: {
        set: true,
      },
    });

    if (!flashcard) {
      return NextResponse.json(
        { error: "Flashcard not found" },
        { status: 404 }
      );
    }

    if (flashcard.set.userId !== userId) {
      return NextResponse.json(
        { error: "Not authorized to update this flashcard" },
        { status: 403 }
      );
    }

    // Toggle the isLearned status
    const updatedFlashcard = await prisma.flashcard.update({
      where: {
        id: params.id,
      },
      data: {
        isLearned: !flashcard.isLearned,
      },
    });

    return NextResponse.json(updatedFlashcard);
  } catch (error) {
    console.error("Error toggling flashcard learned status:", error);
    return NextResponse.json(
      { error: "Failed to update flashcard" },
      { status: 500 }
    );
  }
}