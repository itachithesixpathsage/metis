import { cn } from '../../utils/cn';

interface HeaderProps {
  onMenuClick: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  return (
    <header className="page-header sticky top-0 z-30">
      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left side - Mobile menu button */}
          <div className="flex items-center gap-4 lg:hidden">
            <button
              type="button"
              onClick={onMenuClick}
              className="btn btn-ghost btn-sm p-2"
              aria-label="Open navigation menu"
              aria-expanded="false"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <h1 className="text-lg font-semibold text-slate-100 truncate">Project Métis</h1>
          </div>

          {/* Center - Page title (hidden on mobile) */}
          <div className="hidden lg:flex lg:items-center lg:flex-1 lg:justify-center">
            <h1 className="text-xl font-semibold text-slate-100">Project Métis</h1>
          </div>

          {/* Right side - Status indicators */}
          <div className="flex items-center gap-3">
            {/* Connection status */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/50 border border-slate-700">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse-subtle" aria-hidden="true" />
              <span className="text-xs font-medium text-green-400">Connected</span>
            </div>

            {/* Environment badge */}
            <span className="badge badge-info hidden sm:inline-flex">
              Research
            </span>

            {/* User placeholder */}
            <div className="w-8 h-8 rounded-full bg-metis-600/20 flex items-center justify-center">
              <span className="text-sm font-medium text-metis-400">M</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}