import { NextResponse } from "next/server";

import { auth } from "@clerk/nextjs/server";

import { prisma } from "@/lib/db";

export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const body = await req.json();
    const { topicName, subtopicName, isCompleted } = body;

    const roadmap = await prisma.roadmap.findUnique({
      where: { id: (await params).id },
      include: { RoadmapItem: true },
    });

    if (!roadmap) {
      return NextResponse.json({ error: "Roadmap not found" }, { status: 404 });
    }

    if (roadmap.userId !== userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 403 });
    }

    const roadmapItem = roadmap.RoadmapItem.find(
      (item) => item.name === topicName
    );

    if (!roadmapItem) {
      return NextResponse.json(
        { error: "Topic not found in roadmap" },
        { status: 404 }
      );
    }

    const updatedCompletedSubtopics = isCompleted
      ? [...roadmapItem.completedSubtopics, subtopicName]
      : roadmapItem.completedSubtopics.filter(
          (topic) => topic !== subtopicName
        );

    await prisma.roadmapItem.update({
      where: { id: roadmapItem.id },
      data: { completedSubtopics: updatedCompletedSubtopics },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error updating subtopic progress:", error);
    return NextResponse.json(
      { error: "Failed to update progress" },
      { status: 500 }
    );
  }
}
