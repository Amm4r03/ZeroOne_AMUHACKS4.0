import { NextResponse } from "next/server";

import { auth } from "@clerk/nextjs/server";

import { prisma } from "@/lib/db";

export const dynamic = 'force-dynamic'; // Force dynamic rendering

export async function GET(req: Request) {
  try {
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const url = new URL(req.url);
    const subtopicName = url.searchParams.get("name");

    if (!subtopicName) {
      return NextResponse.json(
        { error: "Subtopic name is required" },
        { status: 400 }
      );
    }

    // Check if we have cached data in the SubtopicDetail table
    const cachedDetail = await prisma.subtopicDetail.findUnique({
      where: {
        subtopicName: subtopicName,
      },
    });

    if (cachedDetail) {
      return NextResponse.json({ details: cachedDetail.details });
    }

    // If no cached data, fetch from external API
    const response = await fetch(process.env.DATA_API!, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ topic: subtopicName }),
    });

    if (!response.ok) {
      throw new Error(`API call failed with status: ${response.status}`);
    }

    const data = await response.json();
    const fetchedDetails = data[0]?.answer; // Assuming the API returns an array with the answer

    if (!fetchedDetails) {
      console.error("API response did not contain expected data:", data);
      throw new Error("Invalid response structure from external API");
    }

    // Store the fetched data in the SubtopicDetail table
    // Use create instead of updateMany/findFirst
    await prisma.subtopicDetail.create({
      data: {
        subtopicName: subtopicName,
        details: fetchedDetails,
      },
    });

    return NextResponse.json({ details: fetchedDetails });
  } catch (error) {
    console.error("Error fetching subtopic details:", error);
    return NextResponse.json(
      { error: "Failed to fetch subtopic details" },
      { status: 500 }
    );
  }
}
