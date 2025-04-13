import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import FlashcardViewClient from "./flashcard-client";

export default async function FlashcardSetPage({ 
  params 
}: { 
  params: { id: string } 
}) {
  const { userId } = await auth();

  if (!userId) {
    redirect("/sign-in");
  }

  return <FlashcardViewClient params={params} />;
}