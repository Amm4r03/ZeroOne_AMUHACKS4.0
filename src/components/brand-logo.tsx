import { Poppins } from "next/font/google";
import Image from "next/image";

const poppins = Poppins({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800", "900"],
});

export default function Branding() {
  return (
    <div className={`flex items-center gap-2 ${poppins.className}`}>
      <Image
        src="/logo.svg"
        width={30}
        height={30}
        alt="Logo for Clarity Hub"
      />
      <span className="text-brand-logo-text font-semibold">ClarityHub</span>
    </div>
  );
}
