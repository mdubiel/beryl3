1. Inparity of displaying data on `/sys/settings`. There are number of tables in view `/sys/settings`, majority of them show information in nice table, however "Installed Applications" and "Middleware" are displayed differently. I suppose "Installed Applications" intention is to display them in tabbed interface, do not do that, list them in table format. Make the lookign the same. Also, on the same view table label (eg. "Static Files Configuration") could have more gap between itself and table below. From same view "Media Storage Statistics" should be gone and move to "Media Browser" or "Metrics".

2. Application Activity. I need to remove completelly this feautre, as it duplicates with logging facility. All these messages, which goes now thru "Application Activity" (what is different from "Recent Activity") have to go thru logging facility, and be available in grafana. Remove this feautre completelly from all views (replace its occourence with appropiate `logging()` call) and remove from `/sys/`. Ensure, there is Grafana dashboard with similar view (table, with important data, not JSON dump).

3. External Services section in SYS sidebar should point also to "resend" service, Adminer, Grafana and other available services we use in this application

4. We are now using cron feautres to proceed email queue. I want to have another view in 'SYS' which will display that queue, together with crontab, and information when it was recently flushed. Also I want to have a button to manually trigger queue processing. Add a link to this view to SYS "System modules" section.

5. HTTPS certificates are not completed. Verify all endpoints are working over SSL, and update NGNIX configuration to use SSL (redirect from plain HTTP when needed)

6. Find all occourences of `example.com`. I think this is used as an example domain. This has to be moved away to env variable. For dev it is: beryl3.localdomain, for stage it is beryl3-stage.mdubiel.org and for production it is beryl.com. Also display this variable in SYS.

7. In SYS, /sys/dashboard, the section 'SYSTEM INFO' is showing invalid information about database.

8.