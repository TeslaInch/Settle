import { type LucideIcon } from "lucide-react";

interface Props {
  icon: LucideIcon;
  message: string;
  ctaLabel?: string;
  onCta?: () => void;
}

export default function EmptyState({ icon: Icon, message, ctaLabel, onCta }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-50">
        <Icon size={28} className="text-green-600" />
      </div>
      <p className="text-gray-500 text-sm leading-relaxed max-w-[220px]">{message}</p>
      {ctaLabel && onCta && (
        <button
          onClick={onCta}
          className="mt-5 rounded-full bg-green-600 px-6 py-2.5 text-sm font-semibold text-white active:scale-95 transition-transform"
        >
          {ctaLabel}
        </button>
      )}
    </div>
  );
}
