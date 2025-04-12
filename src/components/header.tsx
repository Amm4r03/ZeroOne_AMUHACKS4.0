import Link from "next/link";

import { SignedIn, UserButton } from "@clerk/nextjs";

import { H3 } from "./typography/h3";
import { Button } from "./ui/button";

const Header = () => {
  return (
    <header className="">
      <div className="flex w-full items-center justify-between">
        <Link href={"/dashboard"}>
          <H3 className="text-brand-logo-text">ClarityHub</H3>
        </Link>
        <div className="flex gap-3">
          <div className="text-brand-logo-text flex items-center gap-1.5 rounded-lg bg-[#F8D7AF] px-2 py-1 text-xs">
            <div className="border-brand-logo-text flex size-4 items-center justify-center rounded-full border">
              i
            </div>
            Personalize your content!
          </div>

          <SignedIn>
            <Button asChild>
              <UserButton />
            </Button>
          </SignedIn>
        </div>
      </div>
    </header>
  );
};

export default Header;
