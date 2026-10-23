# NTEC Engenharia & Geotecnia — Portal

This repository publishes the public frontend for the NTEC portal via GitHub Pages.

- The deployment workflow decodes and validates `site-payload.zip.b64`, extracts the static HTML assets, and publishes them.
- The public payload contains only client-side website files. No database setup SQL or Supabase migrations are included.
- The Supabase publishable key used by the browser is a public client key; access control is enforced by Supabase Auth and database row-level security policies.
- Administrative login is served at `/admin/` under the published website path.

The GitHub Pages site needs to use **GitHub Actions** as its publishing source.
