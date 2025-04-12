import { NextResponse } from "next/server";

import { auth } from "@clerk/nextjs/server";
import { z } from "zod";

import { prisma } from "@/lib/db";

const scoreSchema = z.object({
  score: z.number().min(0).max(100),
});

export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json(
        {
          error: "Unauthorized",
        },
        { status: 401 }
      );
    }

    const body = await req.json();
    const validationResult = scoreSchema.safeParse(body);

    if (!validationResult.success) {
      return NextResponse.json(
        {
          error: "Validation error",
          details: validationResult.error.issues,
        },
        { status: 400 }
      );
    }

    const quiz = await prisma.quiz.findUnique({
      where: { id: (await params).id },
    });

    if (!quiz) {
      return NextResponse.json({ error: "Quiz not found" }, { status: 404 });
    }

    if (quiz.userId !== userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const updatedQuiz = await prisma.quiz.update({
      where: { id: (await params).id },
      data: { score: validationResult.data.score },
    });

    return NextResponse.json(updatedQuiz);
  } catch (error) {
    console.error("Error updating quiz score:", error);
    return NextResponse.json(
      { error: "Failed to update quiz score" },
      { status: 500 }
    );
  }
}
