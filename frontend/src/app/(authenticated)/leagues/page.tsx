'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { leaguesService } from '@/services/leagues';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card';
import { PlusIcon, TrophyIcon, UsersIcon } from '@heroicons/react/24/outline';

export default function LeaguesPage() {
  const [isCreatingLeague, setIsCreatingLeague] = useState(false);

  const { data: leagues, isLoading, error } = useQuery({
    queryKey: ['leagues'],
    queryFn: () => leaguesService.getMyLeagues(),
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">My Leagues</h1>
        <Button onClick={() => setIsCreatingLeague(true)} asChild>
          <Link href="/leagues/create">
            <PlusIcon className="h-4 w-4 mr-2" />
            Create League
          </Link>
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      ) : error ? (
        <div className="bg-destructive/15 text-destructive text-sm p-4 rounded-md">
          Failed to load leagues. Please try again later.
        </div>
      ) : leagues && leagues.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {leagues.map((league) => (
            <Card key={league.id} className="overflow-hidden">
              <CardHeader className="pb-3">
                <CardTitle>{league.name}</CardTitle>
                <CardDescription>
                  Created on {new Date(league.created_at).toLocaleDateString()}
                </CardDescription>
              </CardHeader>
              <CardContent className="pb-3">
                <div className="flex items-center text-sm text-muted-foreground">
                  <UsersIcon className="h-4 w-4 mr-1" />
                  <span>{league.member_count} members</span>
                </div>
                {league.description && (
                  <p className="mt-2 text-sm">{league.description}</p>
                )}
              </CardContent>
              <CardFooter className="flex justify-between pt-3 border-t">
                <Button variant="outline" size="sm" asChild>
                  <Link href={`/leagues/${league.id}/standings`}>
                    <TrophyIcon className="h-4 w-4 mr-1" />
                    Standings
                  </Link>
                </Button>
                <Button size="sm" asChild>
                  <Link href={`/leagues/${league.id}`}>View Details</Link>
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <h3 className="text-xl font-medium mb-2">No leagues yet</h3>
          <p className="text-muted-foreground mb-6">
            Create your first league or join an existing one
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button asChild>
              <Link href="/leagues/create">
                <PlusIcon className="h-4 w-4 mr-2" />
                Create League
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/leagues/join">Join League</Link>
            </Button>
          </div>
        </div>
      )}
    </div>
  );
} 