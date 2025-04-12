import { QuizClient } from "./quiz-client";

export default async function QuizPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return <QuizClient id={(await params).id} />;
}
