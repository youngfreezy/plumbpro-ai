import GlobalNav from "@/components/nav/GlobalNav";

export default function DashboardShell({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background">
      <GlobalNav />
      <main className="container mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
