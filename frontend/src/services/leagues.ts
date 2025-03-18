import api from '@/lib/api';

export interface League {
  id: number;
  name: string;
  owner_id: number;
  created_at: string;
  member_count: number;
}

export interface LeagueDetail extends League {
  members: LeagueMember[];
}

export interface LeagueMember {
  id: number;
  username: string;
  email: string;
}

export interface LeagueStanding {
  user_id: number;
  username: string;
  total_points: number;
  position: number;
  predictions_made: number;
  perfect_predictions: number;
}

export interface LeagueStandingsResponse {
  league_id: number;
  league_name: string;
  standings: LeagueStanding[];
  last_updated: string;
}

export interface CreateLeagueData {
  name: string;
  icon?: string;
}

export const leaguesService = {
  /**
   * Get all leagues for the current user
   */
  async getMyLeagues(): Promise<League[]> {
    const response = await api.get<League[]>('/leagues/my');
    return response.data;
  },

  /**
   * Get a specific league by ID
   */
  async getLeague(id: number): Promise<League> {
    const response = await api.get<League>(`/leagues/${id}`);
    return response.data;
  },

  /**
   * Get standings for a league
   */
  async getLeagueStandings(id: number): Promise<LeagueStandingsResponse> {
    const response = await api.get<LeagueStandingsResponse>(`/leagues/${id}/standings`);
    return response.data;
  },

  /**
   * Create a new league
   */
  async createLeague(data: CreateLeagueData): Promise<League> {
    const response = await api.post<League>('/leagues', data);
    return response.data;
  },

  /**
   * Add a member to a league
   */
  async addMember(leagueId: number, userId: number): Promise<void> {
    await api.post(`/leagues/${leagueId}/members/${userId}`);
  },

  /**
   * Remove a member from a league
   */
  async removeMember(leagueId: number, userId: number): Promise<void> {
    await api.delete(`/leagues/${leagueId}/members/${userId}`);
  },

  /**
   * Delete a league
   */
  async deleteLeague(id: number): Promise<void> {
    await api.delete(`/leagues/${id}`);
  },

  /**
   * Transfer ownership of a league
   */
  async transferOwnership(leagueId: number, newOwnerId: number): Promise<void> {
    await api.put(`/leagues/${leagueId}/transfer-ownership/${newOwnerId}`);
  },
}; 