import Link from "next/link";

import { auth } from "@clerk/nextjs/server";

import { H2 } from "@/components/typography/h2";
import { Para } from "@/components/typography/para";
import { Button } from "@/components/ui/button";
import { features } from "@/lib/constants";
import { prisma } from "@/lib/db";
import { Feature } from "@/lib/types";

export default async function Dashboard() {
  const { userId } = await auth();

  if (!userId) {
    return null;
  }

  const roadmaps = await prisma.roadmap.findMany({
    where: { userId },
    include: {
      RoadmapItem: true,
    },
    orderBy: { createdAt: "desc" },
  });

  const quizzes = await prisma.quiz.findMany({
    where: { userId },
    include: {
      QuizItem: true,
    },
    orderBy: { createdAt: "desc" },
  });
  return (
    <div className="p-10 pl-32">
      <div className="mb-10">
        <H2>Generate Content</H2>
        <Para>
          Create personalized study roadmaps and quizzes to enhance your
          learning.
        </Para>

        <div className="flex flex-wrap gap-10 pt-10">
          {features.map((feature) => (
            <FeatureBox key={feature.id} feature={feature} />
          ))}
        </div>
      </div>

      <div className="mb-10">
        <H2>Your Roadmaps</H2>
        <div className="mt-6 grid gap-6">
          {roadmaps.map((roadmap) => (
            <div
              key={roadmap.id}
              className="flex items-center justify-between rounded-xl bg-white p-6"
            >
              <div>
                <h3 className="mb-2 text-xl font-semibold">
                  {roadmap.syllabus}
                </h3>
                <p className="text-gray-600">
                  {roadmap.subject} - {roadmap.difficulty}
                </p>
                <p className="mt-2 text-sm text-gray-500">
                  Created on {new Date(roadmap.createdAt).toLocaleDateString()}
                </p>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <span className="text-brand-logo-text text-2xl font-bold">
                    {Math.round(
                      (roadmap.RoadmapItem.reduce(
                        (acc, item) =>
                          acc +
                          item.completedSubtopics.length /
                            item.subtopics.length,
                        0
                      ) /
                        roadmap.RoadmapItem.length) *
                        100
                    ) || 0}
                    %
                  </span>
                  <p className="text-sm text-gray-500">Complete</p>
                </div>
                <Link href={`/roadmap/${roadmap.id}`}>
                  <Button variant="outline">Continue</Button>
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <H2>Your Quizzes</H2>
        <div className="mt-6 grid gap-6">
          {quizzes.map((quiz) => (
            <div
              key={quiz.id}
              className="flex items-center justify-between rounded-xl bg-white p-6"
            >
              <div>
                <h3 className="mb-2 text-xl font-semibold">{quiz.topic}</h3>
                <p className="text-gray-600">
                  {quiz.QuizItem.length} questions
                </p>
                <p className="mt-2 text-sm text-gray-500">
                  Created on {new Date(quiz.createdAt).toLocaleDateString()}
                </p>
              </div>
              <div className="flex items-center gap-4">
                <Link href={`/quiz/${quiz.id}`}>
                  <Button variant="outline">
                    {quiz.score !== null ? "Review" : "Start"}
                  </Button>
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function FeatureBox({ feature }: { feature: Feature }) {
  return (
    <div className="flex w-96 flex-col gap-7 rounded-xl bg-white p-5">
      <H2>
        {feature.title.split(" ").map((word, index) => {
          if (index === 0) return `${word} `;
          return (
            <span key={index} className="text-brand-logo-text">
              {word}
            </span>
          );
        })}
      </H2>

      <p className="text-xl">{feature.description}</p>

      <Link href={feature.url}>
        <Button className="rounded-none text-lg">Let's Start</Button>
      </Link>
    </div>
  );
}
