'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { authService } from '@/services/auth';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card';
import { UserIcon, EnvelopeIcon, CalendarIcon } from '@heroicons/react/24/outline';

export default function ProfilePage() {
  const [isEditing, setIsEditing] = useState(false);

  const { data: user, isLoading, error } = useQuery({
    queryKey: ['current-user'],
    queryFn: () => authService.getCurrentUser(),
  });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const handleLogout = () => {
    authService.logout();
    window.location.href = '/login';
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">My Profile</h1>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      ) : error ? (
        <div className="bg-destructive/15 text-destructive text-sm p-4 rounded-md">
          Failed to load profile. Please try again later.
        </div>
      ) : user ? (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
              <CardDescription>
                Your personal information and account details
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-4 py-2">
                <div className="bg-primary/10 p-3 rounded-full">
                  <UserIcon className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Username</p>
                  <p className="font-medium">{user.name}</p>
                </div>
              </div>

              <div className="flex items-center space-x-4 py-2">
                <div className="bg-primary/10 p-3 rounded-full">
                  <EnvelopeIcon className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Email</p>
                  <p className="font-medium">{user.email}</p>
                </div>
              </div>

              <div className="flex items-center space-x-4 py-2">
                <div className="bg-primary/10 p-3 rounded-full">
                  <CalendarIcon className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Member Since</p>
                  <p className="font-medium">{formatDate(user.created_at)}</p>
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex justify-between border-t pt-6">
              <Button variant="outline" onClick={() => setIsEditing(true)}>
                Edit Profile
              </Button>
              <Button variant="destructive" onClick={handleLogout}>
                Logout
              </Button>
            </CardFooter>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Account Statistics</CardTitle>
              <CardDescription>
                Your prediction statistics and achievements
              </CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-accent p-4 rounded-lg text-center">
                <p className="text-2xl font-bold">0</p>
                <p className="text-sm text-muted-foreground">Predictions Made</p>
              </div>
              <div className="bg-accent p-4 rounded-lg text-center">
                <p className="text-2xl font-bold">0</p>
                <p className="text-sm text-muted-foreground">Leagues Joined</p>
              </div>
              <div className="bg-accent p-4 rounded-lg text-center">
                <p className="text-2xl font-bold">0</p>
                <p className="text-sm text-muted-foreground">Total Points</p>
              </div>
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
} 