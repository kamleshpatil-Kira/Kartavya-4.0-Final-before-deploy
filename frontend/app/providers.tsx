"use client";

import { HeroUIProvider } from "@heroui/react";
import { CourseProvider } from "./context/CourseContext";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <HeroUIProvider>
      <CourseProvider>{children}</CourseProvider>
    </HeroUIProvider>
  );
}
