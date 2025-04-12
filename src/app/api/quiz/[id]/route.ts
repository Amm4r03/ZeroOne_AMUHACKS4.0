import { NextResponse } from "next/server";

import { auth } from "@clerk/nextjs/server";

import { prisma } from "@/lib/db";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const quiz = await prisma.quiz.findUnique({
      where: { id: (await params).id },
      include: {
        QuizItem: true,
      },
    });

    if (!quiz) {
      return NextResponse.json({ error: "Quiz not found" }, { status: 404 });
    }

    if (quiz.userId !== userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 403 });
    }

    const formattedQuiz = {
      topic: quiz.topic,
      questions: quiz.QuizItem.map((item) => ({
        id: item.id,
        question: item.question,
        options: item.options,
        answer: item.answer,
      })),
    };

    return NextResponse.json(formattedQuiz);
  } catch (error) {
    console.error("Error fetching quiz:", error);
    return NextResponse.json(
      { error: "Failed to fetch quiz" },
      { status: 500 }
    );
  }
}
