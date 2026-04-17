# envctl

A CLI tool to manage and sync environment variables across local, staging, and production configs.

---

## Installation

```bash
pip install envctl
```

Or install from source:

```bash
git clone https://github.com/yourname/envctl.git
cd envctl && pip install -e .
```

---

## Usage

```bash
# Initialize envctl in your project
envctl init

# Set a variable for a specific environment
envctl set DATABASE_URL postgres://localhost/mydb --env local
envctl set DATABASE_URL postgres://prod-host/mydb --env production

# Get a variable
envctl get DATABASE_URL --env production

# Sync variables from local to staging
envctl sync --from local --to staging

# List all variables for an environment
envctl list --env staging

# Pull a remote config into your local .env file
envctl pull --env production --output .env
```

Config files are stored in `.envctl/` at your project root. Each environment is tracked separately, making it easy to diff and audit changes across deployments.

---

## Configuration

envctl stores environment configs in `.envctl/<environment>.env`. Add `.envctl/production.env` to your `.gitignore` to avoid committing sensitive values.

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss any major changes.

---

## License

[MIT](LICENSE)