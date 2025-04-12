import { auth } from "@clerk/nextjs/server";

import { prisma } from "@/lib/db";

import RoadmapClient from "./roadmap-client";

export default async function RoadmapPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { userId, redirectToSignIn } = await auth();
  const p = await params;
  if (!userId) {
    redirectToSignIn();
  }

  try {
    const roadmap = await prisma.roadmap.findUnique({
      where: { id: p.id },
      include: {
        RoadmapItem: true,
      },
    });

    if (!roadmap) {
      return <div>Roadmap not found</div>;
    }

    if (roadmap.userId !== userId) {
      return <div>Unauthorized</div>;
    }

    const formattedRoadmap = {
      topics: roadmap.RoadmapItem.map((item) => ({
        name: item.name,
        subtopics: item.subtopics.map((subtopic) => ({
          name: subtopic,
          isCompleted: item.completedSubtopics.includes(subtopic),
        })),
        resources: item.resources || [],
        youtube_link: item.youtubeLink || "",
      })),
      completion_time: roadmap.completionTime,
    };

    return <RoadmapClient initialData={formattedRoadmap} id={p.id} />;
  } catch (error) {
    console.error("Error fetching roadmap:", error);
    return <div>Something went wrong</div>;
  }
}
