'use client';

import React from 'react';
import { useAiTutorStore } from '@/lib/ai-tutor-store';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react'; // Using lucide-react for icons

export function AiTutorPersistentTimer() {
  // Select individual state slices needed by this component
  const jobId = useAiTutorStore((state) => state.jobId);
  const status = useAiTutorStore((state) => state.status);
  const progress = useAiTutorStore((state) => state.progress);
  const topic = useAiTutorStore((state) => state.topic);
  const cancelJob = useAiTutorStore((state) => state.cancelJob); // Get the cancel action

  const isGenerating = status === 'queued' || status === 'processing';

  // Only render if a job is actively generating
  if (!isGenerating || !jobId) {
    return null;
  }

  const handleCancel = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent potential link navigation if wrapped
    if (confirm('Are you sure you want to cancel this video generation?')) {
        cancelJob();
    }
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 w-64 rounded-lg border bg-card text-card-foreground shadow-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-semibold">AI Tutor Generation</p>
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={handleCancel}>
           <X className="h-4 w-4" />
           <span className="sr-only">Cancel Generation</span>
        </Button>
      </div>
      <p className="text-xs text-muted-foreground mb-1 truncate" title={topic ?? undefined}>
        Topic: {topic || '...'}
      </p>
      <p className="text-xs text-muted-foreground mb-2">
        Status: <span className="font-medium">{status}</span>
      </p>
      <Progress value={progress} className="h-2" />
    </div>
  );
}
