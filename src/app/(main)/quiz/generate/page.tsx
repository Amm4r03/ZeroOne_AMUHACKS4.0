"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { H2 } from "@/components/typography/h2";
import { Para } from "@/components/typography/para";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function GenerateQuiz() {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [topic, setTopic] = useState("");
  const [numQuestions, setNumQuestions] = useState(5);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      if (!topic) {
        setError("Please enter a topic");
        return;
      }
      setError("");
      const response = await fetch("/api/quiz", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic,
          num_questions: numQuestions,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        router.push(`/quiz/${data.id}`);
      }
    } catch (error) {
      console.error("Error generating quiz:", error);
      setError("An error occurred while generating the quiz");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-10 pl-32">
      <div>
        <H2>Generate Quiz</H2>
        <Para>
          AI-generated quiz to test your knowledge on specific topics.
        </Para>
      </div>

      <form
        onSubmit={handleSubmit}
        className="mt-10 flex max-w-2xl flex-col gap-6"
      >
        <div className="flex flex-col gap-2">
          <label htmlFor="topic" className="text-lg font-medium">
            Enter your quiz topic
          </label>
          <Input
            id="topic"
            placeholder="Ex: Newton's Laws of Motion"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="rounded-lg bg-white p-4"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="numQuestions" className="text-lg font-medium">
            Number of Questions
          </label>
          <Input
            id="numQuestions"
            type="number"
            min={1}
            max={20}
            value={numQuestions}
            onChange={(e) => setNumQuestions(parseInt(e.target.value))}
            className="rounded-lg bg-white p-4"
          />
        </div>

        <Button
          type="submit"
          loading={loading} // Pass loading state to the loading prop
          disabled={loading} // Keep disabled prop for clarity
          className="w-fit rounded-none text-lg"
        >
          GENERATE QUIZ
        </Button>

        {error && <p className="text-red-500">{error}</p>}
      </form>
    </div>
  );
}
