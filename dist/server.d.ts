import { BaseServer } from '@modelcontextprotocol/sdk';
import type { Tool } from '@modelcontextprotocol/sdk';
import { JiraConfig } from './types';
export declare class JiraServer extends BaseServer {
    private jira;
    private projectCache;
    constructor(config: JiraConfig);
    getTools(): Tool[];
    executeTool(name: string, args: Record<string, unknown>): Promise<Tool.Response>;
    private jqlSearch;
    private getIssue;
    private createIssue;
    private planSprint;
}
