import api from '@/lib/api';

export interface RaceWeekend {
  id: number;
  year: number;
  round_number: number;
  country: string;
  location: string;
  circuit_name: string;
  session_date: string;
  has_sprint: boolean;
}

export interface RaceWeekendList {
  items: RaceWeekend[];
  total: number;
}

export interface Prediction {
  id: number;
  user_id: number;
  race_weekend_id: number;
  created_at: string;
  updated_at: string | null;
  top_10_prediction: string;
  pole_position: number;
  sprint_winner: number | null;
  most_pit_stops_driver: number;
  fastest_lap_driver: number;
  most_positions_gained: number;
}

export interface PredictionScore {
  id: number;
  prediction_id: number;
  calculated_at: string;
  top_5_score: number;
  position_6_to_10_score: number;
  perfect_top_10_bonus: number;
  partial_position_score: number;
  pole_position_score: number;
  sprint_winner_score: number;
  most_pit_stops_score: number;
  fastest_lap_score: number;
  most_positions_gained_score: number;
  streak_bonus: number;
  underdog_bonus: number;
  total_score: number;
}

export interface CreatePredictionData {
  race_weekend_id: number;
  top_10_prediction: string;
  pole_position: number;
  sprint_winner?: number;
  most_pit_stops_driver: number;
  fastest_lap_driver: number;
  most_positions_gained: number;
}

export interface Driver {
  number: number;
  name: string;
  team: string;
  nationality: string;
  flag_filename: string;
}

export interface DriverList {
  items: Driver[];
}

export const predictionsService = {
  /**
   * Get all race weekends with optional year filter
   */
  async getRaceWeekends(year?: number, skip = 0, limit = 10): Promise<RaceWeekendList> {
    const params = new URLSearchParams();
    if (year) params.append('year', year.toString());
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    
    const response = await api.get<RaceWeekendList>(`/f1/race-weekends/?${params.toString()}`);
    return response.data;
  },

  /**
   * Get the current or next upcoming race weekend
   */
  async getCurrentRaceWeekend(): Promise<RaceWeekend> {
    const response = await api.get<RaceWeekend>('/f1/race-weekends/current/');
    return response.data;
  },

  /**
   * Get a specific race weekend by ID
   */
  async getRaceWeekend(id: number): Promise<RaceWeekend> {
    const response = await api.get<RaceWeekend>(`/f1/race-weekends/${id}`);
    return response.data;
  },

  /**
   * Get upcoming race weekends
   */
  async getUpcomingRaces(): Promise<RaceWeekend[]> {
    const now = new Date();
    const currentYear = now.getFullYear();
    
    // Get race weekends for the current year
    const response = await this.getRaceWeekends(currentYear, 0, 20);
    
    // Filter to only include upcoming races or races happening today
    const upcomingRaces = response.items.filter(race => {
      const raceDate = new Date(race.session_date);
      // Keep races that are today or in the future
      return raceDate.setHours(0, 0, 0, 0) >= now.setHours(0, 0, 0, 0);
    });
    
    // Sort by date (closest first)
    return upcomingRaces.sort((a, b) => 
      new Date(a.session_date).getTime() - new Date(b.session_date).getTime()
    );
  },

  /**
   * Get all predictions for the current user
   */
  async getMyPredictions(): Promise<Prediction[]> {
    const response = await api.get<Prediction[]>('/predictions/my');
    return response.data;
  },

  /**
   * Get a specific prediction by ID
   */
  async getPrediction(id: number): Promise<Prediction> {
    const response = await api.get<Prediction>(`/predictions/${id}`);
    return response.data;
  },

  /**
   * Get predictions for a specific race weekend
   */
  async getPredictionsForRaceWeekend(raceWeekendId: number): Promise<Prediction[]> {
    const response = await api.get<Prediction[]>(`/predictions/race/${raceWeekendId}`);
    return response.data;
  },

  /**
   * Create a new prediction
   */
  async createPrediction(data: CreatePredictionData): Promise<Prediction> {
    const response = await api.post<Prediction>('/predictions', data);
    return response.data;
  },

  /**
   * Update an existing prediction
   */
  async updatePrediction(id: number, data: Partial<CreatePredictionData>): Promise<Prediction> {
    const response = await api.put<Prediction>(`/predictions/${id}`, data);
    return response.data;
  },

  /**
   * Delete a prediction
   */
  async deletePrediction(id: number): Promise<void> {
    await api.delete(`/predictions/${id}`);
  },

  /**
   * Get score for a prediction
   */
  async getPredictionScore(predictionId: number): Promise<PredictionScore> {
    const response = await api.get<PredictionScore>(`/predictions/${predictionId}/score`);
    return response.data;
  },

  /**
   * Get current season drivers
   */
  async getCurrentSeasonDrivers(year?: number): Promise<Driver[]> {
    const params = new URLSearchParams();
    if (year) params.append('year', year.toString());
    
    const response = await api.get<DriverList>(`/f1/drivers/?${params.toString()}`);
    return response.data.items;
  }
}; 