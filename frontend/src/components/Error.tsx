interface ErrorProps {
  message?: string
  onRetry?: () => void
}

export default function Error({ message = '加载失败，请稍后重试', onRetry }: ErrorProps) {
  return (
    <div className="card text-center py-12">
      <div className="mb-4 text-rose-500">
        <svg
          className="mx-auto h-12 w-12"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>
      <p className="mb-4 text-slate-600">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="btn-primary"
        >
          重试
        </button>
      )}
    </div>
  )
}
