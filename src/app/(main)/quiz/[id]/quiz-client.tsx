"use client";

import { useEffect, useState } from "react";

import { H2 } from "@/components/typography/h2";
import { Para } from "@/components/typography/para";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

interface Question {
  id: number;
  question: string;
  options: string[];
  answer: string;
}

interface Quiz {
  topic: string;
  questions: Question[];
}

export function QuizClient({ id }: { id: string }) {
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<{
    [key: number]: number;
  }>({});
  const [showResults, setShowResults] = useState(false);
  const [score, setScore] = useState(0);

  useEffect(() => {
    const fetchQuiz = async () => {
      try {
        const response = await fetch(`/api/quiz/${id}`);
        if (!response.ok) {
          throw new Error("Failed to fetch quiz");
        }
        const data = await response.json();
        setQuiz(data);
      } catch (err) {
        setError("Failed to load quiz. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchQuiz();
  }, [id]);

  const handleAnswerSelect = (questionId: number, answerIndex: number) => {
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionId]: answerIndex,
    }));
  };

  const handleNext = () => {
    if (quiz && currentQuestion < quiz.questions.length - 1) {
      setCurrentQuestion((prev) => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion((prev) => prev - 1);
    }
  };

  const handleSubmit = async () => {
    if (!quiz) return;

    const totalQuestions = quiz.questions.length;
    let correctAnswers = 0;

    quiz.questions.forEach((question, index) => {
      if (selectedAnswers[question.id] === question.options.indexOf(question.answer)) {
        correctAnswers++;
      }
    });

    const finalScore = (correctAnswers / totalQuestions) * 100;
    setScore(finalScore);
    setShowResults(true);

    try {
      await fetch(`/api/quiz/${id}/score`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ score: finalScore }),
      });
    } catch (error) {
      console.error('Failed to save quiz score:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-10 pl-32">
        <Para>Loading quiz...</Para>
      </div>
    );
  }

  if (error || !quiz) {
    return (
      <div className="p-10 pl-32">
        <Para className="text-red-500">{error || "Quiz not found"}</Para>
      </div>
    );
  }

  const question = quiz.questions[currentQuestion];

  return (
    <div className="p-10 pl-32">
      <div className="mb-10">
        <H2>{quiz.topic}</H2>
      </div>

      {!showResults ? (
        <div className="rounded-xl bg-white p-6 shadow-lg">
          <div className="mb-6">
            <div className="mb-2 flex justify-between">
              <span className="text-sm text-gray-500">
                Question {currentQuestion + 1} of {quiz.questions.length}
              </span>
              <span className="text-sm text-gray-500">
                {Math.round(
                  (Object.keys(selectedAnswers).length /
                    quiz.questions.length) *
                    100
                )}% Complete
              </span>
            </div>
            <div className="h-2 w-full rounded-full bg-gray-200">
              <div
                className="bg-brand-logo-text h-2 rounded-full transition-all"
                style={{
                  width: `${(Object.keys(selectedAnswers).length / quiz.questions.length) * 100}%`,
                }}
              />
            </div>
          </div>

          <div className="mb-8">
            <h3 className="mb-6 text-xl font-semibold">{question.question}</h3>
            <RadioGroup
              value={selectedAnswers[question.id]?.toString() || ""}
              onValueChange={(value) =>
                handleAnswerSelect(question.id, parseInt(value))
              }
              className="flex flex-col gap-4"
            >
              {question.options.map((option, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <RadioGroupItem
                    value={index.toString()}
                    id={`option-${index}`}
                  />
                  <label
                    htmlFor={`option-${index}`}
                    className="text-lg leading-none font-medium peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    {option}
                  </label>
                </div>
              ))}
            </RadioGroup>
          </div>

          <div className="flex justify-between">
            <Button
              variant="outline"
              onClick={handlePrevious}
              disabled={currentQuestion === 0}
            >
              Previous
            </Button>
            {currentQuestion === quiz.questions.length - 1 ? (
              <Button
                onClick={handleSubmit}
                className="bg-brand-logo-text hover:bg-brand-logo-text/90 text-white"
                disabled={
                  Object.keys(selectedAnswers).length !== quiz.questions.length
                }
              >
                Submit
              </Button>
            ) : (
              <Button
                onClick={handleNext}
                className="bg-brand-logo-text hover:bg-brand-logo-text/90 text-white"
                disabled={selectedAnswers[question.id] === undefined}
              >
                Next
              </Button>
            )}
          </div>
        </div>
      ) : (
        <div className="rounded-xl bg-white p-6 shadow-lg">
          <div className="mb-6 text-center">
            <h3 className="mb-4 text-2xl font-bold">Quiz Complete!</h3>
            <div className="mb-6">
              <span className="text-brand-logo-text text-4xl font-bold">
                {Math.round(score)}%
              </span>
            </div>
            <Para>
              You got {Math.round((score / 100) * quiz.questions.length)} out of{" "}
              {quiz.questions.length} questions correct.
            </Para>
          </div>

          <div className="flex justify-center">
            <Button
              onClick={() => {
                setShowResults(false);
                setCurrentQuestion(0);
                setSelectedAnswers({});
                setScore(0);
              }}
              className="bg-brand-logo-text hover:bg-brand-logo-text/90 text-white"
            >
              Retake Quiz
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}