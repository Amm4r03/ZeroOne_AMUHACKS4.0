import Link from "next/link";

import Branding from "@/components/brand-logo";
import HeroSlides from "@/components/landing/hero-slides";
import { H1 } from "@/components/typography/h1";
import { Para } from "@/components/typography/para";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="mx-auto flex h-[90dvh] w-full max-w-[1440px] flex-col justify-between p-5 sm:p-10 md:flex-row">
      <div className="flex h-full flex-col justify-between pb-10 text-center sm:text-left">
        <Branding />

        <div className="flex flex-col flex-wrap">
          <H1>
            Welcome to <span className="text-brand-logo-text">ClarityHub</span>
          </H1>
          <Para className="max-w-lg">
            AI-powered study planner that helps you generate structured
            roadmaps, access curated resources, and test your knowledge with
            quizzes.
          </Para>

          <Link className="mt-5" href={"/dashboard"}>
            <Button className="cursor-pointer rounded-none sm:w-fit">
              GET STARTED
            </Button>
          </Link>
        </div>
      </div>

      <HeroSlides />
    </div>
  );
}
