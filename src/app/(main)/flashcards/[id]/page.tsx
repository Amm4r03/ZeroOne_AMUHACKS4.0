"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { H1 } from "@/components/typography/h1";
import { H2 } from "@/components/typography/h2";
import { Para } from "@/components/typography/para";
import { useRouter } from "next/navigation";

interface Flashcard {
  id: string;
  question: string;
  hint: string;
  answer: string;
  isLearned: boolean;
}

interface FlashcardSet {
  id: string;
  topic: string;
  difficulty: string;
  createdAt: string;
  flashcards: Flashcard[];
}

export default function FlashcardViewClient({ 
  params 
}: { 
  params: { id: string } 
}) {
  const router = useRouter();
  const [flashcardSet, setFlashcardSet] = useState<FlashcardSet | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [showHint, setShowHint] = useState(false);

  useEffect(() => {
    const fetchFlashcardSet = async () => {
      try {
        const response = await fetch(`/api/flashcards/${params.id}`);
        if (!response.ok) {
          throw new Error("Failed to fetch flashcard set");
        }
        const data = await response.json();
        setFlashcardSet(data);
      } catch (err) {
        setError("Failed to load flashcards");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchFlashcardSet();
  }, [params.id]);

  const handleNext = () => {
    if (!flashcardSet) return;
    setIsFlipped(false);
    setShowHint(false);
    setCurrentCardIndex((prev) => 
      prev < flashcardSet.flashcards.length - 1 ? prev + 1 : 0
    );
  };

  const handlePrevious = () => {
    if (!flashcardSet) return;
    setIsFlipped(false);
    setShowHint(false);
    setCurrentCardIndex((prev) => 
      prev > 0 ? prev - 1 : flashcardSet.flashcards.length - 1
    );
  };

  const toggleFlip = () => {
    setIsFlipped(!isFlipped);
  };

  const toggleHint = () => {
    setShowHint(!showHint);
  };

  const markAsLearned = async () => {
    if (!flashcardSet) return;
    const currentCard = flashcardSet.flashcards[currentCardIndex];
    
    try {
      const response = await fetch(`/api/flashcards/card/${currentCard.id}/toggle-learned`, {
        method: "POST",
      });

      if (response.ok) {
        // Update local state
        const updatedFlashcards = [...flashcardSet.flashcards];
        updatedFlashcards[currentCardIndex] = {
          ...currentCard,
          isLearned: !currentCard.isLearned
        };
        
        setFlashcardSet({
          ...flashcardSet,
          flashcards: updatedFlashcards
        });
      }
    } catch (error) {
      console.error("Failed to mark card as learned:", error);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="mb-4 h-6 w-6 animate-spin rounded-full border-t-2 border-b-2 border-gray-900"></div>
          <Para>Loading flashcards...</Para>
        </div>
      </div>
    );
  }

  if (error || !flashcardSet) {
    return (
      <div className="p-10 pl-32 text-center">
        <H2>Error</H2>
        <Para className="mt-4 text-red-500">{error || "Flashcard set not found"}</Para>
        <Button className="mt-6" onClick={() => router.push("/flashcards")}>
          Go Back
        </Button>
      </div>
    );
  }

  const currentCard = flashcardSet.flashcards[currentCardIndex];
  const progress = `${currentCardIndex + 1} / ${flashcardSet.flashcards.length}`;

  return (
    <div className="p-10 pl-32">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <H1>{flashcardSet.topic}</H1>
          <Para className="text-gray-600">
            Difficulty: {flashcardSet.difficulty.charAt(0).toUpperCase() + flashcardSet.difficulty.slice(1)} · 
            Created: {new Date(flashcardSet.createdAt).toLocaleDateString()}
          </Para>
        </div>
        <Button 
          variant="outline" 
          onClick={() => router.push("/flashcards")}
        >
          Back to Flashcards
        </Button>
      </div>

      {/* Flashcard display */}
      <div className="mx-auto max-w-2xl">
        <div className="mb-4 flex items-center justify-between">
          <Para className="text-gray-600">{progress}</Para>
          <div className="flex items-center">
            <Button 
              variant={currentCard.isLearned ? "default" : "outline"} 
              onClick={markAsLearned}
              className="mr-2"
            >
              {currentCard.isLearned ? "Learned" : "Mark as Learned"}
            </Button>
          </div>
        </div>

        {/* Flashcard */}
        <div 
          className={`mb-6 h-64 w-full cursor-pointer rounded-xl bg-white p-8 shadow-md transition-all duration-300 ${
            isFlipped ? "rotate-y-180" : ""
          }`}
          onClick={toggleFlip}
        >
          <div className="flex h-full flex-col items-center justify-center">
            {isFlipped ? (
              <div className="text-center">
                <H2 className="mb-4">Answer</H2>
                <Para className="text-xl">{currentCard.answer}</Para>
              </div>
            ) : (
              <div className="text-center">
                <H2 className="mb-4">Question</H2>
                <Para className="text-xl">{currentCard.question}</Para>
                
                {showHint && (
                  <div className="mt-4 rounded-lg bg-gray-100 p-3">
                    <Para className="text-sm italic">Hint: {currentCard.hint}</Para>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Controls */}
        <div className="mt-8 flex items-center justify-between">
          <Button variant="outline" onClick={handlePrevious}>
            Previous
          </Button>
          
          {!isFlipped && (
            <Button
              variant="outline"
              onClick={(e) => {
                e.stopPropagation();
                toggleHint();
              }}
            >
              {showHint ? "Hide Hint" : "Show Hint"}
            </Button>
          )}
          
          <Button variant="outline" onClick={handleNext}>
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}