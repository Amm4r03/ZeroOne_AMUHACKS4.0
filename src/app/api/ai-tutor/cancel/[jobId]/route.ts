import { NextRequest, NextResponse } from 'next/server';

const AITUTOR_API_BASE_URL = process.env.AITUTOR_API_BASE_URL;
if (!AITUTOR_API_BASE_URL) {
  console.error("AITUTOR_API_BASE_URL environment variable is not set.");
  throw new Error("AITUTOR_API_BASE_URL environment variable is not set.");
}

const EXTERNAL_API_CANCEL_URL_BASE = `${AITUTOR_API_BASE_URL}cancel/`;

// Define the expected shape of the route parameters
interface RouteParams {
  jobId: string;
}

// Use NextRequest and explicitly type the context object containing params
export async function GET(
  request: NextRequest, // Use NextRequest
  { params }: { params: RouteParams } // Type the context object
) {
  // Access jobId from the destructured params
  const jobId = params.jobId;

  if (!jobId) {
    return NextResponse.json({ error: 'Missing job ID' }, { status: 400 });
  }

  const externalUrl = `${EXTERNAL_API_CANCEL_URL_BASE}${jobId}`;
  console.log(`Sending cancellation request to: ${externalUrl}`);

  try {
    const response = await fetch(externalUrl, {
      method: 'GET',
      headers: {
      },
    });

    if (!response.ok) {
      // Handle cases where the job might not be found (404) or other errors
      const errorData = await response.text();
       if (response.status === 404) {
         console.warn(`Cancel request: Job ${jobId} not found on external API.`);
         // Still might want to return success to frontend if job is gone? Or error? Let's return error.
         return NextResponse.json({ error: `Job ${jobId} not found for cancellation` }, { status: 404 });
       }
      console.error(`External API Error cancelling job ${jobId}:`, response.status, errorData);
      return NextResponse.json({ error: `External API failed cancellation with status ${response.status}: ${errorData}` }, { status: response.status });
    }

    console.log(`Job ${jobId} cancellation request successful.`);
    return NextResponse.json({ message: `Job ${jobId} cancellation requested successfully.` });

  } catch (error) {
    console.error(`Error sending cancellation for job ${jobId}:`, error);
    return NextResponse.json({ error: 'Internal Server Error during cancellation' }, { status: 500 });
  }
}
