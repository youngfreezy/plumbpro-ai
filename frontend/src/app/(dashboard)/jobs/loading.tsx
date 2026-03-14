export default function JobsLoading() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="h-8 w-24 bg-muted animate-pulse rounded-md" />
          <div className="h-4 w-48 bg-muted animate-pulse rounded-md mt-2" />
        </div>
        <div className="h-10 w-28 bg-muted animate-pulse rounded-md" />
      </div>

      <div className="flex gap-3">
        <div className="h-10 flex-1 bg-muted animate-pulse rounded-md" />
        <div className="h-10 w-36 bg-muted animate-pulse rounded-md" />
        <div className="h-10 w-36 bg-muted animate-pulse rounded-md" />
      </div>

      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="rounded-lg border bg-card p-4">
            <div className="flex items-start justify-between mb-3">
              <div className="h-5 w-48 bg-muted animate-pulse rounded" />
              <div className="h-5 w-16 bg-muted animate-pulse rounded-full" />
            </div>
            <div className="space-y-2">
              <div className="h-3.5 w-36 bg-muted animate-pulse rounded" />
              <div className="h-3.5 w-52 bg-muted animate-pulse rounded" />
            </div>
            <div className="flex items-center justify-between mt-3 pt-3 border-t">
              <div className="h-5 w-20 bg-muted animate-pulse rounded-full" />
              <div className="h-3.5 w-24 bg-muted animate-pulse rounded" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
