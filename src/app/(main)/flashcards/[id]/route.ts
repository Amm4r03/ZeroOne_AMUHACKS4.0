import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
import { prisma } from "@/lib/db";

interface Flashcard {
  question: string;
  hint: string;
  answer: string;
}

export async function POST(req: NextRequest) {
  try {
    const { userId } = await auth();
    if (!userId) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      );
    }

    const { topic, difficulty, num_flashcards } = await req.json();

    if (!topic) {
      return NextResponse.json(
        { error: "Topic is required" },
        { status: 400 }
      );
    }

    // Call the external API to generate flashcards
    const response = await fetch("http://localhost:7070/generate_flashcards", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        topic,
        difficulty,
        num_flashcards,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error("External API error:", errorData);
      return NextResponse.json(
        { error: "Failed to generate flashcards" },
        { status: 500 }
      );
    }

    const data = await response.json();
    
    // Create a new flashcard set in the database
    const flashcardSet = await prisma.flashcardSet.create({
      data: {
        userId,
        topic,
        difficulty,
        createdAt: new Date(),
      },
    });

    // Create individual flashcards in the database
    await Promise.all(
      data.flashcards.map((card: Flashcard) =>
        prisma.flashcard.create({
          data: {
            setId: flashcardSet.id,
            question: card.question,
            hint: card.hint,
            answer: card.answer,
            createdAt: new Date(),
          },
        })
      )
    );

    return NextResponse.json({ id: flashcardSet.id });
  } catch (error) {
    console.error("Error generating flashcards:", error);
    return NextResponse.json(
      { error: "Failed to generate flashcards" },
      { status: 500 }
    );
  }
}