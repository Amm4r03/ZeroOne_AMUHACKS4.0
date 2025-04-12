"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { H2 } from "@/components/typography/h2";
import { Para } from "@/components/typography/para";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function GenerateQuiz() {
  const [topic, setTopic] = useState("");
  const [difficulty, setDifficulty] = useState("intermediate");
  const [questionCount, setQuestionCount] = useState("5");
  const [questionType, setQuestionType] = useState("multiple-choice");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const response = await fetch("/api/quiz", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic,
          difficulty,
          questionCount,
          questionType,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        router.push(`/quiz/${data.id}`);
      } else {
        setError(data.error || "Failed to generate quiz");
      }
    } catch (error) {
      console.error("Error generating quiz:", error);
      setError("An unexpected error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-10 pl-32">
      <div>
        <H2>Generate Quiz</H2>
        <Para>
          AI-generated quiz with customized questions to test your knowledge.
        </Para>
      </div>

      <form
        onSubmit={handleSubmit}
        className="mt-10 flex max-w-2xl flex-col gap-6"
      >
        <div className="flex flex-col gap-2">
          <label htmlFor="topic" className="text-lg font-medium">
            Enter quiz topic
          </label>
          <Input
            id="topic"
            placeholder="Ex: Database management concepts"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="h-32 resize-none rounded-xl bg-white p-4"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="difficulty" className="text-lg font-medium">
            Difficulty Level
          </label>
          <Select value={difficulty} onValueChange={setDifficulty}>
            <SelectTrigger className="bg-white text-lg">
              <SelectValue placeholder="Select difficulty" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="beginner">Beginner</SelectItem>
              <SelectItem value="intermediate">Intermediate</SelectItem>
              <SelectItem value="advanced">Advanced</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="questionCount" className="text-lg font-medium">
            Number of Questions
          </label>
          <Select value={questionCount} onValueChange={setQuestionCount}>
            <SelectTrigger className="bg-white text-lg">
              <SelectValue placeholder="Select number of questions" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="5">5 questions</SelectItem>
              <SelectItem value="10">10 questions</SelectItem>
              <SelectItem value="15">15 questions</SelectItem>
              <SelectItem value="20">20 questions</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="questionType" className="text-lg font-medium">
            Question Type
          </label>
          <Select value={questionType} onValueChange={setQuestionType}>
            <SelectTrigger className="bg-white text-lg">
              <SelectValue placeholder="Select question type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="multiple-choice">Multiple Choice</SelectItem>
              <SelectItem value="true-false">True/False</SelectItem>
              <SelectItem value="mixed">Mixed</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {error && (
          <div className="rounded-md bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        <Button 
          type="submit" 
          className="w-fit rounded-none text-lg"
          disabled={isLoading}
        >
          {isLoading ? "Generating..." : "GENERATE"}
        </Button>
      </form>
    </div>
  );
}
