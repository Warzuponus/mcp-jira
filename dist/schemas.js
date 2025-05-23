"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.toolSchemas = void 0;
exports.toolSchemas = {
    jql_search: {
        type: 'object',
        properties: {
            jql: { type: 'string', description: 'JQL query string' },
            nextPageToken: {
                type: 'string',
                description: 'Token for next page'
            },
            maxResults: {
                type: 'integer',
                description: 'Maximum results to fetch'
            },
            fields: {
                type: 'array',
                items: { type: 'string' },
                description: 'List of fields to return for each issue'
            },
            expand: {
                type: 'string',
                description: 'Additional info to include in the response'
            }
        },
        required: ['jql']
    },
    get_issue: {
        type: 'object',
        properties: {
            issueIdOrKey: {
                type: 'string',
                description: 'ID or key of the issue'
            },
            fields: {
                type: 'array',
                items: { type: 'string' },
                description: 'Fields to include in the response'
            },
            expand: {
                type: 'string',
                description: 'Additional information to include in the response'
            },
            properties: {
                type: 'array',
                items: { type: 'string' },
                description: 'Properties to include in the response'
            },
            failFast: {
                type: 'boolean',
                description: 'Fail quickly on errors',
                default: false
            }
        },
        required: ['issueIdOrKey']
    },
    // Our additional tool schemas
    create_issue: {
        type: 'object',
        properties: {
            project: { type: 'string', description: 'Project key' },
            summary: { type: 'string', description: 'Issue summary' },
            description: { type: 'string', description: 'Issue description' },
            issueType: { type: 'string', description: 'Type of issue' },
            priority: { type: 'string', description: 'Issue priority' },
            assignee: { type: 'string', description: 'Assignee username' },
            labels: {
                type: 'array',
                items: { type: 'string' },
                description: 'Issue labels'
            },
            storyPoints: { type: 'number', description: 'Story points estimate' },
            epic: { type: 'string', description: 'Epic link' }
        },
        required: ['project', 'summary', 'issueType']
    },
    plan_sprint: {
        type: 'object',
        properties: {
            projectKey: { type: 'string', description: 'Project key' },
            sprintName: { type: 'string', description: 'Sprint name' },
            sprintGoal: { type: 'string', description: 'Sprint goal' },
            startDate: { type: 'string', description: 'Sprint start date' },
            endDate: { type: 'string', description: 'Sprint end date' },
            teamCapacity: { type: 'number', description: 'Team capacity in story points' }
        },
        required: ['projectKey', 'sprintName', 'startDate', 'endDate', 'teamCapacity']
    }
};
