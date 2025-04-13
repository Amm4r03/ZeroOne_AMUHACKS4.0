import { create } from 'zustand';

// Matches backend JobStatus Enum + idle/cancelled
type JobStatus = 'idle' | 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';

interface AiTutorState {
  jobId: string | null;
  status: JobStatus;
  progress: number;
  topic: string | null;
  videoUrl: string | null;
  errorMessage: string | null;
  setJobDetails: (details: { jobId: string; status: JobStatus; progress: number; topic: string }) => void;
  updateJobStatus: (details: { status: JobStatus; progress: number; videoUrl?: string; errorMessage?: string }) => void;
  cancelJob: () => void;
  resetJob: () => void;
}

export const useAiTutorStore = create<AiTutorState>((set) => ({
  // Initial state
  jobId: null,
  status: 'idle',
  progress: 0,
  topic: null,
  videoUrl: null,
  errorMessage: null,

  // Action to set initial job details when generation starts
  setJobDetails: ({ jobId, status, progress, topic }) => set({
    jobId,
    status,
    progress,
    topic,
    videoUrl: null, // Ensure videoUrl is reset
    errorMessage: null, // Ensure error message is reset
  }),

  // Action to update status during polling or on completion/failure
  updateJobStatus: ({ status, progress, videoUrl, errorMessage }) => set((state) => {
    // Only update if the job ID matches (or if there's no current job)
    // This prevents updates from stale polling intervals if a new job started quickly
    if (!state.jobId) return {}; // Don't update if no job is active

    const newState: Partial<AiTutorState> = { status, progress };
    if (videoUrl !== undefined) newState.videoUrl = videoUrl;
    if (errorMessage !== undefined) newState.errorMessage = errorMessage;

    // If job is completed or failed, clear the topic? Or keep it for display? Let's keep it for now.
    // if (status === 'completed' || status === 'failed') {
    //   newState.topic = null; // Optional: clear topic when job ends
    // }

    return newState;
  }),

  // Action to handle cancellation, now calls backend API first
  cancelJob: async () => {
    const currentJobId = useAiTutorStore.getState().jobId;
    if (!currentJobId) {
      console.log('No active job to cancel.');
      return; // No job to cancel
    }

    console.log(`Attempting to cancel job ${currentJobId} via API...`);
    try {
      const response = await fetch(`/api/ai-tutor/cancel/${currentJobId}`);
      if (!response.ok) {
        // Log error but still proceed with frontend cancellation state update
        const errorData = await response.text();
        console.error(`API call to cancel job ${currentJobId} failed (${response.status}): ${errorData}`);
        // Optionally set a specific error message in the store here?
        // For now, we'll just log and proceed to set state to cancelled.
      } else {
        console.log(`Backend cancellation request for job ${currentJobId} successful.`);
      }
    } catch (error) {
      // Log error but still proceed with frontend cancellation state update
      console.error(`Failed to send cancellation request for job ${currentJobId}:`, error);
      // Optionally set a specific error message in the store here?
    }

    // Update the store state regardless of API call success/failure
    // to ensure the UI reflects the cancellation attempt.
    set({
      status: 'cancelled',
      jobId: null, // Clear job ID after cancellation attempt
      progress: 0,
      errorMessage: 'Generation cancelled by user.', // Keep this message for UI
    });
  },

  // Action to reset the store, e.g., when starting a new generation or navigating away explicitly
  resetJob: () => set({
    jobId: null,
    status: 'idle',
    progress: 0,
    topic: null,
    videoUrl: null,
    errorMessage: null,
  }),
}));
