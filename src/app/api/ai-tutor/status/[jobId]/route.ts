import { NextRequest, NextResponse } from 'next/server'; // Import NextRequest

const AITUTOR_API_BASE_URL = process.env.AITUTOR_API_BASE_URL;
if (!AITUTOR_API_BASE_URL) {
  console.error("AITUTOR_API_BASE_URL environment variable is not set.");
  throw new Error("AITUTOR_API_BASE_URL environment variable is not set.");
}

const EXTERNAL_API_BASE_URL = `${AITUTOR_API_BASE_URL}jobs/`;

// Define the expected shape of the route parameters
interface RouteParams {
  jobId: string;
}

// Workaround: Extract jobId from URL path instead of using params object
export async function GET(
  request: NextRequest // Only need request
) {
  // Extract jobId from the URL path
  const url = new URL(request.url);
  const pathSegments = url.pathname.split('/');
  const jobId = pathSegments[pathSegments.length - 1];


  if (!jobId || jobId === '[jobId]') { // Add check for placeholder during build/dev
    return NextResponse.json({ error: 'Missing or invalid job ID in URL path' }, { status: 400 });
  }

  const externalUrl = `${EXTERNAL_API_BASE_URL}${jobId}`;
  console.log(`Fetching job status from: ${externalUrl}`);

  try {
    const response = await fetch(externalUrl, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        // Add any necessary authentication headers here if required
      },
      signal: AbortSignal.timeout(60000), // Add 60-second timeout
    });

    if (!response.ok) {
      // Handle cases where the job might not be found (404) or other errors
      const errorData = await response.text();
       if (response.status === 404) {
         console.warn(`Job status check: Job ${jobId} not found.`);
         return NextResponse.json({ error: `Job ${jobId} not found` }, { status: 404 });
       }
      console.error(`External API Error fetching job status ${jobId}:`, response.status, errorData);
      return NextResponse.json({ error: `External API failed with status ${response.status}: ${errorData}` }, { status: response.status });
    }

    const data = await response.json();
    console.log(`Job ${jobId} status response:`, data);

    // Return the status data from the external API
    return NextResponse.json(data);

  } catch (error) {
    console.error(`Error fetching status for job ${jobId}:`, error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
