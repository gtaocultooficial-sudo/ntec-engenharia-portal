# NTEC Engenharia & Geotecnia — Portal

This repository publishes the public frontend for the NTEC portal via GitHub Pages.

- The deployment workflow decodes and validates `site-payload.zip.b64`, extracts the static HTML assets, and publishes them.
- The Supabase publishable key used by the browser is a public client key; access control is enforced by Supabase Auth and database row-level security policies.
- Administrative login is served at `/admin/` under the published website path.
- `database/programming_items.sql` documents the programming table, including proposal/report links, date ranges and parent-molding links.
- `database/proposal_service_schedule.sql` documents the proposal classification fields and idempotent schedule keys. Both migrations have been applied to the NTEC Supabase database.
- In the admin portal, the proposal list can open **Analisar e fechar**. The system suggests monthly, daily or point service from the saved scope, asks an administrator to confirm the project and dates, then approves the proposal and generates linked programming items. Daily items use the selected weekdays; monthly service is split into month-long date ranges. Duplicate generation is prevented by a unique schedule key.
- The GitHub Pages build validates the programming UI scripts before publishing.
- The GitHub Pages site needs to use **GitHub Actions** as its publishing source.
