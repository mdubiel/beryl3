# Task 34: Add Marketing Consent Checkbox to Registration

**Status:** ✅ Completed
**Verified:** Yes
**Commit ID:** 38382b3 (part of Task 25)

## Task Description

Add a checkbox for user marketing consent when registering. It has to be disabled by default.

## Implementation Summary

### Features Implemented

1. **Registration Form Enhancement**
   - Added marketing consent checkbox to signup form
   - Checkbox disabled (unchecked) by default (opt-in required)
   - Clear labeling and description
   - GDPR-compliant implementation

2. **Resend Integration**
   - Automatic audience subscription on opt-in
   - No subscription if checkbox unchecked
   - Sync status tracking from registration

3. **Form Template**
   - DaisyUI styled checkbox
   - Proper label association
   - Help text explaining purpose
   - Accessible form controls

### Technical Implementation

**Custom Signup Form:**
```python
class CustomSignupForm(SignupForm):
    receive_marketing_emails = forms.BooleanField(
        required=False,
        initial=False,  # Disabled by default
        label='I want to receive marketing emails',
        help_text='Optional: Subscribe to our newsletter and updates'
    )
```

**Registration Flow:**
1. User fills out registration form
2. Marketing consent checkbox visible (unchecked by default)
3. User optionally checks the box
4. On registration:
   - UserProfile created
   - `receive_marketing_emails` set based on checkbox
   - If checked: Email added to Resend audience
   - If unchecked: No subscription created

**Default State:** Opt-in (user must actively check the box)

### Files Modified
- `web/forms.py` - CustomSignupForm with marketing consent field
- `templates/account/signup.html` - Registration template with checkbox
- `web/views/auth.py` - Registration handling with Resend sync
- `web/models.py` - UserProfile model (see Task 25)

### Form Template Example
```html
<div class="form-control">
  <label class="label cursor-pointer justify-start gap-3">
    <input
      type="checkbox"
      name="receive_marketing_emails"
      class="checkbox checkbox-primary"
      {% if form.receive_marketing_emails.value %}checked{% endif %}
    />
    <span class="label-text">
      {{ form.receive_marketing_emails.label }}
      <span class="text-sm opacity-70">{{ form.receive_marketing_emails.help_text }}</span>
    </span>
  </label>
</div>
```

## GDPR Compliance

### Key Requirements Met
1. ✅ **Opt-in by default:** Checkbox unchecked (disabled)
2. ✅ **Clear consent:** Explicit action required from user
3. ✅ **Transparent purpose:** Help text explains what emails they'll receive
4. ✅ **Easy withdrawal:** Users can unsubscribe anytime (Task 25)
5. ✅ **Granular control:** Separate from account creation
6. ✅ **Audit trail:** Consent tracked in UserProfile model

### Legal Considerations
- **GDPR Article 7:** Conditions for consent - met
- **Opt-in requirement:** User must actively check box
- **Unbundling:** Marketing consent separate from registration
- **Withdrawal:** Easy unsubscribe mechanism (secure token link)

## Testing Checklist
- ✅ Checkbox visible on registration form
- ✅ Checkbox unchecked by default
- ✅ Registration works with checkbox checked
- ✅ Registration works with checkbox unchecked
- ✅ Resend audience updated when checked
- ✅ No Resend subscription when unchecked
- ✅ UserProfile created correctly
- ✅ Consent status visible in user settings (Task 28)
- ✅ Consent status visible in SYS panel (Task 26)

## User Journey

**Scenario 1: User Opts In**
1. Visit registration page
2. Fill out required fields (email, password)
3. Check marketing consent checkbox
4. Submit form
5. Account created + UserProfile created
6. Email added to Resend audience
7. Can manage preference in account settings

**Scenario 2: User Opts Out**
1. Visit registration page
2. Fill out required fields
3. Leave marketing consent checkbox unchecked
4. Submit form
5. Account created + UserProfile created
6. Email NOT added to Resend audience
7. Can opt-in later via account settings

## Related Tasks
- Task 25: Email marketing subscription system (parent task)
- Task 26: SYS view for marketing consent management
- Task 27: Remove emails from Resend audiences
- Task 28: User account settings page

## Commit Reference
```
38382b3 - task: Task 25 - Implement email marketing subscription with Resend integration (includes registration checkbox)
```

## Notes
- Implementation completed as part of Task 25
- Single commit covers entire email marketing feature
- Default state is opt-out (GDPR compliant)
- Clear separation between account creation and marketing consent
