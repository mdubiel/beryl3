# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring

import time
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from post_office import mail


class Command(BaseCommand):
    help = 'Send test emails using the application email stack (django-post-office + configured SMTP)'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address to send test emails to'
        )
        parser.add_argument(
            'count',
            type=int,
            help='Number of test emails to send'
        )
        parser.add_argument(
            '--priority',
            type=str,
            choices=['now', 'high', 'medium', 'low'],
            default='now',
            help='Email priority (default: now)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.1,
            help='Delay between emails in seconds (default: 0.1)'
        )

    def handle(self, *args, **options):
        email_address = options['email']
        count = options['count']
        priority = options['priority']
        delay = options['delay']

        if count <= 0:
            raise CommandError('Count must be greater than 0')

        if count > 100:
            raise CommandError('Count cannot exceed 100 for safety')

        self.stdout.write(
            self.style.SUCCESS(f'Sending {count} test emails to {email_address} with priority "{priority}"...')
        )

        successful = 0
        failed = 0

        for i in range(1, count + 1):
            try:
                subject = f'Beryl3 Test Email #{i:03d}'
                
                plain_message = f"""
This is test email #{i} of {count} from Beryl3 application.

Email Details:
- Test Number: {i}/{count}
- Priority: {priority}
- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}
- Email Stack: django-post-office + {settings.EMAIL_HOST}

This email was sent to test the email delivery system.

Best regards,
Beryl3 Email Testing System
"""

                html_message = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
        .header {{ background: #f4f4f4; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .details {{ background: #f9f9f9; padding: 15px; border-left: 4px solid #007cba; }}
        .footer {{ color: #666; font-size: 12px; padding: 20px; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>🧪 Beryl3 Test Email #{i:03d}</h2>
    </div>
    <div class="content">
        <p>This is test email <strong>#{i} of {count}</strong> from Beryl3 application.</p>
        
        <div class="details">
            <h3>📧 Email Details:</h3>
            <ul>
                <li><strong>Test Number:</strong> {i}/{count}</li>
                <li><strong>Priority:</strong> {priority}</li>
                <li><strong>Timestamp:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</li>
                <li><strong>Email Stack:</strong> django-post-office + {settings.EMAIL_HOST}</li>
            </ul>
        </div>
        
        <p>This email was sent to test the email delivery system.</p>
    </div>
    <div class="footer">
        Best regards,<br>
        <strong>Beryl3 Email Testing System</strong>
    </div>
</body>
</html>
"""

                mail.send(
                    recipients=[email_address],
                    sender=settings.DEFAULT_FROM_EMAIL,
                    subject=subject,
                    message=plain_message,
                    html_message=html_message,
                    priority=priority,
                )
                
                successful += 1
                self.stdout.write(f'  ✓ Queued test email #{i}')
                
                # Add delay between emails if specified
                if delay > 0 and i < count:
                    time.sleep(delay)
                    
            except Exception as e:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Failed to queue test email #{i}: {str(e)}')
                )

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Email queuing completed:'))
        self.stdout.write(f'  • Successfully queued: {successful}')
        self.stdout.write(f'  • Failed: {failed}')
        self.stdout.write('')
        
        if successful > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'Run "python manage.py send_queued_mail" to process the email queue.'
                )
            )