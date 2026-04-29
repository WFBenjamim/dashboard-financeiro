import { cn } from "@/lib/utils";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  delay?: number;
}

export function Card({ className, children, delay = 0, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-2xl bg-[var(--card)] border border-[var(--border)] p-6 shadow-sm transition-all duration-300 hover:shadow-md hover:border-[var(--accent)]/50",
        className
      )}
      style={{ animationDelay: `${delay}ms` }}
      {...props}
    >
      {children}
    </div>
  );
}
