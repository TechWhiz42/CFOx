# CFOx Release Checklist

## Before deployment

- [ ] `pytest` passes in the backend virtual environment.
- [ ] `npm run build` passes in the frontend.
- [ ] `.env.production` has been created from the template.
- [ ] All placeholder secrets have been replaced.
- [ ] `.env.production` is ignored by Git.
- [ ] `docker compose -f docker-compose.production.yml config` passes.
- [ ] Docker daemon is reachable.
- [ ] Database credentials are valid.
- [ ] Database is not publicly exposed.
- [ ] Production domain/origin is configured for the frontend API.
- [ ] A database backup/rollback plan exists.

## Deployment

1. Validate the Compose configuration.
2. Build images.
3. Start the database.
4. Wait for the database health check.
5. Apply Alembic migrations.
6. Start/recreate backend and frontend.
7. Run smoke tests.
8. Inspect service status and recent logs.

Docker Compose supports production use on a single host; production configurations commonly use health checks and `depends_on` conditions so an application does not assume a dependency is ready merely because its container has started.

## Rollback

Keep the previous image/version available.

If a release fails:

1. Stop the affected application service.
2. Restore the previous application image/version.
3. Roll back the database only when the migration is known to be reversible and rollback is required.
4. Run smoke tests.
5. Inspect logs.
