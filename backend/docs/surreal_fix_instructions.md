SurrealDB Namespace Permission Troubleshooting
===========================================

If you see IAM/permission errors like "Not enough permissions to perform this action" when the backend attempts to CREATE records, the namespace-level user configured in Cloud Run likely lacks the required RBAC scope for INSERT/CREATE operations.

Options to fix
--------------

1) Create or promote a namespace-level user with appropriate permissions

Use the SurrealDB Cloud Console or the SurrealQL HTTP API to create a user scoped to your namespace and grant it rights. Below are example SurrealQL commands you can run in the SurrealDB Cloud Console (or via the `surreal` CLI connected to your instance):

-- Sign in as an admin/root user (in the Cloud Console you already are)
CREATE user SET email = "service@yourdomain.com", password = "S3rv1ceP@ss!"

-- Create a role with permissions for creating users and other records
DEFINE ROLE "clipstream-service" ON namespace::clipstream
  PERMIT create, select, update, delete ON TABLE user,
  PERMIT create, select, update, delete ON TABLE video,
  PERMIT create, select, update, delete ON TABLE earning
;

-- Grant the role to the service user (you may need to find the user id returned by CREATE)
GRANT clipstream-service TO user:service@yourdomain.com;

Note: SurrealDB's RBAC/roles syntax may vary based on version. Use the Cloud Console UI to manage roles if in doubt.

2) Use an admin/user that already has full namespace permissions

If you already have a namespace-level user that functions as an admin, make sure the Cloud Run service has SURREALDB_USER and SURREALDB_PASS set to that user's credentials. Update the Cloud Run service environment variables and redeploy.

Update Cloud Run env vars (gcloud)
----------------------------------

gcloud run services update <SERVICE_NAME> \
  --region=<REGION> \
  --set-env-vars=SURREALDB_USER=service@yourdomain.com,SURREALDB_PASS="S3rv1ceP@ss!",SURREALDB_NS=clipstream,SURREALDB_DB=production

Replace <SERVICE_NAME> and <REGION> with your Cloud Run values. Alternatively, change the `cloudbuild.yaml` and re-run the build/deploy pipeline.

3) Test the fix
---------------

- Redeploy Cloud Run or restart the service after changing env vars.
- Trigger the OAuth flow in your dev/staging environment and inspect Cloud Run logs for successful user creation: look for logs indicating `User created:` and absence of `IAM error` messages.
- You can also run a quick curl test against a protected endpoint that creates a user (or use the backend admin endpoints) to verify CREATE works.

If you want, I can prepare exact SurrealQL statements for the Cloud Console if you tell me whether you're using the Cloud Console UI or the `surreal` CLI and what admin user you have available.
