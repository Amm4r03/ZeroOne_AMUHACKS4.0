import { NextResponse } from "next/server";

import { auth } from "@clerk/nextjs/server";
import { z } from "zod";

import { prisma } from "@/lib/db";

const quizSchema = z.object({
  topic: z.string().min(1, "Topic is required"),
  difficulty: z.enum(["beginner", "intermediate", "advanced"]),
  questionCount: z.string().transform((val) => parseInt(val, 10)),
  questionType: z.enum(["multiple-choice", "true-false", "mixed"]),
});

type QuizQuestion = {
  question: string;
  options: string[];
  answer: string;
};

async function fetchQuizFromExternalAPI(
  data: z.infer<typeof quizSchema>
): Promise<QuizQuestion[]> {
  const res = await fetch(process.env.QUIZ_API!, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  const resData = await res.json();
  return resData;
}

export async function POST(req: Request) {
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
    const validationResult = quizSchema.safeParse(body);

    if (!validationResult.success) {
      return NextResponse.json(
        {
          error: "Validation error",
          details: validationResult.error.issues,
        },
        { status: 400 }
      );
    }

    const data = validationResult.data;
    const quizQuestions = await fetchQuizFromExternalAPI(data);

    const quiz = await prisma.quiz.create({
      data: {
        userId: userId,
        topic: data.topic,
      },
    });

    await prisma.quizItem.createMany({
      data: quizQuestions.map((item) => ({
        quizId: quiz.id,
        question: item.question,
        options: item.options,
        answer: item.answer,
      })),
    });

    return NextResponse.json({ id: quiz.id });
  } catch (error) {
    console.error("Error generating quiz:", error);
    return NextResponse.json(
      { error: "Failed to generate quiz" },
      { status: 500 }
    );
  }
}
