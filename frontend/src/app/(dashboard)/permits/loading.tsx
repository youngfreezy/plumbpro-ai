export default function PermitsLoading() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-8 w-32 bg-muted animate-pulse rounded-md" />
          <div className="h-4 w-48 bg-muted animate-pulse rounded-md mt-2" />
        </div>
        <div className="h-10 w-28 bg-muted animate-pulse rounded-md" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="rounded-lg border bg-card p-5">
            <div className="h-5 w-3/4 bg-muted animate-pulse rounded mb-3" />
            <div className="h-4 w-1/2 bg-muted animate-pulse rounded mb-2" />
            <div className="h-4 w-full bg-muted animate-pulse rounded mb-2" />
            <div className="h-3 w-2/3 bg-muted animate-pulse rounded" />
          </div>
        ))}
      </div>
    </div>
  );
}
