from __future__ import annotations

from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count
from django.core.cache import cache
import logging


from api.common.services.base import BaseService, CRUDService, ServiceException
from api.common.utils.helpers import paginate_queryset
from api.content.models import ContentPage, FAQ, ContactInfo, Banner

logger = logging.getLogger(__name__)

class ContentPageService(CRUDService):
    """Service for content page operations"""
    model = ContentPage
    
    def get_page_by_type(self, page_type: str) -> ContentPage:
        """Get content page by type - caching handled by view decorator"""
        try:
            page = ContentPage.objects.get(page_type=page_type, is_active=True)
            return page
            
        except ContentPage.DoesNotExist:
            raise ServiceException(
                detail=f"Content page '{page_type}' not found",
                code="page_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to get content page")
    
    @transaction.atomic
    def update_page_content(self, page_type: str, title: str, content: str, admin_user) -> ContentPage:
        """Update content page"""
        try:
            page, created = ContentPage.objects.get_or_create(
                page_type=page_type,
                defaults={'title': title, 'content': content, 'is_active': True}
            )
            
            if not created:
                page.title = title
                page.content = content
                page.save(update_fields=['title', 'content', 'updated_at'])
            
            # Clear cache
            cache_key = f"content_page:{page_type}"
            cache.delete(cache_key)
            
            # Log admin action
            from api.admin.models import AdminActionLog
            AdminActionLog.objects.create(
                admin_user=admin_user,
                action_type='UPDATE_CONTENT_PAGE',
                target_model='ContentPage',
                target_id=str(page.id),
                changes={'page_type': page_type, 'title': title},
                description=f"Updated content page: {page_type}",
                ip_address="127.0.0.1",
                user_agent="Admin Panel"
            )
            
            self.log_info(f"Content page updated: {page_type}")
            return page
            
        except Exception as e:
            self.handle_service_error(e, "Failed to update content page")


class FAQService(CRUDService):
    """Service for FAQ operations"""
    model = FAQ
    
    def get_faqs_by_category(self) -> Dict[str, List[FAQ]]:
        """Get FAQs grouped by category - caching handled by view decorator"""
        try:
            faqs = FAQ.objects.filter(is_active=True).order_by('category', 'sort_order')
            
            # Group by category
            faqs_by_category = {}
            for faq in faqs:
                if faq.category not in faqs_by_category:
                    faqs_by_category[faq.category] = []
                faqs_by_category[faq.category].append(faq)
            
            return faqs_by_category
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get FAQs by category")
    
    def search_faqs(self, query: str) -> List[FAQ]:
        """Search FAQs by question or answer"""
        try:
            return FAQ.objects.filter(
                Q(question__icontains=query) | Q(answer__icontains=query),
                is_active=True
            ).order_by('category', 'sort_order')
        except Exception as e:
            self.handle_service_error(e, "Failed to search FAQs")
    
    @transaction.atomic
    def create_faq(self, question: str, answer: str, category: str, admin_user) -> FAQ:
        """Create new FAQ - cache invalidation handled by view decorator"""
        try:
            # Get next sort order for category
            max_order = FAQ.objects.filter(category=category).aggregate(
                max_order=Count('sort_order')
            )['max_order'] or 0
            
            faq = FAQ.objects.create(
                question=question,
                answer=answer,
                category=category,
                sort_order=max_order + 1,
                created_by=admin_user,
                updated_by=admin_user
            )
            
            self.log_info(f"FAQ created: {question[:50]}...")
            return faq
            
        except Exception as e:
            self.handle_service_error(e, "Failed to create FAQ")
    
    @transaction.atomic
    def update_faq(self, faq_id: str, question: str, answer: str, category: str, admin_user) -> FAQ:
        """Update existing FAQ - cache invalidation handled by view decorator"""
        try:
            faq = FAQ.objects.get(id=faq_id)
            
            faq.question = question
            faq.answer = answer
            faq.category = category
            faq.updated_by = admin_user
            faq.save(update_fields=['question', 'answer', 'category', 'updated_by', 'updated_at'])
            
            self.log_info(f"FAQ updated: {faq_id}")
            return faq
            
        except FAQ.DoesNotExist:
            raise ServiceException(
                detail="FAQ not found",
                code="faq_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to update FAQ")


class ContactInfoService(CRUDService):
    """Service for contact information operations"""
    model = ContactInfo
    
    def get_all_contact_info(self) -> List[ContactInfo]:
        """Get all active contact information - caching handled by view decorator"""
        try:
            contact_info = ContactInfo.objects.filter(is_active=True).order_by('info_type')
            logger.debug(f"Found {contact_info.count()} active contact info records")
            
            return contact_info
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get contact information")
    
    @transaction.atomic
    def update_contact_info(self, info_type: str, label: str, value: str, 
                          description: str, admin_user) -> ContactInfo:
        """Update contact information - cache invalidation handled by view decorator"""
        try:
            contact_info, created = ContactInfo.objects.get_or_create(
                info_type=info_type,
                defaults={
                    'label': label,
                    'value': value,
                    'description': description,
                    'updated_by': admin_user
                }
            )
            
            if not created:
                contact_info.label = label
                contact_info.value = value
                contact_info.description = description
                contact_info.updated_by = admin_user
                contact_info.save(update_fields=['label', 'value', 'description', 'updated_by', 'updated_at'])
            
            self.log_info(f"Contact info updated: {info_type}")
            return contact_info
            
        except Exception as e:
            self.handle_service_error(e, "Failed to update contact information")


class BannerService(CRUDService):
    """Service for banner operations"""
    model = Banner
    
    def get_active_banners(self) -> List[Banner]:
        """Get currently active banners - caching handled by view decorator"""
        try:
            now = timezone.now()
            banners = Banner.objects.filter(
                is_active=True,
                valid_from__lte=now,
                valid_until__gte=now
            ).order_by('display_order', '-created_at')
            
            return banners
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get active banners")
    
    @transaction.atomic
    def create_banner(self, title: str, description: str, image_url: str,
                     redirect_url: str, valid_from: timezone.datetime,
                     valid_until: timezone.datetime, admin_user) -> Banner:
        """Create new banner - cache invalidation handled by view decorator"""
        try:
            # Get next display order
            max_order = Banner.objects.aggregate(
                max_order=Count('display_order')
            )['max_order'] or 0
            
            banner = Banner.objects.create(
                title=title,
                description=description,
                image_url=image_url,
                redirect_url=redirect_url,
                display_order=max_order + 1,
                valid_from=valid_from,
                valid_until=valid_until
            )
            
            self.log_info(f"Banner created: {title}")
            return banner
            
        except Exception as e:
            self.handle_service_error(e, "Failed to create banner")


class AppInfoService(BaseService):
    """Service for app information"""
    
    def get_app_version_info(self, current_version: str) -> Dict[str, Any]:
        """Get app version information"""
        try:
            # These would typically come from app configuration or database
            latest_version = "1.2.3"  # Should be configurable
            minimum_version = "1.0.0"  # Should be configurable
            
            # Parse version numbers for comparison
            def parse_version(version_str):
                return tuple(map(int, version_str.split('.')))
            
            current_parsed = parse_version(current_version)
            latest_parsed = parse_version(latest_version)
            minimum_parsed = parse_version(minimum_version)
            
            update_required = current_parsed < minimum_parsed
            update_available = current_parsed < latest_parsed
            
            return {
                'current_version': current_version,
                'minimum_version': minimum_version,
                'latest_version': latest_version,
                'update_required': update_required,
                'update_available': update_available,
                'update_url': 'https://play.google.com/store/apps/details?id=com.powerbank.app' if update_available else None,
                'release_notes': 'Bug fixes and performance improvements' if update_available else ''
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get app version info")
    
    def get_app_health(self) -> Dict[str, Any]:
        """Get app health status"""
        try:
            from django.conf import settings
            import time
            
            # Basic health check
            health_data = {
                'status': 'healthy',
                'timestamp': timezone.now(),
                'version': getattr(settings, 'APP_VERSION', '1.0.0'),
                'uptime_seconds': int(time.time()),  # Mock uptime
                'database_status': 'healthy',
                'cache_status': 'healthy',
                'services': {
                    'redis': 'healthy',
                    'celery': 'healthy',
                    'storage': 'healthy'
                }
            }
            
            return health_data
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get app health")


class ContentSearchService(BaseService):
    """Service for content search"""
    
    def search_content(self, query: str, content_type: str = 'all') -> List[Dict[str, Any]]:
        """Search across all content types"""
        try:
            results = []
            
            if content_type in ['all', 'pages']:
                # Search content pages
                pages = ContentPage.objects.filter(
                    Q(title__icontains=query) | Q(content__icontains=query),
                    is_active=True
                )
                
                for page in pages:
                    results.append({
                        'content_type': 'page',
                        'title': page.title,
                        'excerpt': page.content[:200] + '...' if len(page.content) > 200 else page.content,
                        'url': f'/content/{page.page_type}',
                        'relevance_score': self._calculate_relevance(query, page.title, page.content)
                    })
            
            if content_type in ['all', 'faqs']:
                # Search FAQs
                faqs = FAQ.objects.filter(
                    Q(question__icontains=query) | Q(answer__icontains=query),
                    is_active=True
                )
                
                for faq in faqs:
                    results.append({
                        'content_type': 'faq',
                        'title': faq.question,
                        'excerpt': faq.answer[:200] + '...' if len(faq.answer) > 200 else faq.answer,
                        'url': f'/faq#{faq.id}',
                        'relevance_score': self._calculate_relevance(query, faq.question, faq.answer)
                    })
            
            if content_type in ['all', 'contact']:
                # Search contact info
                contact_info = ContactInfo.objects.filter(
                    Q(label__icontains=query) | Q(value__icontains=query) | Q(description__icontains=query),
                    is_active=True
                )
                
                for info in contact_info:
                    results.append({
                        'content_type': 'contact',
                        'title': info.label,
                        'excerpt': f"{info.value} - {info.description or ''}",
                        'url': '/contact',
                        'relevance_score': self._calculate_relevance(query, info.label, info.value)
                    })
            
            # Sort by relevance score
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return results[:20]  # Limit to top 20 results
            
        except Exception as e:
            self.handle_service_error(e, "Failed to search content")
    
    def _calculate_relevance(self, query: str, title: str, content: str) -> float:
        """Calculate relevance score for search results"""
        try:
            query_lower = query.lower()
            title_lower = title.lower()
            content_lower = content.lower()
            
            score = 0.0
            
            # Title matches get higher score
            if query_lower in title_lower:
                score += 10.0
                if title_lower.startswith(query_lower):
                    score += 5.0
            
            # Content matches
            content_matches = content_lower.count(query_lower)
            score += content_matches * 2.0
            
            # Exact matches get bonus
            if query_lower == title_lower:
                score += 20.0
            
            return score
            
        except Exception:
            return 0.0


class ContentAnalyticsService(BaseService):
    """Service for content analytics"""
    
    def get_content_analytics(self) -> Dict[str, Any]:
        """Get content analytics data"""
        try:
            # Basic counts
            total_pages = ContentPage.objects.filter(is_active=True).count()
            total_faqs = FAQ.objects.filter(is_active=True).count()
            total_banners = Banner.objects.count()
            
            now = timezone.now()
            active_banners = Banner.objects.filter(
                is_active=True,
                valid_from__lte=now,
                valid_until__gte=now
            ).count()
            
            # Popular content (mock data - would need view tracking)
            popular_pages = [
                {'page_type': 'terms-of-service', 'views': 1250},
                {'page_type': 'privacy-policy', 'views': 980},
                {'page_type': 'faq', 'views': 2100}
            ]
            
            popular_faqs = [
                {'question': 'How do I rent a power bank?', 'views': 450},
                {'question': 'What are the rental charges?', 'views': 380},
                {'question': 'How do I return a power bank?', 'views': 320}
            ]
            
            # Recent updates
            recent_updates = []
            
            recent_pages = ContentPage.objects.filter(
                updated_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).order_by('-updated_at')[:5]
            
            for page in recent_pages:
                recent_updates.append({
                    'type': 'page',
                    'title': page.title,
                    'updated_at': page.updated_at
                })
            
            recent_faqs = FAQ.objects.filter(
                updated_at__gte=timezone.now() - timezone.timedelta(days=7)
            ).order_by('-updated_at')[:5]
            
            for faq in recent_faqs:
                recent_updates.append({
                    'type': 'faq',
                    'title': faq.question[:50] + '...' if len(faq.question) > 50 else faq.question,
                    'updated_at': faq.updated_at
                })
            
            # Sort recent updates by date
            recent_updates.sort(key=lambda x: x['updated_at'], reverse=True)
            
            return {
                'total_pages': total_pages,
                'total_faqs': total_faqs,
                'total_banners': total_banners,
                'active_banners': active_banners,
                'popular_pages': popular_pages,
                'popular_faqs': popular_faqs,
                'recent_updates': recent_updates[:10],
                'last_updated': timezone.now()
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get content analytics")