export interface JiraConfig {
    instanceUrl: string;
    email: string;
    apiKey: string;
}
export interface SprintConfig {
    name: string;
    goal?: string;
    startDate: string;
    endDate: string;
    originBoardId: number;
}
export interface JiraIssue {
    id: string;
    key: string;
    fields: {
        summary: string;
        description: string;
        status: {
            name: string;
            statusCategory: {
                key: string;
            };
        };
        priority?: {
            name: string;
        };
        customfield_10016?: number;
    };
}
export interface JiraBoard {
    id: number;
    type: string;
}
export interface JiraBoards {
    values: JiraBoard[];
}
