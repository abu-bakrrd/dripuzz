import { spawn } from 'child_process';

// Start Flask application
const flask = spawn('python', ['app.py'], {
  stdio: 'inherit',
  env: process.env
});

flask.on('error', (error) => {
  console.error(`Failed to start Flask: ${error.message}`);
  process.exit(1);
});

flask.on('exit', (code) => {
  console.log(`Flask process exited with code ${code}`);
  process.exit(code || 0);
});

// Handle termination signals
process.on('SIGTERM', () => {
  flask.kill('SIGTERM');
});

process.on('SIGINT', () => {
  flask.kill('SIGINT');
});
