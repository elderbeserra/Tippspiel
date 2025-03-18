'use client';

import { ReactNode, useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { isAuthenticated, removeAuthToken } from '@/lib/api';
import { ApiStatus } from '@/components/ui/ApiStatus';

interface NavItemProps {
  href: string;
  children: ReactNode;
  className?: string;
}

function NavItem({ href, children, className }: NavItemProps) {
  const pathname = usePathname();
  const isActive = pathname === href;

  return (
    <Link
      href={href}
      className={cn(
        'flex items-center px-4 py-2 text-sm font-medium rounded-md',
        isActive
          ? 'bg-primary text-primary-foreground'
          : 'text-muted-foreground hover:text-foreground hover:bg-accent',
        className
      )}
    >
      {children}
    </Link>
  );
}

interface MainLayoutProps {
  children: ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    setIsLoggedIn(isAuthenticated());
  }, []);

  const handleLogout = () => {
    removeAuthToken();
    window.location.href = '/login';
  };

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-40 border-b bg-background">
        <div className="container flex h-16 items-center justify-between py-4">
          <div className="flex items-center gap-2">
            <Link href="/" className="flex items-center space-x-2">
              <span className="font-bold text-xl">F1 Tippspiel</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            <NavItem href="/">Home</NavItem>
            {isLoggedIn ? (
              <>
                <NavItem href="/leagues">My Leagues</NavItem>
                <NavItem href="/predictions">Predictions</NavItem>
                <NavItem href="/profile">Profile</NavItem>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent rounded-md"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <NavItem href="/login">Login</NavItem>
                <NavItem href="/register">Register</NavItem>
              </>
            )}
          </nav>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              className="w-6 h-6"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d={
                  isMobileMenuOpen
                    ? 'M6 18L18 6M6 6l12 12'
                    : 'M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5'
                }
              />
            </svg>
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t p-4">
            <nav className="flex flex-col space-y-2">
              <NavItem href="/">Home</NavItem>
              {isLoggedIn ? (
                <>
                  <NavItem href="/leagues">My Leagues</NavItem>
                  <NavItem href="/predictions">Predictions</NavItem>
                  <NavItem href="/profile">Profile</NavItem>
                  <button
                    onClick={handleLogout}
                    className="flex items-center px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent rounded-md"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <NavItem href="/login">Login</NavItem>
                  <NavItem href="/register">Register</NavItem>
                </>
              )}
            </nav>
          </div>
        )}
      </header>

      <main className="flex-1 container py-6">{children}</main>

      <footer className="border-t py-6 md:py-0">
        <div className="container flex flex-col md:flex-row items-center justify-between gap-4 md:h-16">
          <div className="flex flex-col md:flex-row items-center gap-4">
            <p className="text-sm text-muted-foreground">
              &copy; {new Date().getFullYear()} F1 Tippspiel. All rights reserved.
            </p>
            <ApiStatus />
          </div>
          <nav className="flex items-center gap-4 text-sm text-muted-foreground">
            <Link href="/about" className="hover:underline">
              About
            </Link>
            <Link href="/privacy" className="hover:underline">
              Privacy
            </Link>
            <Link href="/terms" className="hover:underline">
              Terms
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  );
} 