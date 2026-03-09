import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/auth";

interface TopbarProps {
  title?: string;
}

export default function Topbar({ title }: TopbarProps) {
  const { user } = useAuth();

  return (
    <header className="fixed top-0 left-[260px] right-0 z-30 flex h-16 items-center justify-between border-b border-border bg-white px-6">
      <h2 className="text-lg font-semibold text-foreground">
        {title || "Dashboard"}
      </h2>

      <div className="flex items-center gap-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar..."
            className="w-64 pl-9"
          />
        </div>

        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground">
            {user?.nombre?.charAt(0)?.toUpperCase() || "U"}
          </div>
          <span className="text-sm font-medium text-foreground">
            {user?.nombre}
          </span>
        </div>
      </div>
    </header>
  );
}
