export interface JiraConfig {
  protocol: string;
  host: string;
  username: string;
  password: string;
  apiVersion: string;
}

export interface SprintPlanningInput {
  projectKey: string;
  sprintName: string;
  sprintGoal: string;
  startDate: string;
  endDate: string;
  teamCapacity: number;
}