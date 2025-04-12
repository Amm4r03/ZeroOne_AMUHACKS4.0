"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

export default function HeroSlides() {
  const [currentSlide, setCurrentSlide] = useState(1);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSlide((prevSlide) => (prevSlide === 5 ? 1 : prevSlide + 1));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <Image
      src={`/landing-images/hero-${currentSlide}.svg`}
      width={400}
      height={400}
      alt="Hero Image"
      className="mx-auto mt-auto md:mx-0"
    />
  );
}
