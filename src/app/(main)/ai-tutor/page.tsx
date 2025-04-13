'use client';

import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { H1 } from '@/components/typography/h1';
import { H2 } from '@/components/typography/h2';
import { Para } from '@/components/typography/para';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useAiTutorStore } from '@/lib/ai-tutor-store'; // Import the store
import { Loader2, History, AlertCircle } from 'lucide-react'; // Import loader and other icons

interface VideoHistoryItem {
  id: string;
  userId: string;
  topic: string;
  language: string;
  voice: string;
  videoUrl: string;
  createdAt: string; // Dates are usually strings after JSON serialization
}

// Data fetched from https://aitutor-api.duckdns.org/api/v1/languages
const languagesData = {
  languages: [
    {
      language_code: 'en-US',
      language_name: 'American English',
      voices: [
        { id: 'af_heart', name: 'Af Heart' }, { id: 'af_alloy', name: 'Af Alloy' }, { id: 'af_aoede', name: 'Af Aoede' }, { id: 'af_bella', name: 'Af Bella' }, { id: 'af_jessica', name: 'Af Jessica' }, { id: 'af_kore', name: 'Af Kore' }, { id: 'af_nicole', name: 'Af Nicole' }, { id: 'af_nova', name: 'Af Nova' }, { id: 'af_river', name: 'Af River' }, { id: 'af_sarah', name: 'Af Sarah' }, { id: 'af_sky', name: 'Af Sky' }, { id: 'am_adam', name: 'Am Adam' }, { id: 'am_echo', name: 'Am Echo' }, { id: 'am_eric', name: 'Am Eric' }, { id: 'am_fenrir', name: 'Am Fenrir' }, { id: 'am_liam', name: 'Am Liam' }, { id: 'am_michael', name: 'Am Michael' }, { id: 'am_onyx', name: 'Am Onyx' }, { id: 'am_puck', name: 'Am Puck' }, { id: 'am_santa', name: 'Am Santa' },
      ],
    },
    {
      language_code: 'en-GB', language_name: 'British English', voices: [ { id: 'bf_alice', name: 'Bf Alice' }, { id: 'bf_emma', name: 'Bf Emma' }, { id: 'bf_isabella', name: 'Bf Isabella' }, { id: 'bf_lily', name: 'Bf Lily' }, { id: 'bm_daniel', name: 'Bm Daniel' }, { id: 'bm_fable', name: 'Bm Fable' }, { id: 'bm_george', name: 'Bm George' }, { id: 'bm_lewis', name: 'Bm Lewis' }, ],
    },
    { language_code: 'es-ES', language_name: 'Spanish', voices: [ { id: 'ef_dora', name: 'Ef Dora' }, { id: 'em_alex', name: 'Em Alex' }, { id: 'em_santa', name: 'Em Santa' }, ], },
    { language_code: 'fr-FR', language_name: 'French', voices: [{ id: 'ff_siwis', name: 'Ff Siwis' }], },
    { language_code: 'hi-IN', language_name: 'Hindi', voices: [ { id: 'hf_alpha', name: 'Hf Alpha' }, { id: 'hf_beta', name: 'Hf Beta' }, { id: 'hm_omega', name: 'Hm Omega' }, { id: 'hm_psi', name: 'Hm Psi' }, ], },
    { language_code: 'it-IT', language_name: 'Italian', voices: [ { id: 'if_sara', name: 'If Sara' }, { id: 'im_nicola', name: 'Im Nicola' }, ], },
    { language_code: 'ja-JP', language_name: 'Japanese', voices: [ { id: 'jf_alpha', name: 'Jf Alpha' }, { id: 'jf_gongitsune', name: 'Jf Gongitsune' }, { id: 'jf_nezumi', name: 'Jf Nezumi' }, { id: 'jf_tebukuro', name: 'Jf Tebukuro' }, { id: 'jm_kumo', name: 'Jm Kumo' }, ], },
    { language_code: 'pt-BR', language_name: 'Brazilian Portuguese', voices: [ { id: 'pf_dora', name: 'Pf Dora' }, { id: 'pm_alex', name: 'Pm Alex' }, { id: 'pm_santa', name: 'Pm Santa' }, ], },
    { language_code: 'zh-CN', language_name: 'Mandarin Chinese', voices: [ { id: 'zf_xiaobei', name: 'Zf Xiaobei' }, { id: 'zf_xiaoni', name: 'Zf Xiaoni' }, { id: 'zf_xiaoxiao', name: 'Zf Xiaoxiao' }, { id: 'zf_xiaoyi', name: 'Zf Xiaoyi' }, { id: 'zm_yunjian', name: 'Zm Yunjian' }, { id: 'zm_yunxi', name: 'Zm Yunxi' }, { id: 'zm_yunxia', name: 'Zm Yunxia' }, { id: 'zm_yunyang', name: 'Zm Yunyang' }, ], },
  ],
};

const POLLING_INTERVAL = 30000; // Check status every 30 seconds
const VIDEO_API_URL_BASE = 'https://aitutor-api.duckdns.org/api/v1/video/';

export default function AiTutorPage() {
  // Local state for form inputs only
  const [formTopic, setFormTopic] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('');
  const [selectedVoice, setSelectedVoice] = useState<string>('');
  // State for video history
  const [videoHistory, setVideoHistory] = useState<VideoHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState<boolean>(true);
  const [historyError, setHistoryError] = useState<string | null>(null);

  // Get state and actions from the global store
  const {
    jobId,
    status,
    progress,
    topic: jobTopic, // Rename to avoid conflict with formTopic
    videoUrl,
    errorMessage,
    setJobDetails,
    updateJobStatus,
    cancelJob,
    resetJob,
  } = useAiTutorStore();

  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const availableVoices = useMemo(() => {
    if (!selectedLanguage) return [];
    const language = languagesData.languages.find(
      (lang) => lang.language_code === selectedLanguage
    );
    return language ? language.voices : [];
  }, [selectedLanguage]);

  // Reset voice selection when language changes
  useEffect(() => {
    setSelectedVoice('');
  }, [selectedLanguage]);

  // Function to stop polling
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
      console.log('Polling stopped.');
    }
  }, []);

  // Function to check job status - uses store actions
  const checkStatus = useCallback(async (currentJobId: string) => {
    console.log(`>>> ENTERING checkStatus for job: ${currentJobId}`); // Add log here
    console.log(`Checking status for job: ${currentJobId}`);
    try {
      console.log(`>>> Attempting fetch for /api/ai-tutor/status/${currentJobId}`); // Add log here
      const response = await fetch(`/api/ai-tutor/status/${currentJobId}`);
      console.log(`>>> Fetch response received for ${currentJobId}, ok: ${response.ok}, status: ${response.status}`); // Add log here
      if (!response.ok) {
        let errorMsg = `Error checking status: ${response.statusText}`;
        if (response.status === 404) {
           errorMsg = `Job ${currentJobId} not found.`;
           console.error(errorMsg);
        } else {
            try {
                const errorData = await response.text();
                errorMsg = `Error checking status: ${errorData || response.statusText}`;
                console.error(`Error checking status (${response.status}):`, errorData);
            } catch { /* Ignore parsing error */ }
        }
        updateJobStatus({ status: 'failed', progress: progress, errorMessage: errorMsg }); // Update store on error
        stopPolling();
        return;
      }

      const data = await response.json();
      console.log('Status update received raw data:', data); // Log raw data first

      const newStatus = data.status || 'failed';
      const newProgress = data.progress || 0;
      console.log(`Parsed status: ${newStatus}, Parsed progress: ${newProgress}`); // Log parsed values
      let newVideoUrl: string | undefined = undefined;
      let newErrorMessage: string | undefined = undefined;

      if (newStatus === 'completed') {
        console.log('Job completed! Full response data:', data); // Log the full data object
        // Assuming the video URL is constructed like this for now, adjust if data object reveals a specific field
        newVideoUrl = `${VIDEO_API_URL_BASE}${currentJobId}`;
        stopPolling();
      } else if (newStatus === 'failed') {
        console.error('Job failed:', data);
        newErrorMessage = data.error || 'Video generation failed.';
        stopPolling();
      }

      // Update the global store
      console.log('Updating store with:', { status: newStatus, progress: newProgress, videoUrl: newVideoUrl, errorMessage: newErrorMessage }); // Log before updating store
      updateJobStatus({
          status: newStatus,
          progress: newProgress,
          videoUrl: newVideoUrl,
          errorMessage: newErrorMessage
      });

    } catch (error) {
      console.error('Failed to fetch job status:', error);
      // Update store on fetch error
      updateJobStatus({ status: 'failed', progress: progress, errorMessage: 'Failed to connect to status check service.' });
      stopPolling(); // Stop polling on network error
    }
  }, [stopPolling, updateJobStatus, progress]); // Include store actions and progress

  // Function to fetch video history
  const fetchHistory = useCallback(async () => {
    console.log('Fetching video history...');
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const response = await fetch('/api/ai-tutor/history');
      if (!response.ok) {
        throw new Error(`Failed to fetch history: ${response.statusText}`);
      }
      const data: VideoHistoryItem[] = await response.json();
      setVideoHistory(data);
      console.log('Video history fetched:', data);
    } catch (error: any) {
      console.error('Error fetching video history:', error);
      setHistoryError(error.message || 'Could not load video history.');
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  // Fetch history on component mount
  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);


  // Start/stop polling based on global store state
  useEffect(() => {
    console.log(`>>> ENTERING useEffect for polling. JobId: ${jobId}, Status: ${status}`); // Add log here
    if (jobId && (status === 'queued' || status === 'processing')) {
      console.log(`>>> useEffect: Starting polling for JobId: ${jobId}`); // Add log here
      stopPolling(); // Clear existing interval first
      checkStatus(jobId); // Initial check
      pollingIntervalRef.current = setInterval(() => checkStatus(jobId), POLLING_INTERVAL);
      console.log('Polling started from store state.');
    } else {
      stopPolling(); // Stop polling if job is not active
    }
    // Cleanup function
    return () => stopPolling();
  }, [jobId, status, checkStatus, stopPolling]); // Depend on store state

  const handleGenerate = async () => {
    if (!formTopic || !selectedLanguage || !selectedVoice) {
      alert('Please fill in all fields.');
      return;
    }

    resetJob(); // Reset store before starting new job
    stopPolling(); // Ensure any previous polling is stopped

    console.log('Requesting video generation:', { topic: formTopic, selectedLanguage, selectedVoice });

    try {
      const response = await fetch('/api/ai-tutor/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: formTopic,
          language: selectedLanguage,
          voice: selectedVoice,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `API request failed with status ${response.status}`);
      }

      const data = await response.json();
      console.log('Generation request successful:', data);

      if (!data.job_id) {
           throw new Error('Backend did not return a job_id.');
      }

      const initialStatus = data.status || 'queued';
      const initialProgress = data.progress || 0;

      // Set initial details in the global store
      setJobDetails({
          jobId: data.job_id,
          status: initialStatus,
          progress: initialProgress,
          topic: formTopic // Use topic from the form
      });

      // If the job is already completed (e.g., from cache), set the video URL immediately
      if (initialStatus === 'completed') {
          console.log('Job already completed from generate response. Setting video URL.');
          const completedVideoUrl = `${VIDEO_API_URL_BASE}${data.job_id}`;
          updateJobStatus({
              status: 'completed',
              progress: 100, // Assume 100% if completed
              videoUrl: completedVideoUrl,
              errorMessage: undefined
          });
          stopPolling(); // Ensure no polling starts
          fetchHistory(); // Refetch history after successful immediate completion
      }
      // Otherwise, polling will start automatically via useEffect based on store state ('queued' or 'processing')

    } catch (error: any) {
      console.error('Failed to start generation:', error);
      // Update store on error starting job
      updateJobStatus({ status: 'failed', progress: 0, errorMessage: error.message || 'Failed to start generation.' });
    }
  };

  // Use cancelJob from the store, adding confirmation
  const handleCancel = () => {
    if (confirm('Are you sure you want to cancel this video generation?')) {
        stopPolling(); // Stop local polling interval immediately
        cancelJob(); // Update global state
        console.log('Generation cancelled by user.');
    }
  };

   // Use resetJob from the store
   const resetFormAndStore = () => {
        setFormTopic('');
        setSelectedLanguage('');
        setSelectedVoice('');
        stopPolling();
        resetJob(); // Reset global state
    };

  const isGenerating = status === 'queued' || status === 'processing';
  // Show form if idle, cancelled, or failed (allows retry)
  const showForm = status === 'idle' || status === 'cancelled' || status === 'failed';

  // Check if Progress component exists
  const ProgressComponent = Progress || (({ value }: { value: number }) => <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700"><div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${value}%` }}></div></div>);

  return (
    <div className="container mx-auto py-10 pl-28"> {/* Adjusted padding */}
      <H1 className="mb-6">AI Tutor Video Generation</H1>

      {/* Form Section */}
      {showForm && (
        <div className="space-y-4 max-w-lg mb-6">
          <div>
            <label htmlFor="topic" className="block text-sm font-medium text-gray-700 mb-1">
              Topic
            </label>
            <Input
              id="topic"
              value={formTopic}
              onChange={(e) => setFormTopic(e.target.value)}
              placeholder="Enter the topic for the video (e.g., Photosynthesis)"
              disabled={isGenerating}
            />
          </div>
          <div>
            <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-1">
              Language
            </label>
            <Select value={selectedLanguage} onValueChange={setSelectedLanguage} disabled={isGenerating}>
              <SelectTrigger id="language">
                <SelectValue placeholder="Select Language" />
              </SelectTrigger>
              <SelectContent>
                {languagesData.languages.map((lang) => (
                  <SelectItem key={lang.language_code} value={lang.language_code}>
                    {lang.language_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label htmlFor="voice" className="block text-sm font-medium text-gray-700 mb-1">
              Voice
            </label>
            <Select
              value={selectedVoice}
              onValueChange={setSelectedVoice}
              disabled={!selectedLanguage || availableVoices.length === 0 || isGenerating}
            >
              <SelectTrigger id="voice">
                <SelectValue placeholder="Select Voice" />
              </SelectTrigger>
              <SelectContent>
                {availableVoices.map((voice) => (
                  <SelectItem key={voice.id} value={voice.id}>
                    {voice.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
             {selectedLanguage && availableVoices.length === 0 && (
                <Para className="text-xs text-red-500 mt-1">No voices available for this language.</Para>
            )}
          </div>
          <Button onClick={handleGenerate} disabled={!formTopic || !selectedLanguage || !selectedVoice || isGenerating}>
            {isGenerating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              'Generate Video'
            )}
          </Button>
           {/* Display errors/cancellation messages from the store */}
           {status === 'cancelled' && <Para className="text-yellow-600 mt-2">{errorMessage || 'Generation was cancelled.'}</Para>}
           {status === 'failed' && <Para className="text-red-600 mt-2">Error: {errorMessage || 'Generation failed.'}</Para>}
        </div>
      )}

      {/* Generation Status Section */}
      {isGenerating && (
        <div className="mt-6 p-6 border rounded-lg shadow-md max-w-md text-center bg-gray-50">
          <H1 className="mb-4">Generating Video...</H1>
          <Para className="mb-2">Status: <span className="font-semibold">{status}</span></Para>
          <ProgressComponent value={progress} />
          <Para className="mt-4 mb-6 text-sm text-gray-600">Job ID: {jobId}</Para>
          <Para className="mb-6">Please wait while we create your video on "{jobTopic}".</Para> {/* Use jobTopic from store */}
          <Button variant="destructive" onClick={handleCancel}>
            Cancel Generation
          </Button>
        </div>
      )}

      {/* Video Display Section */}
      {status === 'completed' && videoUrl ? (
         <div className="mt-6">
            <H1 className="mb-4">Video Ready!</H1>
            <Para className="mb-4">Here is your video about "{jobTopic}":</Para> {/* Use jobTopic from store */}
            <div className="aspect-video max-w-2xl border rounded-lg overflow-hidden shadow-lg bg-black">
                 <video controls src={videoUrl} className="w-full h-full" key={videoUrl}>
                    Your browser does not support the video tag.
                 </video>
            </div>
             <Button onClick={resetFormAndStore} className="mt-4">
                Generate Another Video
            </Button>
        </div>
      ) : null}

      {/* Video History Section */}
      <div className="mt-12 pt-8 border-t">
        <H2 className="mb-4 flex items-center">
          <History className="mr-2 h-6 w-6" /> Your Generated Videos
        </H2>
        {historyLoading && (
          <div className="flex items-center justify-center py-4">
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
            <Para>Loading history...</Para>
          </div>
        )}
        {historyError && (
          <div className="flex items-center text-red-600 bg-red-100 p-3 rounded-md">
             <AlertCircle className="mr-2 h-5 w-5" />
            <Para>{historyError}</Para>
          </div>
        )}
        {!historyLoading && !historyError && videoHistory.length === 0 && (
          <Para className="text-gray-500">You haven't generated any videos yet.</Para>
        )}
        {!historyLoading && !historyError && videoHistory.length > 0 && (
          <>
            <ul className="space-y-3">
              {videoHistory.map((video) => (
                <li key={video.id} className="p-4 border rounded-md flex justify-between items-center bg-white shadow-sm">
                  <div>
                    <Para className="font-semibold">{video.topic}</Para>
                    <Para className="text-sm text-gray-600">
                      Generated: {new Date(video.createdAt).toLocaleString()}
                    </Para>
                    <Para className="text-xs text-gray-500">
                      Lang: {video.language}, Voice: {video.voice}
                    </Para>
                  </div>
                  <a href={video.videoUrl} target="_blank" rel="noopener noreferrer">
                    <Button size="sm" variant="outline">View Video</Button>
                  </a>
                </li>
              ))}
            </ul>
            <Para className="text-xs text-gray-500 mt-4">
              Note: Video links are provided by the external generation service and may expire after 7 days.
            </Para>
          </>
        )}
      </div>
    </div>
  );
}
