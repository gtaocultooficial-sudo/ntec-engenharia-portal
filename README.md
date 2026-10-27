# NTEC Engenharia & Geotecnia — Portal

This repository publishes the public frontend for the NTEC portal via GitHub Pages.

- The deployment workflow decodes and validates `site-payload.zip.b64`, extracts the static HTML assets, and publishes them.
- The Supabase publishable key used by the browser is a public client key; access control is enforced by Supabase Auth and database row-level security policies.
- Administrative login is served at `/admin/` under the published website path.
- `database/programming_items.sql` documents the schema for the programming module, including proposal, report and parent-molding links. The production Supabase database has the `public.programming_items` table, row-level security, and self-reference support for generated rupture activities. The GitHub Pages build validates the programming UI scripts before publishing.
- The GitHub Pages site needs to use **GitHub Actions** as its publishing source.
