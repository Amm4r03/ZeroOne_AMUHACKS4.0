import { NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server'; // Import Clerk auth
import { prisma } from '@/lib/db'; // Import Prisma client (correct name)

const AITUTOR_API_BASE_URL = process.env.AITUTOR_API_BASE_URL;
if (!AITUTOR_API_BASE_URL) {
  // It's better to return an error response than throw, especially in API routes
  console.error("AITUTOR_API_BASE_URL environment variable is not set.");
  // Return an internal server error response or handle appropriately
  // For now, let's log and potentially throw during startup or use a default/fallback
  // Throwing here might crash the server process if not caught higher up
  throw new Error("AITUTOR_API_BASE_URL environment variable is not set.");
}

const EXTERNAL_API_URL = `${AITUTOR_API_BASE_URL}generate_video/`;
const VIDEO_API_URL_BASE = `${AITUTOR_API_BASE_URL}video/`; // Base URL for video playback

export async function POST(request: Request) {
  try {
    // 1. Get User ID from authentication context
    const { userId } = await auth(); // Await the auth() call
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // 2. Parse request body
    const { topic, language, voice } = await request.json();
    if (!topic || !language || !voice) {
      return NextResponse.json({ error: 'Missing required fields: topic, language, voice' }, { status: 400 });
    }

    console.log('Forwarding generation request to external API:', { topic, language, voice });

    const response = await fetch(EXTERNAL_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Add any necessary authentication headers here if required by the external API
      },
      body: JSON.stringify({
        topic: topic,
        language: language, // e.g., "en-US"
        voice: voice,       // e.g., "af_heart"
        cleanup: false,
        skip_content_cache: false,
        no_animation_cache: false,
      }),
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error('External API Error:', response.status, errorData);
      return NextResponse.json({ error: `External API failed with status ${response.status}: ${errorData}` }, { status: response.status });
    }

    const data = await response.json();
    console.log('External API Response:', data);

    // 3. Save video details to the database if job_id exists
    if (data.job_id) {
      try {
        const videoUrl = `${VIDEO_API_URL_BASE}${data.job_id}`;
        await prisma.aiTutorVideo.create({ // Use prisma instead of db
          data: {
            id: data.job_id, // Use job_id as the primary key
            userId: userId,
            topic: topic,
            language: language,
            voice: voice,
            videoUrl: videoUrl,
          },
        });
        console.log(`Saved video details for job ${data.job_id} to database.`);
      } catch (dbError) {
        // Log DB error but still return the original API response to the client
        console.error(`Failed to save video details for job ${data.job_id} to database:`, dbError);
        // Optionally, we could implement a retry mechanism or queue this for later saving
      }
    } else {
       console.warn('External API did not return a job_id. Skipping database save.');
    }

    // 4. Return the original response from the external API
    return NextResponse.json(data);

  } catch (error) {
    console.error('Error in /api/ai-tutor/generate:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
