# Task Daemon

The task daemon is a persistent process that runs scheduled tasks with full Claude context.

## Starting the daemon

```bash
./task_daemon.sh start
```

## Checking status

```bash
./task_daemon.sh status
```

## Viewing logs

```bash
./task_daemon.sh logs
```

## Stopping the daemon

```bash
./task_daemon.sh stop
```

## Auto-start on boot

Add this to your shell profile or startup scripts:

```bash
/Users/claudemini/Claude/Code/utils/task_daemon.sh start
```

The daemon will:
- Load CLAUDE.md context
- Set up environment variables from .env
- Execute scheduled tasks from the database
- Run with a 60-second tick interval
- Handle errors gracefully
- Log all activity to logs/task_daemon.log