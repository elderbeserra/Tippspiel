import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card';

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center space-y-12 py-12">
      <section className="w-full max-w-5xl text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          Formula 1 Prediction Game
        </h1>
        <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
          Predict race outcomes, compete with friends, and climb the leaderboard in our F1 prediction game.
        </p>
        <div className="flex flex-wrap justify-center gap-4 mt-8">
          <Button size="lg" asChild>
            <Link href="/register">Get Started</Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link href="/login">Sign In</Link>
          </Button>
        </div>
      </section>

      <section className="w-full max-w-5xl py-12">
        <h2 className="text-3xl font-bold text-center mb-8">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>1. Make Predictions</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                Predict the top 10 finishers, pole position, fastest lap, and more for each F1 race weekend.
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>2. Score Points</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                Earn points based on the accuracy of your predictions. The more accurate, the more points you score.
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>3. Compete in Leagues</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                Create or join private leagues to compete with friends, family, or colleagues throughout the season.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      <section className="w-full max-w-5xl py-12 bg-accent rounded-lg p-8">
        <div className="text-center space-y-4">
          <h2 className="text-3xl font-bold">Ready to Test Your F1 Knowledge?</h2>
          <p className="text-xl">
            Join thousands of F1 fans making predictions for every race weekend.
          </p>
          <Button size="lg" className="mt-4" asChild>
            <Link href="/register">Create Your Account</Link>
          </Button>
        </div>
      </section>

      <section className="w-full max-w-5xl py-12">
        <h2 className="text-3xl font-bold text-center mb-8">Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Real-time Results</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                See your scores update in real-time as race results come in.
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Detailed Statistics</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                Track your prediction accuracy and performance over time with detailed statistics.
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Private Leagues</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                Create private leagues and invite friends to compete throughout the season.
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Season-long Competition</CardTitle>
            </CardHeader>
            <CardContent>
              <p>
                Compete for the championship with season-long points accumulation.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
