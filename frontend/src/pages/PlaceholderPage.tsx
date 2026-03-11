import Header from '@/components/layout/Header';
import { Construction } from 'lucide-react';

interface PlaceholderPageProps {
  title: string;
  subtitle?: string;
}

export default function PlaceholderPage({ title, subtitle }: PlaceholderPageProps) {
  return (
    <div>
      <Header title={title} subtitle={subtitle} />
      <div className="flex flex-col items-center justify-center py-32 text-gray-400">
        <Construction size={48} className="mb-4" />
        <h2 className="text-lg font-semibold text-gray-500">En construccion</h2>
        <p className="text-sm mt-1">Este modulo estara disponible pronto</p>
      </div>
    </div>
  );
}
