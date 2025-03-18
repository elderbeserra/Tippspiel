'use client';

import { useParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { leaguesService } from '@/services/leagues';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { ArrowLeftIcon, TrophyIcon } from '@heroicons/react/24/outline';

export default function LeagueStandingsPage() {
  const params = useParams();
  const router = useRouter();
  const leagueId = Number(params.id);

  const { data, isLoading, error } = useQuery({
    queryKey: ['league-standings', leagueId],
    queryFn: () => leaguesService.getLeagueStandings(leagueId),
    enabled: !isNaN(leagueId),
  });

  const { data: leagueDetails } = useQuery({
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
        <h1 className="text-3xl font-bold">League Standings</h1>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      ) : error ? (
        <div className="bg-destructive/15 text-destructive text-sm p-4 rounded-md">
          Failed to load league standings. Please try again later.
        </div>
      ) : data ? (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <TrophyIcon className="h-5 w-5" />
              {data.league_name} Standings
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Last updated: {new Date(data.last_updated).toLocaleString()}
            </p>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4">Position</th>
                    <th className="text-left py-3 px-4">User</th>
                    <th className="text-right py-3 px-4">Points</th>
                    <th className="text-right py-3 px-4">Predictions</th>
                    <th className="text-right py-3 px-4">Perfect</th>
                  </tr>
                </thead>
                <tbody>
                  {data.standings.map((standing) => (
                    <tr key={standing.user_id} className="border-b hover:bg-muted/50">
                      <td className="py-3 px-4">
                        <div className="flex items-center">
                          {standing.position === 1 && (
                            <span className="text-yellow-500 mr-1">🥇</span>
                          )}
                          {standing.position === 2 && (
                            <span className="text-gray-400 mr-1">🥈</span>
                          )}
                          {standing.position === 3 && (
                            <span className="text-amber-700 mr-1">🥉</span>
                          )}
                          {standing.position > 3 && (
                            <span className="mr-1">{standing.position}.</span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">{standing.username}</td>
                      <td className="py-3 px-4 text-right font-medium">{standing.total_points}</td>
                      <td className="py-3 px-4 text-right">{standing.predictions_made}</td>
                      <td className="py-3 px-4 text-right">{standing.perfect_predictions}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
} 