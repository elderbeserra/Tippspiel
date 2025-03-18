'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { leaguesService } from '@/services/leagues';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { ArrowLeftIcon, TrophyIcon, UserPlusIcon, UserMinusIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

export default function LeagueDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const leagueId = Number(params.id);
  const [isAddingMember, setIsAddingMember] = useState(false);

  const { data: league, isLoading, error } = useQuery({
    queryKey: ['league', leagueId],
    queryFn: () => leaguesService.getLeague(leagueId),
    enabled: !isNaN(leagueId),
  });

  const handleBack = () => {
    router.back();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" onClick={handleBack}>
          <ArrowLeftIcon className="h-4 w-4" />
        </Button>
        <h1 className="text-3xl font-bold">League Details</h1>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      ) : error ? (
        <div className="bg-destructive/15 text-destructive text-sm p-4 rounded-md">
          Failed to load league details. Please try again later.
        </div>
      ) : league ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>{league.name}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-medium mb-1">League Information</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="text-muted-foreground">Created</div>
                  <div>{new Date(league.created_at).toLocaleDateString()}</div>
                  <div className="text-muted-foreground">Members</div>
                  <div>{league.member_count}</div>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 pt-4">
                <Button asChild>
                  <Link href={`/leagues/${leagueId}/standings`}>
                    <TrophyIcon className="h-4 w-4 mr-2" />
                    View Standings
                  </Link>
                </Button>
                <Button variant="outline">
                  <UserPlusIcon className="h-4 w-4 mr-2" />
                  Invite Member
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-start" asChild>
                <Link href={`/leagues/${leagueId}/standings`}>
                  <TrophyIcon className="h-4 w-4 mr-2" />
                  View Standings
                </Link>
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <UserPlusIcon className="h-4 w-4 mr-2" />
                Invite Member
              </Button>
              <Button variant="outline" className="w-full justify-start">
                <ArrowPathIcon className="h-4 w-4 mr-2" />
                Transfer Ownership
              </Button>
              <Button variant="destructive" className="w-full justify-start">
                <UserMinusIcon className="h-4 w-4 mr-2" />
                Leave League
              </Button>
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  );
} 