# The Ultimate Task List

Important! - for generic agent behaviour always consult CLAUDE.md file.

Proceed one by one with listed tasks. Before making changes, create a plan to review. If task is too big, divide it to smaller parts.
For each task, create a branch - do implementation (after review) and then commit changes to this branch. Then ask me to verify the implementation on the local dev environment (write to the console summary and what I should test), also update task summary with the same information.
When testing is completed merge a branch to main, and commit all changes.
Do not push changes to repository (I'll do the same) and do not execute any scripts, especially for production. Do this only when explicitly asked.
After commit is completed, update the task with commit ID.

In this file @TODO.md keep table of contents, and drafted tasks. If the drafted task has no index number add this number over next iteration.
All completed tasks documentation is stored in `docs/reports/taskXXX.md` files.

---

## Table of Contents

### ✅ Completed Tasks (1-47, 45, 48, 49, 50, 51, 52, 53, 56, 58, 59, 60, 62, 64)

See detailed reports in `docs/reports/` directory:

| Task | Description | Report | Commit |
|------|-------------|--------|--------|
| 1 | Fix /sys/settings display inconsistencies | [task001.md](reports/task001.md) | a62d4ab |
| 2 | Remove Application Activity feature | [task002.md](reports/task002.md) | 39e6813 |
| 3 | Add External Services to SYS sidebar | [task003.md](reports/task003.md) | ba38708 |
| 4 | Create email queue management view | [task004.md](reports/task004.md) | 45c738a |
| 5 | Fix external services sidebar links | [task005.md](reports/task005.md) | 82f5723 |
| 6 | Fix /sys/email-queue Error 500 | [task006.md](reports/task006.md) | 63ffb56 |
| 7 | Configure SSL certificates and HTTPS redirects | [task007.md](reports/task007.md) | multiple |
| 8 | Replace example.com with environment variables | [task008.md](reports/task008.md) | 70d9730 |
| 9 | Fix database information display in SYSTEM INFO | [task009.md](reports/task009.md) | abb50af |
| 10 | Improve staging-status command with service states | [task010.md](reports/task010.md) | abb50af |
| 11 | Fix chip and icon visibility in header navigation | [task011.md](reports/task011.md) | ed770fb |
| 12 | Remove opacity classes and use semantic colors | [task012.md](reports/task012.md) | e876d2e |
| 13 | Hide breadcrumb on home page | [task013.md](reports/task013.md) | 27d453d |
| 14 | Update home page for logged-in users | [task014.md](reports/task014.md) | 3cea57e |
| 15 | Update callout action colors and improve visibility | [task015.md](reports/task015.md) | 7386088 |
| 16 | Fix image upload placeholder opacity | [task016.md](reports/task016.md) | ab6b654 |
| 17 | Use gray colors instead of black for placeholders | [task017.md](reports/task017.md) | 40959f0 |
| 18 | Improve visibility of feature cards | [task018.md](reports/task018.md) | 40959f0 |
| 19 | Redesign 'share your passion' section | [task019.md](reports/task019.md) | 40959f0 |
| 20 | Create gradient color scheme for feature cards | [task020.md](reports/task020.md) | 1a6b4bb |
| 21 | Add dashboard tips similar to shareable collections | [task021.md](reports/task021.md) | b68f3ed |
| 22 | Dual gradient color scheme for second row | [task022.md](reports/task022.md) | b68f3ed |
| 23 | Fix remaining low opacity class usage | [task023.md](reports/task023.md) | 1e6edb4 |
| 24 | Fix user display name in context menu | [task024.md](reports/task024.md) | 3e1088d |
| 25 | Implement email marketing subscription with Resend | [task025.md](reports/task025.md) | 38382b3 |
| 26 | Create sys view for email marketing consent | [task026.md](reports/task026.md) | 4647fef |
| 27 | Add action to remove emails from Resend audiences | [task027.md](reports/task027.md) | 855d016 |
| 28 | Implement comprehensive user account settings | [task028.md](reports/task028.md) | 898d9ef |
| 29 | Create 40+ item types with attributes | [task029.md](reports/task029.md) | ebe768b |
| 30 | Research and create 100 link patterns | [task030.md](reports/task030.md) | ebe768b |
| 31 | Resolve critical Lucide icon validation errors | [task031.md](reports/task031.md) | 7b18da2 |
| 32 | Implement comprehensive data import feature | [task032.md](reports/task032.md) | 5d47893 |
| 33 | Implement content moderation with nudity detection | [task033.md](reports/task033.md) | 3ea305a |
| 34 | Add marketing consent checkbox to registration | [task034.md](reports/task034.md) | 38382b3 |
| 35 | Enhance system administration interface | [task035.md](reports/task035.md) | 3bacd48 |
| 36 | Implement daily metrics collection system | [task036.md](reports/task036.md) | bd5aa52 |
| 37 | Refactor item attributes from JSON to relational model | [task037.md](reports/task037.md) | 5e1c77c |
| 38 | Fix item type popup layout with multi-column grid | [task038.md](reports/task038.md) | 5266501 |
| 39 | Implement dynamic boolean attribute UI with HTMX | [task039.md](reports/task039.md) | 5266501 |
| 40 | Allow duplicate attributes (multiple authors, genres) | [task040.md](reports/task040.md) | 5e1c77c |
| 41 | Add item type selection during item creation | [task041.md](reports/task041.md) | multiple |
| 42 | Fix link modal text wrapping | [task042.md](reports/task042.md) | 67822f7 |
| 43 | Redirect to item after edit/create | [task043.md](reports/task043.md) | 67822f7 |
| 44 | Add extra add buttons in attributes/links tables | [task044.md](reports/task044.md) | 67822f7 |
| 45 | Enhanced collection filtering (status, type, attribute) | [task045.md](reports/task045.md) | 1b8c566 |
| 46 | Add pagination to collection | [task046.md](reports/task046.md) | 2c4e8b7 |
| 47 | Implement attribute grouping in collections | [task047.md](reports/task047.md) | 2c4e8b7 |
| 48 | Add hidden attributes hint | (implemented) | 689eaac |
| 49 | Attribute sorting and grouping | (implemented) | 2c4e8b7 |
| 50 | Add custom item fields (Location and Your ID) | [task050_progress.md](reports/task050_progress.md) | 689eaac, 12f2819, eecdef6, 4e09d9b |
| 51 | Improve move item dialog UI | (implemented) | 85ed5c1 |
| 52 | Smart filter attribute statistics and filtering | (implemented) | 2c4e8b7 |
| 53 | Make thumbnails clickable | (implemented) | 576beb5 |
| 56 | Implement error pages | (implemented) | b3572f3 |
| 58 | Group display of multiple same attributes | [task058.md](reports/task058.md) | 772825b |
| 59 | Easy toggle for boolean attributes | [task059.md](reports/task059.md) | (confirmed working) |
| 60 | Fix item type popup layout | (implemented) | 09bfe23 |
| 62 | Dynamic background images for public collections | [task062.md](reports/task062.md) | 68a827c |
| 64 | Create public user profile page | [task064.md](reports/task064.md) | c74fbf1 |

---

## 📋 Planned Tasks

### Task 54: Mobile UI Improvements

**Status:** Pending

**Description:**
Mobile version of the app need some UI improvements

**Areas to Improve:**
- Navigation menu
- Form inputs
- Touch targets
- Responsive tables
- Image galleries
- Modal dialogs

---

### Task 55: Consolidate JavaScript to Single File

**Status:** Pending

**Description:**
Compact all JavaScript to one file and reference JS from there. No inline javascript code if not necessary

**Goals:**
- Single app.js file
- No inline scripts
- Better caching
- Easier maintenance
- Minification support

---

### Task 57: Add Autocompletion for Item Attributes

**Status:** Pending

**Description:**
When adding or editing item attribute the system (with HX) should try to autocomplete that information (min. 3 characters, search anywhere in the string). For autocomplete data you need to query CollectionItemAttributeValue for the items user own, and are the same type.

**Example:**
When I'm trying to add to the 'book' the 'Author' attribute it should look up for all CollectionItemAttributeValue records where user is an owner, and are the records are type 'Author' referenced to book item attribute.
Then, similar like in task 50, it should autocomplete this value, pointing to existing entry to the database to avoid duplicates with same value. If value for current user is unknown then create new one.

**Technical Requirements:**
- HTMX endpoint for autocomplete
- Min 3 characters to trigger
- Search user's existing values
- Filter by item type
- Fuzzy matching
- Fast response (<100ms)

---

### Task 61: Geographic Access Restrictions

**Status:** Pending

**Original Description:**
Prevent users from specific countries (configurable as env variable) to access the application. Silently fail or redirect to their country intelligence agency. It is supposed to protect application and be mcompliant with the law from the possible users from selected countries.

---

### Task 63: Remove Image Placeholders

**Status:** Pending

**Description:**
Review entire codebase and remove image placeholders that are still in use.

**Requirements:**
- Search for placeholder image references
- Replace with proper image handling or icons
- Ensure no broken image displays

---

### Task 65: Performance Optimization Plan

**Status:** Pending

**Description:**
Collections with many items and attributes load very slow. Create a performance improvement plan.

**Requirements:**
- Analyze current bottlenecks (make a plan, do not implement)
- Identify slow database queries
- Review template rendering performance
- Propose caching strategies
- Consider pagination improvements
- Suggest database indexing
- Recommend lazy loading strategies

**Deliverable:** Performance analysis document, not implementation

---


## Task 33 Additional Requirements

**Status:** Pending (base implementation completed)

These enhancements extend the content moderation system (Task 33):

### Image URL Logic

**Requirement:**
When displaying images, verify moderation status:
- If approved or not flagged: return regular image URL
- For user content when flagged: return 'error image' URL
- Same applies to thumbnails
- For SYS content moderation: normal URL but blurred

**Implementation Needed:**
- Template tag or model method: `get_safe_image_url()`
- Returns appropriate URL based on status
- Handles thumbnails same way
- SYS views get blur-sm class

### Modifications to `/sys/content-moderation/`

**Keep:**
- Moderation Overview
- Moderation actions
- Recent flagged content

**Changes:**
- Change blur to `blur-sm`
- Link user to `/admin/` user page
- Remove 'Review' button
- Add 'Approve' button
- Add 'Delete' button

**Remove:**
- Content status section
- Recent violations section

### Modifications to `/sys/content-moderation/flagged/`

**Keep:**
- Filter on top

**Change to Table Layout:**
Instead of grid, show table with columns:
- **Image** (2x bigger than dashboard, blurred with `blur-sm`)
- **Flagged datetime**
- **Total score**
- **Detection classes** - Badges with individual scores (rounded to 2 places)
  - Format: "Female breast exposed: 0.87", "Face female: 0.85"
  - Do NOT show bounding box information
- **Actions:**
  - Approve button - mark as Approved
  - Delete button - delete permanently
  - Ban user button - immediate ban in django-allauth

### Update `/sys/media/` Browser View

**Keep:**
- Filter

**Table Modifications:**
- **Add image thumbnail** as first column
- **Merge type** (collection or item) with name
  - Keep Downloaded/Uploaded icon
  - Add icon description to legend
- **Name field:**
  - Show filename in small font
  - Clickable link to open image in new window
  - If GCS: add icon link to GCS location
- **Item/Collection:**
  - Trim to 15 chars
  - Link to object
  - Show hash below
- **Keep size column**
- **Remove Storage column** - show as icon next to filename instead
- **Change modified date to created** (upload timestamp)
- **Owner:** Display as preferred name, link to admin profile
- **Add content column:** Content moderation status + total score
- **Keep status column** (needs clarification on meaning)
- **Keep actions**

---

## Notes

- All completed tasks (1-47, 45, 48-53, 56, 58-60, 62, 64) have detailed reports in `docs/reports/` directory
- Task 61 is declined due to ethical concerns
- Task 33 additional requirements need implementation
- Tasks 54, 55, 57 are next priority pending tasks
- Task 64 implemented - public user profiles at `/u/<username>/`
- Unnumbered tasks (remove placeholders, performance plan) are pending
- When starting new tasks, follow the workflow: plan → review → implement → test → commit
- Always check CLAUDE.md for workflow guidelines
