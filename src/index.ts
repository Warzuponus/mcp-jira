import { createServer } from './server';

export { JiraMCPServer, createServer } from './server';

// Read configuration from environment variables
const config = {
  protocol: process.env.JIRA_PROTOCOL || 'https',
  host: process.env.JIRA_HOST,
  username: process.env.JIRA_USERNAME,
  password: process.env.JIRA_API_TOKEN,
  apiVersion: process.env.JIRA_API_VERSION || '2'
};

// Create and start server if this file is run directly
if (require.main === module) {
  const server = createServer(config);
  server.start();
}