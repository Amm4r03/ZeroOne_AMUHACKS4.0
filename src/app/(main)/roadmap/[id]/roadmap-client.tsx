"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";

interface Subtopic {
  name: string;
  isCompleted: boolean;
}

interface Topic {
  name: string;
  subtopics: Subtopic[];
  resources: string[];
  youtube_link: string;
}

interface RoadmapData {
  topics: Topic[];
  completion_time: number;
}

interface RoadmapClientProps {
  initialData: RoadmapData;
  id: string;
}

export default function RoadmapClient({ initialData, id }: RoadmapClientProps) {
  const router = useRouter();
  const [roadmapData, setRoadmapData] = useState<RoadmapData>(initialData);
  const [selectedSubtopic, setSelectedSubtopic] = useState<string | null>(null);
  const [subtopicDetails, setSubtopicDetails] = useState<string>("");
  // State to track loading for each "Read More" button
  const [readMoreLoading, setReadMoreLoading] = useState<Record<string, boolean>>(
    {}
  );

  const handleSubtopicToggle = async (
    topicIndex: number,
    subtopicIndex: number
  ) => {
    try {
      const updatedTopics = [...roadmapData.topics];
      const currentSubtopic =
        updatedTopics[topicIndex].subtopics[subtopicIndex];
      currentSubtopic.isCompleted = !currentSubtopic.isCompleted;

      await fetch(`/api/roadmap/${id}/progress`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topicName: updatedTopics[topicIndex].name,
          subtopicName: currentSubtopic.name,
          isCompleted: currentSubtopic.isCompleted,
        }),
      });

      setRoadmapData({ ...roadmapData, topics: updatedTopics });
    } catch (error) {
      console.error("Error updating progress:", error);
    }
  };

  const handleReadMore = async (subtopicName: string) => {
    // Set loading state for this specific button
    setReadMoreLoading((prev) => ({ ...prev, [subtopicName]: true }));
    try {
      const response = await fetch(
        `/api/subtopic-details?name=${encodeURIComponent(subtopicName)}`
      );
      const data = await response.json();
      setSelectedSubtopic(subtopicName);
      setSubtopicDetails(
        data.details || "No additional information available."
      );
    } catch (error) {
      console.error("Error fetching subtopic details:", error);
      setSubtopicDetails("Failed to load additional information.");
    } finally {
      // Unset loading state regardless of success/failure
      setReadMoreLoading((prev) => ({ ...prev, [subtopicName]: false }));
    }
  };

  const handleTakeQuiz = async (topicName: string) => {
    try {
      const response = await fetch("/api/quiz", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic: topicName,
          difficulty: "beginner",
          questionCount: "5",
          questionType: "multiple-choice",
        }),
      });

      const data = await response.json();
      if (data.id) {
        router.push(`/quiz/${data.id}`);
      }
    } catch (error) {
      console.error("Error creating quiz:", error);
    }
  };

  return (
    <div className="p-10 pl-32">
      <div className="mb-8">
        <h2 className="mb-4 text-2xl font-bold">Your Learning Roadmap</h2>
        <p className="text-gray-600">
          Estimated completion time: {roadmapData.completion_time} weeks
        </p>
      </div>

      <div className="space-y-8">
        {roadmapData.topics.map((topic, topicIndex) => (
          <div key={topic.name} className="rounded-xl bg-white p-6 shadow-lg">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-xl font-semibold">{topic.name}</h3>
              <button
                onClick={() => handleTakeQuiz(topic.name)}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                Take Quiz
              </button>
            </div>
            <div className="space-y-3">
              {topic.subtopics.map((subtopic, subtopicIndex) => (
                <div key={subtopic.name} className="space-y-2">
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={subtopic.isCompleted}
                      onChange={() =>
                        handleSubtopicToggle(topicIndex, subtopicIndex)
                      }
                      className="h-5 w-5 rounded border-gray-300"
                    />
                    <span
                      className={`text-lg ${subtopic.isCompleted ? "text-gray-400 line-through" : ""}`}
                    >
                      {subtopic.name}
                    </span>
                    {/* Use the enhanced Button component */}
                    <Button
                      variant="link"
                      size="sm"
                      onClick={() => handleReadMore(subtopic.name)}
                      loading={readMoreLoading[subtopic.name]} // Pass loading state
                      disabled={readMoreLoading[subtopic.name]} // Pass disabled state
                      className="ml-2 h-auto p-0 text-sm" // Adjust styling as needed
                    >
                      Read More
                    </Button>
                  </div>
                  {selectedSubtopic === subtopic.name && !readMoreLoading[subtopic.name] && ( // Only show details if not loading
                    <div className="mt-2 ml-8 rounded-lg bg-gray-50 p-4">
                      <p className="text-sm text-gray-700">{subtopicDetails}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Resources and YouTube link for each topic */}
            <div className="mt-4 border-t border-gray-200 pt-4">
              {topic.resources && topic.resources.length > 0 && (
                <div className="mb-3">
                  <h4 className="mb-2 text-lg font-medium">
                    Additional Resources
                  </h4>
                  <ul className="list-disc space-y-1 pl-5">
                    {topic.resources.map((resource) => (
                      <li key={resource}>
                        <p>{resource}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {topic.youtube_link && (
                <div>
                  <h4 className="mb-2 text-lg font-medium">Video Tutorial</h4>
                  <a
                    href={topic.youtube_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    Watch Tutorial
                  </a>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
