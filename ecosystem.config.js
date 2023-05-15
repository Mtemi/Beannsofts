module.exports = {
  "apps": [{
    "name": "api3commas",
    "script": "manage.py",
    "args": ["run", "--port", "3010", "--host", "0.0.0.0"],
    "instances": "1",
    "wait_ready": true,
    "autorestart": true,
    "max_restarts": 5,
    "interpreter" : "venv/bin/python",
  },
  {
    "name": "api-3c-Celery",
    "cwd": ".",
    "script": "venv/bin/python3",
    "args": "-m celery -A app.tasks.celery worker -l INFO -B",
    "instances": "1",
    "wait_ready": true,
    "autorestart": true,
    "max_restarts": 5
  },
  {
    "name": "3commasTelegramBot",
    "script": "bot.py",
    "interpreter" : "venv/bin/python3",
  }]
};
