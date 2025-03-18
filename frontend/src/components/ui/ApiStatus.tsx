'use client';

import { useEffect, useState } from 'react';
import { checkBackendConnection } from '@/lib/utils';
import { ExclamationTriangleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

export function ApiStatus() {
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [isChecking, setIsChecking] = useState(false);

  const checkConnection = async () => {
    setIsChecking(true);
    try {
      const connected = await checkBackendConnection();
      setIsConnected(connected);
    } catch (error) {
      setIsConnected(false);
      console.error('Error checking API connection:', error);
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    checkConnection();
    
    // Check connection every 30 seconds
    const interval = setInterval(checkConnection, 30000);
    
    return () => clearInterval(interval);
  }, []);

  if (isConnected === null) {
    return (
      <div className="flex items-center space-x-2 text-sm text-muted-foreground">
        <div className="h-2 w-2 animate-pulse rounded-full bg-muted-foreground"></div>
        <span>Checking API connection...</span>
      </div>
    );
  }

  if (isConnected) {
    return (
      <div className="flex items-center space-x-2 text-sm text-green-600">
        <CheckCircleIcon className="h-4 w-4" />
        <span>API Connected</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col space-y-2">
      <div className="flex items-center space-x-2 text-sm text-destructive">
        <ExclamationTriangleIcon className="h-4 w-4" />
        <span>API Connection Failed</span>
      </div>
      <button
        onClick={checkConnection}
        disabled={isChecking}
        className="text-xs text-primary hover:underline"
      >
        {isChecking ? 'Checking...' : 'Retry Connection'}
      </button>
      <div className="text-xs text-muted-foreground">
        Make sure the backend server is running at{' '}
        <code className="bg-muted px-1 py-0.5 rounded text-xs">
          {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}
        </code>
      </div>
    </div>
  );
} 