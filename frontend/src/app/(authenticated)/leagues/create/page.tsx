'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { leaguesService, CreateLeagueData } from '@/services/leagues';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card';
import { Form, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/Form';

const createLeagueSchema = z.object({
  name: z.string().min(3, 'League name must be at least 3 characters').max(50, 'League name cannot exceed 50 characters'),
  description: z.string().max(200, 'Description cannot exceed 200 characters').optional(),
});

type CreateLeagueFormValues = z.infer<typeof createLeagueSchema>;

export default function CreateLeaguePage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<CreateLeagueFormValues>({
    resolver: zodResolver(createLeagueSchema),
    defaultValues: {
      name: '',
      description: '',
    },
  });

  const onSubmit = async (data: CreateLeagueFormValues) => {
    setIsLoading(true);
    setError(null);

    try {
      const leagueData: CreateLeagueData = {
        name: data.name,
        description: data.description || '',
      };

      const league = await leaguesService.createLeague(leagueData);
      router.push(`/leagues/${league.id}`);
    } catch (err: any) {
      console.error('Create league error:', err);
      setError(
        err.response?.data?.error?.message || 
        'Failed to create league. Please try again later.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Create a New League</h1>
        <p className="text-muted-foreground mt-2">
          Create a league to compete with friends and track predictions
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>League Details</CardTitle>
          <CardDescription>
            Enter the details for your new league
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="bg-destructive/15 text-destructive text-sm p-3 rounded-md mb-4">
              {error}
            </div>
          )}
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>League Name</FormLabel>
                    <Input
                      placeholder="My Awesome F1 League"
                      disabled={isLoading}
                      {...field}
                    />
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description (Optional)</FormLabel>
                    <Input
                      placeholder="A brief description of your league"
                      disabled={isLoading}
                      {...field}
                    />
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="flex justify-end space-x-4 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  disabled={isLoading}
                  asChild
                >
                  <Link href="/leagues">Cancel</Link>
                </Button>
                <Button type="submit" isLoading={isLoading}>
                  Create League
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
} 