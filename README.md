# NTEC Engenharia & Geotecnia — Portal

This repository publishes the public frontend for the NTEC portal via GitHub Pages.

- The deployment workflow decodes and validates `site-payload.zip.b64`, extracts the static HTML assets, and publishes them.
- The Supabase publishable key used by the browser is a public client key; access control is enforced by Supabase Auth and database row-level security policies.
- Administrative login is served at `/admin/` under the published website path.
- `database/programming_items.sql` is an incremental schema script for the planned programming module. It is not yet applied to the production Supabase database, and the programming interface must not be enabled until this migration has been applied and verified.
- The GitHub Pages site needs to use **GitHub Actions** as its publishing source.
