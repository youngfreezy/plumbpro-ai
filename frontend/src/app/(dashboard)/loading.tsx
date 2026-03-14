export default function DashboardLoading() {
  return (
    <div className="space-y-6">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div>
          <div className="h-8 w-40 bg-muted animate-pulse rounded-md" />
          <div className="h-4 w-56 bg-muted animate-pulse rounded-md mt-2" />
        </div>
        <div className="h-9 w-24 bg-muted animate-pulse rounded-md" />
      </div>

      {/* Stats grid skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-lg border bg-card p-5">
            <div className="flex items-center justify-between">
              <div>
                <div className="h-4 w-24 bg-muted animate-pulse rounded" />
                <div className="h-9 w-12 bg-muted animate-pulse rounded mt-2" />
              </div>
              <div className="w-10 h-10 bg-muted animate-pulse rounded-lg" />
            </div>
            <div className="h-3 w-32 bg-muted animate-pulse rounded mt-3" />
          </div>
        ))}
      </div>

      {/* Content grid skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-lg border bg-card p-6">
          <div className="h-5 w-36 bg-muted animate-pulse rounded mb-4" />
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-16 bg-muted animate-pulse rounded-lg" />
            ))}
          </div>
        </div>
        <div className="rounded-lg border bg-card p-6">
          <div className="h-5 w-32 bg-muted animate-pulse rounded mb-4" />
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex gap-3">
                <div className="w-4 h-4 bg-muted animate-pulse rounded-full shrink-0" />
                <div className="flex-1">
                  <div className="h-3 w-full bg-muted animate-pulse rounded" />
                  <div className="h-2 w-16 bg-muted animate-pulse rounded mt-1.5" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
