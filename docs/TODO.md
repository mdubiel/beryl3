1. ✅ **COMPLETED** - Inparity of displaying data on `/sys/settings`. There are number of tables in view `/sys/settings`, majority of them show information in nice table, however "Installed Applications" and "Middleware" are displayed differently. I suppose "Installed Applications" intention is to display them in tabbed interface, do not do that, list them in table format. Make the lookign the same. Also, on the same view table label (eg. "Static Files Configuration") could have more gap between itself and table below. From same view "Media Storage Statistics" should be gone and move to "Media Browser" or "Metrics".

2. ✅ **COMPLETED** - Application Activity. I need to remove completelly this feautre, as it duplicates with logging facility. All these messages, which goes now thru "Application Activity" (what is different from "Recent Activity") have to go thru logging facility, and be available in grafana. Remove this feautre completelly from all views (replace its occourence with appropiate `logging()` call) and remove from `/sys/`. Ensure, there is Grafana dashboard with similar view (table, with important data, not JSON dump).

3. ✅ **COMPLETED** - External Services section in SYS sidebar should point also to "resend" service, Adminer, Grafana and other available external services we use in this application

4. ✅ **COMPLETED** - We are now using cron feautres to proceed email queue. I want to have another view in 'SYS' which will display that queue, together with crontab, and information when it was recently flushed. Also I want to have a button to manually trigger queue processing. Add a link to this view to SYS "System modules" section.

5. ✅ **COMPLETED** - External services sidenav section in SYS is missing links to other services like Resend, Graphana or adminer. Add them to this section, similar to others. It might require changing condition statements. 

6. ✅ **COMPLETED** - When accessing `/sys/email-queue` I got Error 500.

7. ✅ **COMPLETED** - HTTPS certificates are not completed. Verify all endpoints are working over SSL, and update NGNIX configuration to use SSL (redirect from plain HTTP when needed)

8. ✅ **COMPLETED** - Find all occourences of `example.com`. I think this is used as an example domain. This has to be moved away to env variable. For dev it is: beryl3.localdomain, for stage it is beryl3-stage.mdubiel.org and for production it is beryl.com. Also display this variable in SYS.

9. ✅ **COMPLETED** - In SYS, /sys/dashboard, the section 'SYSTEM INFO' is showing invalid information about database.

10. ✅ **COMPLETED** - In makefile, when listing status of services from command `staging-status` list all services with the appropiate status is is UP, DOWN, ERROR or whatever other state it is.

11. ✅ **COMPLETED** - Chip and icon for text change is barelly visible, it should be rather darker. Ensure both chips (text change and user avatar are aligned). Make the border of both close to black, always use semantic color definitions. and the text with one of highlight colors. Background should blend with main background.

12. ✅ **COMPLETED** - Icons used in 'unknown image' are using classes with divided value, do not use that at all. Remove all /10, /20 /30 and similar rntirelly from the application as it looks bad. use semantic definitions for it.

13. ✅ **COMPLETED** - Breadcrund should not be displayed at Home '/' page.

14. ✅ **COMPLETED** - On the Home page, when user is logged in they should see a link to their dashboard, collections and favourites instead the hero section "Ready to organize..."

15. The callout actions in 'What you can do with Beryl3', should use different colors for icon and title, as some of the grays used there are barelly visible.

16. Revisit task 12. I was talking mostly about skipped element: - Image upload placeholders (`text-base-content/40` for image icons) - that looks terrible bad, and has to be modified.