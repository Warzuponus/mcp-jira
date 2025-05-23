export declare const toolSchemas: {
    jql_search: {
        type: string;
        properties: {
            jql: {
                type: string;
                description: string;
            };
            nextPageToken: {
                type: string;
                description: string;
            };
            maxResults: {
                type: string;
                description: string;
            };
            fields: {
                type: string;
                items: {
                    type: string;
                };
                description: string;
            };
            expand: {
                type: string;
                description: string;
            };
        };
        required: string[];
    };
    get_issue: {
        type: string;
        properties: {
            issueIdOrKey: {
                type: string;
                description: string;
            };
            fields: {
                type: string;
                items: {
                    type: string;
                };
                description: string;
            };
            expand: {
                type: string;
                description: string;
            };
            properties: {
                type: string;
                items: {
                    type: string;
                };
                description: string;
            };
            failFast: {
                type: string;
                description: string;
                default: boolean;
            };
        };
        required: string[];
    };
    create_issue: {
        type: string;
        properties: {
            project: {
                type: string;
                description: string;
            };
            summary: {
                type: string;
                description: string;
            };
            description: {
                type: string;
                description: string;
            };
            issueType: {
                type: string;
                description: string;
            };
            priority: {
                type: string;
                description: string;
            };
            assignee: {
                type: string;
                description: string;
            };
            labels: {
                type: string;
                items: {
                    type: string;
                };
                description: string;
            };
            storyPoints: {
                type: string;
                description: string;
            };
            epic: {
                type: string;
                description: string;
            };
        };
        required: string[];
    };
    plan_sprint: {
        type: string;
        properties: {
            projectKey: {
                type: string;
                description: string;
            };
            sprintName: {
                type: string;
                description: string;
            };
            sprintGoal: {
                type: string;
                description: string;
            };
            startDate: {
                type: string;
                description: string;
            };
            endDate: {
                type: string;
                description: string;
            };
            teamCapacity: {
                type: string;
                description: string;
            };
        };
        required: string[];
    };
};
