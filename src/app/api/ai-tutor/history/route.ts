import { NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';
import { prisma } from '@/lib/db';

export async function GET() {
  try {
    // 1. Get User ID from authentication context
    const { userId } = await auth();
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // 2. Fetch video history for the user
    const videoHistory = await prisma.aiTutorVideo.findMany({
      where: {
        userId: userId,
      },
      orderBy: {
        createdAt: 'desc', // Show newest videos first
      },
    });

    // 3. Return the history
    return NextResponse.json(videoHistory);

  } catch (error) {
    console.error('Error fetching AI Tutor video history:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
