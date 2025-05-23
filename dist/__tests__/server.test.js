"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const server_1 = require("../server");
describe('JiraServer', () => {
    const mockConfig = {
        instanceUrl: 'https://test.atlassian.net',
        email: 'test@example.com',
        apiKey: 'test-token'
    };
    let server;
    beforeEach(() => {
        server = new server_1.JiraServer(mockConfig);
    });
    describe('getTools', () => {
        it('should return list of available tools', () => {
            const tools = server.getTools();
            expect(tools.length).toBeGreaterThan(0);
            expect(tools[0]).toHaveProperty('name');
            expect(tools[0]).toHaveProperty('schema');
        });
    });
    describe('jqlSearch', () => {
        it('should search for issues using JQL', async () => {
            // Add test implementation
        });
    });
    describe('getIssue', () => {
        it('should fetch issue details', async () => {
            // Add test implementation
        });
    });
    describe('createIssue', () => {
        it('should create a new issue', async () => {
            // Add test implementation
        });
    });
});
