export default function Loading() {
  return (
    <div className="card-dark flex flex-col items-center justify-center gap-3 py-12">
      <div className="h-12 w-12 animate-spin rounded-full border-2 border-white/30 border-t-orange-400" />
      <p className="text-sm font-medium text-slate-200">正在同步训练数据...</p>
    </div>
  )
}
