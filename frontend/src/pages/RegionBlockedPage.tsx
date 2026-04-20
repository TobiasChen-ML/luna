import { Globe, MapPin, AlertTriangle } from 'lucide-react';

interface RegionBlockedPageProps {
  countryCode?: string;
  countryName?: string;
}

export function RegionBlockedPage({ countryCode, countryName }: RegionBlockedPageProps) {
  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center space-y-8">
        {/* Icon */}
        <div className="relative mx-auto w-24 h-24">
          <div className="absolute inset-0 bg-red-500/20 rounded-full animate-pulse" />
          <div className="relative w-full h-full bg-zinc-900 rounded-full flex items-center justify-center border border-red-500/30">
            <Globe size={48} className="text-red-400" />
          </div>
        </div>

        {/* Title */}
        <div className="space-y-2">
          <h1 className="text-3xl font-heading font-bold text-white">
            Service Unavailable in Your Region
          </h1>
          <p className="text-zinc-400 text-lg">
            We do not currently provide service in your region.
          </p>
        </div>

        {/* Location Info */}
        {(countryCode || countryName) && (
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 inline-flex items-center gap-3">
            <MapPin size={20} className="text-zinc-500" />
            <span className="text-zinc-400">
              Detected location: <span className="text-white font-medium">{countryName || countryCode}</span>
            </span>
          </div>
        )}

        {/* Info Box */}
        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4 text-left">
          <div className="flex items-start gap-3">
            <AlertTriangle size={20} className="text-yellow-500 flex-shrink-0 mt-0.5" />
            <div className="space-y-2">
              <p className="text-yellow-200 text-sm font-medium">
                Why is this service restricted?
              </p>
              <p className="text-zinc-400 text-sm">
                Due to regulatory requirements and content policies, service is blocked for mainland China IP ranges.
                Access from Hong Kong and Macao is allowed.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <p className="text-zinc-600 text-sm">
          If you believe this is an error, please contact{' '}
          <a href="mailto:support@roxyclub.ai" className="text-primary-400 hover:text-primary-300">
            support@roxyclub.ai
          </a>
        </p>
      </div>
    </div>
  );
}
