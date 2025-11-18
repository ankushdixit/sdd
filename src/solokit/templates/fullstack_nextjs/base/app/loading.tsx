export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="space-y-4 text-center">
        <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-white/30 border-t-white"></div>
        <p className="text-sm text-white/70">Loading...</p>
      </div>
    </div>
  );
}
