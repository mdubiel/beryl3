"""
Content Moderation Service using NudeNet

Provides image content analysis and moderation functionality
"""

import logging
import tempfile
from typing import Dict, Tuple, Optional
from datetime import datetime

from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone

logger = logging.getLogger("webapp")


class ContentModerationService:
    """
    Service for analyzing and moderating image content using NudeNet
    """
    
    def __init__(self):
        self.detector = None
        self._initialize_models()
    
    def _initialize_models(self):
        """
        Initialize NudeNet models lazily
        """
        try:
            from nudenet import NudeDetector
            
            if not self.detector:
                logger.info("Initializing NudeNet detector...")
                self.detector = NudeDetector()
                logger.info("NudeNet detector initialized successfully")
                
        except ImportError as e:
            logger.error(f"Failed to import NudeNet: {e}")
            raise ImportError("NudeNet is required for content moderation")
        except Exception as e:
            logger.error(f"Failed to initialize NudeNet models: {e}")
            raise
    
    def is_enabled(self) -> bool:
        """
        Check if content moderation is enabled
        """
        return getattr(settings, 'CONTENT_MODERATION_ENABLED', False)
    
    def get_moderation_action(self) -> str:
        """
        Get the configured moderation action
        """
        return getattr(settings, 'CONTENT_MODERATION_ACTION', 'flag_only')
    
    def analyze_image(self, media_file) -> Tuple[bool, float, Dict]:
        """
        Analyze an image for inappropriate content
        
        Args:
            media_file: MediaFile instance to analyze
            
        Returns:
            Tuple of (is_inappropriate, confidence_score, detailed_results)
        """
        if not self.is_enabled():
            logger.debug("Content moderation disabled, skipping analysis")
            return False, 0.0, {"status": "disabled"}
        
        try:
            # Download image to temporary file for analysis
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                # Get file content from storage
                if hasattr(media_file.file_path, 'read'):
                    # File-like object
                    content = media_file.file_path.read()
                else:
                    # File path string
                    with default_storage.open(media_file.file_path, 'rb') as f:
                        content = f.read()
                
                temp_file.write(content)
                temp_file.flush()
                temp_path = temp_file.name
            
            # Perform detection for detailed analysis
            detection_result = self.detector.detect(temp_path)
            
            # Process results
            is_inappropriate = False
            confidence_score = 0.0
            
            # Analyze detection results
            # NudeDetector returns list of detections: [{'class': 'type', 'score': 0.9, 'box': [x,y,w,h]}]
            inappropriate_classes = [
                'BUTTOCKS_EXPOSED', 'FEMALE_BREAST_EXPOSED', 'FEMALE_GENITALIA_EXPOSED',
                'MALE_BREAST_EXPOSED', 'MALE_GENITALIA_EXPOSED', 'ANUS_EXPOSED'
            ]
            
            max_score = 0.0
            detected_classes = []
            
            for detection in detection_result:
                class_name = detection.get('class', detection.get('label', ''))
                score = detection.get('score', 0.0)
                detected_classes.append({'class': class_name, 'score': score})
                
                # Check if this is an inappropriate class
                if class_name in inappropriate_classes:
                    max_score = max(max_score, score)
                    
            # Consider image inappropriate if any inappropriate class detected with score > 0.6
            confidence_score = max_score
            is_inappropriate = max_score > 0.6
            
            # Compile detailed results
            detailed_results = {
                "timestamp": timezone.now().isoformat(),
                "detection": detection_result,
                "detected_classes": detected_classes,
                "max_inappropriate_score": max_score,
                "confidence_score": confidence_score,
                "is_inappropriate": is_inappropriate,
                "threshold_used": 0.6,
                "model_version": "nudenet_3.4.2"
            }
            
            logger.info(
                f"Content analysis complete for {media_file.original_filename}: "
                f"inappropriate={is_inappropriate}, confidence={confidence_score:.3f}"
            )
            
            # Clean up temporary file
            import os
            try:
                os.unlink(temp_path)
            except:
                pass
            
            return is_inappropriate, confidence_score, detailed_results
            
        except Exception as e:
            logger.error(f"Failed to analyze image {media_file.original_filename}: {e}")
            
            error_results = {
                "timestamp": timezone.now().isoformat(),
                "error": str(e),
                "status": "analysis_failed"
            }
            
            return False, 0.0, error_results
    
    def process_media_file(self, media_file) -> Dict:
        """
        Process a media file through content moderation
        
        Args:
            media_file: MediaFile instance to process
            
        Returns:
            Dict with processing results and actions taken
        """
        from web.models import MediaFile
        
        if not self.is_enabled():
            return {
                "status": "disabled",
                "action": "none"
            }
        
        # Skip non-image files
        if not media_file.content_type or not media_file.content_type.startswith('image/'):
            return {
                "status": "skipped",
                "reason": "not_an_image",
                "action": "none"
            }
        
        logger.info(f"Processing media file for content moderation: {media_file.original_filename}")
        
        # Analyze the image
        is_inappropriate, confidence_score, detailed_results = self.analyze_image(media_file)
        
        # Update media file with moderation results
        if is_inappropriate:
            media_file.content_moderation_status = MediaFile.ContentModerationStatus.FLAGGED
        else:
            media_file.content_moderation_status = MediaFile.ContentModerationStatus.APPROVED
        
        media_file.content_moderation_score = confidence_score
        media_file.content_moderation_details = detailed_results
        media_file.content_moderation_checked_at = timezone.now()
        media_file.save(update_fields=[
            'content_moderation_status', 
            'content_moderation_score',
            'content_moderation_details',
            'content_moderation_checked_at'
        ])
        
        result = {
            "status": "analyzed",
            "is_inappropriate": is_inappropriate,
            "confidence_score": confidence_score,
            "action": "none"
        }
        
        # Take action based on moderation policy
        if is_inappropriate:
            action = self.get_moderation_action()
            result["action"] = action
            
            if action in ['delete', 'soft_ban', 'hard_ban']:
                # Delete the image
                self._delete_media_file(media_file)
                result["file_deleted"] = True
                
                # Handle user violations for ban actions
                if action in ['soft_ban', 'hard_ban'] and media_file.created_by:
                    result.update(self._handle_user_violation(media_file, detailed_results))
                
                # Send notification to user
                self._notify_user_of_violation(media_file, action)
        
        return result
    
    def _delete_media_file(self, media_file):
        """
        Delete media file from storage and mark as deleted
        """
        try:
            # Delete from storage
            if default_storage.exists(media_file.file_path):
                default_storage.delete(media_file.file_path)
                logger.info(f"Deleted file from storage: {media_file.file_path}")
            
            # Mark file as non-existent
            media_file.file_exists = False
            media_file.save(update_fields=['file_exists'])
            
        except Exception as e:
            logger.error(f"Failed to delete media file {media_file.file_path}: {e}")
    
    def _handle_user_violation(self, media_file, detailed_results) -> Dict:
        """
        Handle user violation for ban actions
        """
        if not media_file.created_by:
            return {"user_action": "no_user"}
        
        try:
            # Get or create user profile
            profile, created = media_file.created_by.profile, False
            if not hasattr(media_file.created_by, 'profile'):
                from web.models_user_profile import UserProfile
                profile, created = UserProfile.objects.get_or_create(user=media_file.created_by)
            
            # Add violation
            reason = f"Inappropriate image: {media_file.original_filename} (confidence: {media_file.content_moderation_score:.2f})"
            was_banned = profile.add_content_violation(reason)
            
            return {
                "user_action": "violation_added",
                "violations_count": profile.content_moderation_violations,
                "user_banned": was_banned
            }
            
        except Exception as e:
            logger.error(f"Failed to handle user violation: {e}")
            return {"user_action": "error", "error": str(e)}
    
    def _notify_user_of_violation(self, media_file, action):
        """
        Send notification to user about content violation
        """
        if not media_file.created_by:
            return
        
        try:
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            from django.conf import settings
            
            action_messages = {
                'flag_only': 'has been flagged for review',
                'delete': 'has been removed due to inappropriate content',
                'soft_ban': 'has been removed. Multiple violations may result in account suspension',
                'hard_ban': 'has been removed and your account has been suspended'
            }
            
            subject = "Content Violation Notice - Beryl3"
            message = f"""
Hello {media_file.created_by.first_name or media_file.created_by.email},

Your uploaded image "{media_file.original_filename}" {action_messages.get(action, 'has been reviewed')}.

Our automated content moderation system detected that this image may contain inappropriate content that violates our terms of service.

If you believe this was an error, please contact support.

Best regards,
The Beryl3 Team
            """.strip()
            
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@beryl3.com'),
                recipient_list=[media_file.created_by.email],
                fail_silently=True
            )
            
            logger.info(f"Sent content violation notice to {media_file.created_by.email}")
            
        except Exception as e:
            logger.error(f"Failed to send violation notification: {e}")
    
    def batch_analyze_pending_files(self, batch_size: int = 10) -> Dict:
        """
        Batch analyze files that haven't been checked yet
        
        Args:
            batch_size: Number of files to process in this batch
            
        Returns:
            Dict with batch processing results
        """
        from web.models import MediaFile
        
        if not self.is_enabled():
            return {"status": "disabled", "processed": 0}
        
        # Find pending files
        pending_files = MediaFile.objects.filter(
            content_moderation_status=MediaFile.ContentModerationStatus.PENDING,
            content_type__startswith='image/',
            file_exists=True
        ).order_by('created')[:batch_size]
        
        results = {
            "status": "completed",
            "processed": 0,
            "flagged": 0,
            "approved": 0,
            "errors": 0,
            "actions_taken": {}
        }
        
        for media_file in pending_files:
            try:
                result = self.process_media_file(media_file)
                results["processed"] += 1
                
                if result.get("is_inappropriate"):
                    results["flagged"] += 1
                else:
                    results["approved"] += 1
                
                if result.get("action") != "none":
                    action = result["action"]
                    results["actions_taken"][action] = results["actions_taken"].get(action, 0) + 1
                
            except Exception as e:
                logger.error(f"Error processing file {media_file.id}: {e}")
                results["errors"] += 1
        
        logger.info(f"Batch analysis complete: {results}")
        return results


# Global service instance
content_moderation_service = ContentModerationService()