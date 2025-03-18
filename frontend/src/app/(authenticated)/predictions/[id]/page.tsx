'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { predictionsService, RaceWeekend, CreatePredictionData, Driver } from '@/services/predictions';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card';
import { Form, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/Form';
import { CalendarIcon, ClockIcon, MapPinIcon } from '@heroicons/react/24/outline';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { DriverGrid } from '@/components/DriverGrid';
import { Alert, AlertCircle, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { toast } from 'react-hot-toast';

// FormControl component
const FormControl = ({ children }: { children: React.ReactNode }) => {
  return <div className="mt-1">{children}</div>;
};

// Validation schema for prediction form
const predictionSchema = z.object({
  top_10_prediction: z.string()
    .min(1, 'Top 10 prediction is required')
    .regex(/^\d+(,\d+){9}$/, 'Must be 10 comma-separated driver numbers'),
  pole_position: z.string().min(1, 'Pole position driver is required'),
  sprint_winner: z.string().optional(),
  most_pit_stops_driver: z.string().min(1, 'Most pit stops driver is required'),
  fastest_lap_driver: z.string().min(1, 'Fastest lap driver is required'),
  most_positions_gained: z.string().min(1, 'Most positions gained driver is required'),
});

type PredictionFormValues = z.infer<typeof predictionSchema>;

export default function PredictionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const raceId = Number(params.id);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

  // Fetch race weekend details
  const { data: race, isLoading: isLoadingRace } = useQuery({
    queryKey: ['race-weekend', raceId],
    queryFn: () => predictionsService.getRaceWeekend(raceId),
    enabled: !isNaN(raceId),
  });

  // Fetch current season drivers
  const { data: drivers, isLoading: isLoadingDrivers } = useQuery({
    queryKey: ['drivers', race?.year],
    queryFn: () => predictionsService.getCurrentSeasonDrivers(race?.year),
    enabled: !!race?.year,
  });

  // Form setup
  const form = useForm<PredictionFormValues>({
    resolver: zodResolver(predictionSchema),
    defaultValues: {
      top_10_prediction: '',
      pole_position: '',
      sprint_winner: '',
      most_pit_stops_driver: '',
      fastest_lap_driver: '',
      most_positions_gained: '',
    },
  });

  // Create prediction mutation
  const createPrediction = useMutation({
    mutationFn: (data: CreatePredictionData) => predictionsService.createPrediction(data),
    onSuccess: () => {
      toast.success('Prediction created successfully!');
      router.push('/predictions');
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to submit prediction');
      setSubmitting(false);
    },
  });

  // Handle form submission
  const onSubmit = (values: PredictionFormValues) => {
    setSubmitting(true);
    setError(null);

    const predictionData: CreatePredictionData = {
      race_weekend_id: raceId,
      top_10_prediction: values.top_10_prediction,
      pole_position: Number(values.pole_position),
      most_pit_stops_driver: Number(values.most_pit_stops_driver),
      fastest_lap_driver: Number(values.fastest_lap_driver),
      most_positions_gained: Number(values.most_positions_gained),
    };

    // Add sprint winner if provided and race has sprint
    if (race?.has_sprint && values.sprint_winner) {
      predictionData.sprint_winner = Number(values.sprint_winner);
    }

    createPrediction.mutate(predictionData);
  };

  // Format date and time
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

  if (isLoadingRace || isLoadingDrivers) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!race) {
    return (
      <div className="bg-destructive/15 text-destructive text-sm p-4 rounded-md">
        Race weekend not found.
      </div>
    );
  }

  // Check if prediction deadline has passed
  if (isPredictionDeadlinePassed(race)) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Make Prediction</h1>
        <Card>
          <CardHeader>
            <CardTitle>{race.country} Grand Prix</CardTitle>
            <CardDescription>Round {race.round_number}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-destructive/15 text-destructive text-sm p-4 rounded-md">
              The prediction deadline for this race has passed.
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Use fetched drivers or fallback to empty array
  const driverOptions = drivers || [];

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Make Prediction</h1>
      
      <Card className="mb-6">
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
            {formatDate(getPredictionDeadline(race).toISOString())} {formatTime(getPredictionDeadline(race).toISOString())}
          </div>
        </CardContent>
      </Card>

      {error && (
        <div className="bg-destructive/15 text-destructive text-sm p-4 rounded-md mb-6">
          {error}
        </div>
      )}

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
          <Card>
            <CardHeader>
              <CardTitle>Top 10 Prediction</CardTitle>
              <CardDescription>
                Select the drivers you predict will finish in the top 10 positions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DriverGrid
                drivers={driverOptions}
                selectedDriver={Number(form.watch('top_10_prediction').split(',')[0])}
                onSelect={(driverNumber: number) => {
                  const currentSelection = form.watch('top_10_prediction').split(',').filter(Boolean);
                  if (currentSelection.length < 10) {
                    form.setValue('top_10_prediction', [...currentSelection, driverNumber].join(','));
                  }
                }}
                title="Select Drivers"
                description="Click on drivers to select them in order (up to 10)"
                isExpanded={expandedCategory === 'top10'}
                onToggleExpand={() => setExpandedCategory(expandedCategory === 'top10' ? null : 'top10')}
              />
              <FormField
                name="top_10_prediction"
                render={({ field }) => (
                  <FormItem className="mt-4">
                    <FormControl>
                      <input type="hidden" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Pole Position</CardTitle>
              <CardDescription>
                Select the driver you predict will get pole position
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DriverGrid
                drivers={driverOptions}
                selectedDriver={Number(form.watch('pole_position'))}
                onSelect={(driverNumber: number) => form.setValue('pole_position', driverNumber.toString())}
                title="Select Driver"
                isExpanded={expandedCategory === 'pole'}
                onToggleExpand={() => setExpandedCategory(expandedCategory === 'pole' ? null : 'pole')}
              />
              <FormField
                name="pole_position"
                render={({ field }) => (
                  <FormItem className="mt-4">
                    <FormControl>
                      <input type="hidden" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {race.has_sprint && (
            <Card>
              <CardHeader>
                <CardTitle>Sprint Winner</CardTitle>
                <CardDescription>
                  Select the driver you predict will win the sprint race
                </CardDescription>
              </CardHeader>
              <CardContent>
                <DriverGrid
                  drivers={driverOptions}
                  selectedDriver={Number(form.watch('sprint_winner'))}
                  onSelect={(driverNumber: number) => form.setValue('sprint_winner', driverNumber.toString())}
                  title="Select Driver"
                  isExpanded={expandedCategory === 'sprint'}
                  onToggleExpand={() => setExpandedCategory(expandedCategory === 'sprint' ? null : 'sprint')}
                />
                <FormField
                  name="sprint_winner"
                  render={({ field }) => (
                    <FormItem className="mt-4">
                      <FormControl>
                        <input type="hidden" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Most Pit Stops</CardTitle>
              <CardDescription>
                Select the driver you predict will make the most pit stops
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DriverGrid
                drivers={driverOptions}
                selectedDriver={Number(form.watch('most_pit_stops_driver'))}
                onSelect={(driverNumber: number) => form.setValue('most_pit_stops_driver', driverNumber.toString())}
                title="Select Driver"
                isExpanded={expandedCategory === 'pitstops'}
                onToggleExpand={() => setExpandedCategory(expandedCategory === 'pitstops' ? null : 'pitstops')}
              />
              <FormField
                name="most_pit_stops_driver"
                render={({ field }) => (
                  <FormItem className="mt-4">
                    <FormControl>
                      <input type="hidden" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Fastest Lap</CardTitle>
              <CardDescription>
                Select the driver you predict will set the fastest lap
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DriverGrid
                drivers={driverOptions}
                selectedDriver={Number(form.watch('fastest_lap_driver'))}
                onSelect={(driverNumber: number) => form.setValue('fastest_lap_driver', driverNumber.toString())}
                title="Select Driver"
                isExpanded={expandedCategory === 'fastestlap'}
                onToggleExpand={() => setExpandedCategory(expandedCategory === 'fastestlap' ? null : 'fastestlap')}
              />
              <FormField
                name="fastest_lap_driver"
                render={({ field }) => (
                  <FormItem className="mt-4">
                    <FormControl>
                      <input type="hidden" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Most Positions Gained</CardTitle>
              <CardDescription>
                Select the driver you predict will gain the most positions during the race
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DriverGrid
                drivers={driverOptions}
                selectedDriver={Number(form.watch('most_positions_gained'))}
                onSelect={(driverNumber: number) => form.setValue('most_positions_gained', driverNumber.toString())}
                title="Select Driver"
                isExpanded={expandedCategory === 'positions'}
                onToggleExpand={() => setExpandedCategory(expandedCategory === 'positions' ? null : 'positions')}
              />
              <FormField
                name="most_positions_gained"
                render={({ field }) => (
                  <FormItem className="mt-4">
                    <FormControl>
                      <input type="hidden" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          <Button type="submit" disabled={submitting}>
            {submitting ? 'Submitting...' : 'Submit Prediction'}
          </Button>
        </form>
      </Form>
    </div>
  );
} 