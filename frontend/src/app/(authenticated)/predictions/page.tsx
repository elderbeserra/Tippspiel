'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { predictionsService, RaceWeekend } from '@/services/predictions';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card';
import { CalendarIcon, ClockIcon, MapPinIcon } from '@heroicons/react/24/outline';

export default function PredictionsPage() {
  const { data: races, isLoading, error } = useQuery({
    queryKey: ['upcoming-races'],
    queryFn: () => predictionsService.getUpcomingRaces(),
  });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Calculate prediction deadline (24 hours before race)
  const getPredictionDeadline = (race: RaceWeekend): Date => {
    const raceDate = new Date(race.session_date);
    const deadline = new Date(raceDate);
    deadline.setHours(deadline.getHours() - 24);
    return deadline;
  };

  const isPredictionDeadlinePassed = (race: RaceWeekend): boolean => {
    const deadline = getPredictionDeadline(race);
    const now = new Date();
    return deadline < now;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Predictions</h1>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        </div>
      ) : error ? (
        <div className="bg-destructive/15 text-destructive text-sm p-4 rounded-md">
          Failed to load upcoming races. Please try again later.
        </div>
      ) : races && races.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {races.map((race) => {
            const deadline = getPredictionDeadline(race);
            return (
              <Card key={race.id} className="overflow-hidden">
                <CardHeader className="pb-3">
                  <CardTitle>{race.country} Grand Prix</CardTitle>
                  <CardDescription>Round {race.round_number}</CardDescription>
                </CardHeader>
                <CardContent className="pb-3 space-y-3">
                  <div className="flex items-center text-sm">
                    <MapPinIcon className="h-4 w-4 mr-2" />
                    <span>{race.circuit_name}, {race.country}</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CalendarIcon className="h-4 w-4 mr-2" />
                    <span>{formatDate(race.session_date)}</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <ClockIcon className="h-4 w-4 mr-2" />
                    <span>{formatTime(race.session_date)}</span>
                  </div>
                  <div className="text-sm">
                    <span className="font-medium">Prediction deadline:</span>{' '}
                    <span className={isPredictionDeadlinePassed(race) ? 'text-destructive' : ''}>
                      {formatDate(deadline.toISOString())} {formatTime(deadline.toISOString())}
                    </span>
                  </div>
                </CardContent>
                <CardFooter className="flex justify-end pt-3 border-t">
                  {isPredictionDeadlinePassed(race) ? (
                    <Button variant="outline" size="sm" disabled>
                      Deadline Passed
                    </Button>
                  ) : (
                    <Button size="sm" asChild>
                      <Link href={`/predictions/${race.id}`}>Make Prediction</Link>
                    </Button>
                  )}
                </CardFooter>
              </Card>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-12">
          <h3 className="text-xl font-medium mb-2">No upcoming races</h3>
          <p className="text-muted-foreground mb-6">
            Check back later for upcoming races
          </p>
        </div>
      )}
    </div>
  );
} 