import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({
  currentPage,
  totalPages,
  onPageChange,
}: PaginationProps) {
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <div className="flex items-center justify-center gap-2 py-6" data-testid="pagination">
      <Button
        size="icon"
        variant="ghost"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="h-10 w-10"
        data-testid="button-page-prev"
      >
        <ChevronLeft className="w-5 h-5" />
      </Button>

      {pages.map((page) => (
        <Button
          key={page}
          size="sm"
          variant={currentPage === page ? "default" : "outline"}
          onClick={() => onPageChange(page)}
          className="min-w-10 h-10"
          data-testid={`button-page-${page}`}
        >
          {page}
        </Button>
      ))}

      <Button
        size="icon"
        variant="ghost"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="h-10 w-10"
        data-testid="button-page-next"
      >
        <ChevronRight className="w-5 h-5" />
      </Button>
    </div>
  );
}
