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

15. ✅ **COMPLETED** - The callout actions in 'What you can do with Beryl3', should use different colors for icon and title, as some of the grays used there are barelly visible.

16. ✅ **COMPLETED** - Revisit task 12. I was talking mostly about skipped element: - Image upload placeholders (`text-base-content/40` for image icons) - that looks terrible bad, and has to be modified.

17. ✅ **COMPLETED** - Revise Task 16. This is now better, but can you use one of gray colors instead of black?

18. ✅ **COMPLETED** - Revise task 15, the cards 'Track everything' and 'share collections' are in very light gray color, and are not well visible.

19. ✅ **COMPLETED** - On /dashboard/ I have this 'share you passion'. I do not really like this section. Shall we get id of it or modify somehow?

20. ✅ **COMPLETED** - Revise 18. Now the cards Guest Reservations and Flexible Structure are in the same light gray. I have a proposal. Take the color of 'Organize collections', then take a color of 'Track everything', define a gradient colors between them (remember to be desaturated), and define new 4 colors in scheme. Then use these 4 colors in addtion to style these 6 cards.

21. ✅ **COMPLETED** - I like to idea of 'Make your collections shareable' on dashboard. Can you add two more of this kind?

22. ✅ **COMPLETED** - I like how this end up in task 20. However, for second row, can you do the same, but take different base colors?

23. ✅ **COMPLETED** - Revise task 17, it is again using the class `text-base-content/40` what is wrong.

24. ✅ **COMPLETED** - In user context menu (which is displayed after user clicks on user chip in right top corner). It shows the user email instead of username. Also, the same applies to "Welcome Back, user@...". I want it to show user first name. Make a method, which will return the user first name, or his email if first name is unavailable and use that wherever username is supposed to be displayed. Use model class method not template tag.

25. ✅ **COMPLETED** - I need to consider a subscription to email list. This is a bit more complex task. I'm going to use Resend at this moment, and want to have users subscribed to Audiences. I need to add new flag on User profile 'receive marketing emails'. If this one is checked I need that user email (promary only) to be added to Resend audiences so I can send marketing email later. This should be done on the registration, and on every change of this property. I also need a separate 'unsubscribe' link which will unsubscribe all user emails from that (so mark all emails as 'receive marketing emails' false when user unsubscribe). For this unsubscribe you need to design secure flow which do not require user logging in.

26. ✅ **COMPLETED** - To continue on task 26. I need in /sys/ a separate table view with all emails saying: user, consent to receive marketing email, email and is this email present in Audiences. If user do not consent and email is in Audiences mark it.

27. ✅ **COMPLETED** - To follow on task 27. If email is marked, make a link to action to quickly remove that user email from Audiences in Resend.

28. ✅ **COMPLETED** - Add a new view to configure user account settings. Now it should contain a number of settings: First name, family name and email marketing consent. It should be available under /user/settings and availeble under 'account settings' from drop down chip user menu.

29. ✅ **COMPLETED** - This is data task. I need you to research what are the most common types of collection items, have a look what we already have in database and try to find another type of items, I need at least 40 item types. For each item type propose attributes for them, as it is now. Sync that data with population scripts, so I can easy integrate this with other environments. Inject this data to DEV environment. Make a plan first, I'll review and approve

30. ✅ **COMPLETED** - This is data task. Research typical internet platforms, where you can link items with the attributes created in task 29. This is to popoulate Link Patterns. Limit to 100 patterns. Sync that data with population scripts, so I can easy integrate this with other environments. Inject this data to DEV environment. Make a plan first, I'll review and approve

31. ✅ **COMPLETED** - System is complaining about No module named 'core.lucide' (at least her: /collections/new/). Validate the entire code, and fix this issue.

32. ✅ **COMPLETED** - Design import feautre, import file should be in JSON/YAML format and should include everything from Colletcion, Item, Links and attributes. Include as much meta data as possible. This import should be available only from SYS (so, only application admin can do that) and need to specify user  to where to import to. Include optional image import (download from WEB). 

33. Implement nudity detection in the images. Implement feautre flag how to thread this detection. This flag should have the following levels: "flag only", "delete", "soft ban", "hard ban". The levels will do the following:
 - in the flag only the image is flagged (need new field in model) and reported in the SYS dashboard. It does not modify user.
 - Delete will immadiatelly remove image from the system, and inform user about detection of unapropiate image content. Also, make this logged correctly.
 - Soft ban will do the same as the previous step, but increse the counter of misuse (need this new field for user). When counter reaches the number (configurable by another feautre flag) user is disallowed to login again permanently, and manual administrator intervention is needed to unblock it.
 - Hard ban will do the same but will ban user after first attemt.
I like to see misuse counter in /sys/users and the state of ban. To not implement 'unban feautre now'. Integrate banning with django-allauth.
Also, make the notice on all user image upload forms, that upload of image is a subject of validation actions and point to (regulamin aplikacji) which we will write later on.
I also want to have a batch action from SYS level on the /sys/media/nudes/ to batch process all images (in batches) to verify they do not break rules. make a table with the fields: user, item, image, findings and last check. 
The image verification status can be loaded into the image model itself, as we already have comprehersive model for image processing. Also, make these verification also part of this model do not create additional helpers, all should be placed in model (we follow the concept of big models, small views).

34. These are fixes to previous point. When image is approved it should be never validated again (until I unapprove). Ensure, that when I do batch analysis the image will be not flagged. Well it can be flagged, but is is now approved, so restrictions do not apply. When you display the image, it has to be implemented globally verify the status of this verification. if it is approved or not flagged return regular image url as it is not, it apply also to images. for user content, when the image is flagged return url to 'error image'. The same applies to thumbnails. For SYS content moderation normal URL but blured, as it is now implemented.
Modifications in the view: /sys/content-moderation/
 - keep Moderation Overview
 - keep Moderation actions
 - remove content status and recent violations
 - keep recent flagged content, but change blur to blur-sm and link user to /admin/ user page. Remove review button and replace it with 'Approve' and 'Delete'.
Modifications in the view: /sys/content-moderation/flagged/
 - keep the filter on top
 - instead of grid, show the table similar to the one on /sys/content-moderation/ but include these information:
   - Image (twice bigger then on /sys/content-moderation/), blured as it is now
   - Flagged datetime
   - It's score total
   - badges with the detection classes and their individual scores (rounded to 2 places), do not show information about boxbox - it should be like: ( Female breast exposed: 0,87 ) ( Face female: 0,85 ) - where () represents badge.
   - buttons: Approve to let this image go, and mark it as Approved; Delete - to delete it permanently; Ban user - to immadiatelly ban the user in django-allauth.
Also, let's update slighty /sys/media/ browser view:
- keep the filter
- table:
 - add image thumbnail as first column
 - merge type (collection or item) with the name, keep the information if file is Downloaded or Uploaded with the icon, add that icon description to the legend.
 - in the name field show with small font file name, with clickable link which will open the image in new window, and if GCS is used link (icon) to the GCS location
 - item / collection (trimmed to 15 chars and linked to that object) and its hash below
 - keep size
 - remove Storage column, move that information as an icon, next to file name
 - Change modified date to created (the moment when image was uploaded to the system)
 - Owner should be displayed as user prefered name and linked to its admin profile
 - Add content with the content management status (total score)
 - Keep status, however I do not know what that means
 - Keep actions


34. Add a checkbox for user marketing consent when registering. It has to be disable by default.

35. ✅ **COMPLETED** - UI fixes on /sys/
These changes will be later replicated to other views, so we need to make them correclty and with best practices.
 - First element (below header, header stays as it is) should be located action buttons. For dashboard view move the buttons from "Quick Actions": Manage Users, Item Types, Link Patterns, View Metrics, System Settings, Media browser. Remove other buttons and "Quick Actions" section entirelly.
 - Each section has to be build in the way that <h3> is no "> header text" but "Icon Header Text". Make icon in the same color as header. Keep same styling for hader text.
 - The sections should not have this additional container with border and gap-6, that consumes space.
 - On dashboard remove "Recent System Activity" section
 - remove gradient and shadow from the elements, keep buttons styling as it is (I like the style with slighty thicker border on bottom for buttons)

#34. Styling of SYS
#
#35. Messages not showing on user space, and in sys should be a banner
#
#36. Public collection view should display preferred user name (nickname, or First name as it is in the dashboard and other spaces)
#
#37.The icon 'minus-circle' does not exist.

# Reporting:
# - number of media files without association to item or collection (preauthorized likt to job to purge that)
# - 

Task 38: In implementation, not tested
Create a new Model for collectiong the following metrics:
 Users:
 - Total users
 - Active (24h, 7d, 30d)
 - New (24h, 7d, 30d)
 Collections:
 - Items
 - Item type distribution
 - Collection Visibility (Private/Public/Unlisted)
 - Item Status (In collection, lent out, ordered, previously owned, reserved, wanted)
 - Item Types and attributes usage and distribution
 Other:
 - Link patterns (matching and not matching) used by all links in collections and items
 Storage:
 - Media storage
 - total files
 - Storage used
 - Recent Uploads (24h, 7d, 30d)
 - file integrity
 Email:
 - Total emails
 - Pending
 - Sent
 - Failed
 - Marketing consent (opt-in, opt-out)
 - Synced with resend
 Content moderation: 
 - flagged
 - pending review
 - user violations
 - banned users

These metrics should be collected once per day, preferably around midnight and another entry should be created.
I want to receive email (on superuser registered email) with a current value, change from day before and change from 1 week before. The execution of that should be done by management command, update deployment scripts (preproduction, production) to deploy this job.
Also, in SYS panel compltelly redesign /sys/metrics and include only these mentioned data from new Model. Make it as a table - first column: metric name followed by: current value, change from yesterday, change from 1 week, change in 30d (use colors and arrows: green up, red down).
Indicate the date (below action buttons) of last metrics collection.
Update /sys/metrics/prometheus to match this data.
Review this task first, and propose other reasonable metrics I can review.
After approval, execute all this tasks locally and update all necessary scripts and make targets if necessary.


 When adding item, user should be able to select initial type of item.

 Item type popup is too large, it has to be splitted into 3 or 4 columns to fit all elements without need to scroll the page.

 When adding attribute type boolean, user should be presented with checkbox with a label not input form. This has to be loaded dynamically with HX.

 In add link modal the text " Custom Display Name (Optional) Leave empty to auto-detect from URL" should wrap, it is too long.

 After editing or adding new item user should be redirected to that item, not to the collection.

 On item details page add extra button to add attrinute and add link in the attributes and links table in addition to action buttons on top.

 Add filtering options in collection view to limit number of displayed items.

 Add pagination to collection.

 Cannot add two attributes with same key (eg.: two authors of the same book).

When collection has a "series" of some attribute, eg. there is "series of diskworl noveles" (items sharing the same attribute key and value), they could be grupped. It can be enabled per collection via checkbox "enable grouping". It can be sen only by owners, and all llist displays needs to respect that.

When item has attributes which do not belong to current item type, there should be some hint that there are hidden attributes.

Add grouping and "sort by this attribute (or name, or status or...)"

Add a field for item "Your Id" and "location"

(Item) move dialog to another colelction need some UI improvements.

Eventually display on top statiscics from attributes (how many read, authors, etc.) and let filter with that values.

Thumbnail image (the main image for the item, should be clickable and lead to item details), same for categories

Mobile version of the app need some UI improvements.

Compact all JavaScript to one file and reference JS from there. No inline javascript code if not necessary.