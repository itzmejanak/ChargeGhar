from __future__ import annotations

from celery import shared_task
from django.utils import timezone
from django.core.cache import cache

from api.common.tasks.base import BaseTask
from api.content.models import Banner, FAQ, ContentPage


@shared_task(base=BaseTask, bind=True)
def cleanup_expired_banners(self):
    """Clean up expired banners"""
    try:
        now = timezone.now()
        
        # Mark expired banners as inactive
        expired_banners = Banner.objects.filter(
            is_active=True,
            valid_until__lt=now
        )
        
        updated_count = expired_banners.update(is_active=False)
        
        # Clear banner cache
        cache.delete("active_banners")
        
        self.logger.info(f"Marked {updated_count} expired banners as inactive")
        return {'expired_count': updated_count}
        
    except Exception as e:
        self.logger.error(f"Failed to cleanup expired banners: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def refresh_content_cache(self):
    """Refresh all content caches"""
    try:
        from api.content.services import (
            ContentPageService, FAQService, ContactInfoService, BannerService
        )
        
        # Clear existing caches
        cache_keys = [
            "active_banners",
            "faqs_by_category", 
            "contact_info_all"
        ]
        
        for key in cache_keys:
            cache.delete(key)
        
        # Also clear content page caches
        for page_type in ContentPage.PageTypeChoices.values:
            cache.delete(f"content_page:{page_type}")
        
        # Warm up caches by fetching data
        banner_service = BannerService()
        banner_service.get_active_banners()
        
        faq_service = FAQService()
        faq_service.get_faqs_by_category()
        
        contact_service = ContactInfoService()
        contact_service.get_all_contact_info()
        
        # Warm up content pages
        content_service = ContentPageService()
        for page_type in ContentPage.PageTypeChoices.values:
            try:
                content_service.get_page_by_type(page_type)
            except:
                pass  # Skip if page doesn't exist
        
        self.logger.info("Content caches refreshed successfully")
        return {'status': 'success', 'caches_refreshed': len(cache_keys) + len(ContentPage.PageTypeChoices.values)}
        
    except Exception as e:
        self.logger.error(f"Failed to refresh content cache: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def generate_content_analytics_report(self):
    """Generate content analytics report"""
    try:
        from api.content.services import ContentAnalyticsService
        
        service = ContentAnalyticsService()
        analytics = service.get_content_analytics()
        
        # Cache the analytics report
        cache.set('content_analytics', analytics, timeout=3600)  # 1 hour
        
        self.logger.info("Content analytics report generated")
        return analytics
        
    except Exception as e:
        self.logger.error(f"Failed to generate content analytics: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def backup_content_data(self):
    """Backup critical content data"""
    try:
        import json
        import os
        from django.conf import settings
        
        # Create backup data
        backup_data = {
            'timestamp': timezone.now().isoformat(),
            'content_pages': [],
            'faqs': [],
            'contact_info': [],
            'banners': []
        }
        
        # Backup content pages
        for page in ContentPage.objects.all():
            backup_data['content_pages'].append({
                'page_type': page.page_type,
                'title': page.title,
                'content': page.content,
                'is_active': page.is_active,
                'created_at': page.created_at.isoformat(),
                'updated_at': page.updated_at.isoformat()
            })
        
        # Backup FAQs
        for faq in FAQ.objects.all():
            backup_data['faqs'].append({
                'question': faq.question,
                'answer': faq.answer,
                'category': faq.category,
                'sort_order': faq.sort_order,
                'is_active': faq.is_active,
                'created_at': faq.created_at.isoformat(),
                'updated_at': faq.updated_at.isoformat()
            })
        
        # Backup contact info
        for info in ContactInfo.objects.all():
            backup_data['contact_info'].append({
                'info_type': info.info_type,
                'label': info.label,
                'value': info.value,
                'description': info.description,
                'is_active': info.is_active,
                'updated_at': info.updated_at.isoformat()
            })
        
        # Backup banners
        for banner in Banner.objects.all():
            backup_data['banners'].append({
                'title': banner.title,
                'description': banner.description,
                'image_url': banner.image_url,
                'redirect_url': banner.redirect_url,
                'display_order': banner.display_order,
                'is_active': banner.is_active,
                'valid_from': banner.valid_from.isoformat(),
                'valid_until': banner.valid_until.isoformat(),
                'created_at': banner.created_at.isoformat()
            })
        
        # Save backup file
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"content_backup_{timestamp}.json"
        
        backup_dir = os.path.join(settings.BASE_DIR, 'backups', 'content')
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_path = os.path.join(backup_dir, backup_filename)
        
        with open(backup_path, 'w') as backup_file:
            json.dump(backup_data, backup_file, indent=2)
        
        # Clean up old backups (keep last 30 days)
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        
        for filename in os.listdir(backup_dir):
            if filename.startswith('content_backup_') and filename.endswith('.json'):
                file_path = os.path.join(backup_dir, filename)
                file_time = timezone.datetime.fromtimestamp(
                    os.path.getctime(file_path),
                    tz=timezone.get_current_timezone()
                )
                
                if file_time < cutoff_date:
                    os.remove(file_path)
        
        self.logger.info(f"Content backup created: {backup_filename}")
        return {
            'backup_filename': backup_filename,
            'backup_path': backup_path,
            'content_pages': len(backup_data['content_pages']),
            'faqs': len(backup_data['faqs']),
            'contact_info': len(backup_data['contact_info']),
            'banners': len(backup_data['banners'])
        }
        
    except Exception as e:
        self.logger.error(f"Failed to backup content data: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def optimize_content_search_index(self):
    """Optimize content for search (if using search engine)"""
    try:
        # This would integrate with search engines like Elasticsearch
        # For now, just update search-related caches
        
        from api.content.services import ContentSearchService
        
        search_service = ContentSearchService()
        
        # Pre-populate common search results
        common_queries = [
            'rental', 'power bank', 'payment', 'return', 'charge',
            'account', 'profile', 'support', 'help', 'contact'
        ]
        
        indexed_queries = 0
        
        for query in common_queries:
            try:
                results = search_service.search_content(query)
                # Cache search results for 1 hour
                cache.set(f"search_results:{query}", results, timeout=3600)
                indexed_queries += 1
            except Exception as e:
                self.logger.warning(f"Failed to index query '{query}': {str(e)}")
        
        self.logger.info(f"Search index optimized for {indexed_queries} queries")
        return {
            'indexed_queries': indexed_queries,
            'total_queries': len(common_queries)
        }
        
    except Exception as e:
        self.logger.error(f"Failed to optimize search index: {str(e)}")
        raise


@shared_task(base=BaseTask, bind=True)
def validate_content_links(self):
    """Validate external links in content"""
    try:
        import requests
        from urllib.parse import urlparse
        
        broken_links = []
        
        # Check banner redirect URLs
        banners_with_urls = Banner.objects.filter(
            redirect_url__isnull=False,
            is_active=True
        ).exclude(redirect_url='')
        
        for banner in banners_with_urls:
            try:
                response = requests.head(banner.redirect_url, timeout=10)
                if response.status_code >= 400:
                    broken_links.append({
                        'type': 'banner',
                        'title': banner.title,
                        'url': banner.redirect_url,
                        'status_code': response.status_code
                    })
            except Exception as e:
                broken_links.append({
                    'type': 'banner',
                    'title': banner.title,
                    'url': banner.redirect_url,
                    'error': str(e)
                })
        
        # Check content page links (basic URL detection)
        import re
        url_pattern = re.compile(r'https?://[^\s<>"]+')
        
        for page in ContentPage.objects.filter(is_active=True):
            urls = url_pattern.findall(page.content)
            
            for url in urls:
                try:
                    response = requests.head(url, timeout=10)
                    if response.status_code >= 400:
                        broken_links.append({
                            'type': 'content_page',
                            'title': page.title,
                            'url': url,
                            'status_code': response.status_code
                        })
                except Exception as e:
                    broken_links.append({
                        'type': 'content_page',
                        'title': page.title,
                        'url': url,
                        'error': str(e)
                    })
        
        # Send alert if broken links found
        if broken_links:
            from api.notifications.services import notify_bulk
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admin_users = User.objects.filter(is_staff=True, is_active=True)
            
            # Send bulk notification to all admins
            notify_bulk(
                admin_users,
                'broken_links_detected',
                async_send=True,
                broken_links_count=len(broken_links),
                broken_links=broken_links
            )
        
        self.logger.info(f"Link validation completed. {len(broken_links)} broken links found")
        return {
            'total_links_checked': len(broken_links) + (len(banners_with_urls) - len([l for l in broken_links if l['type'] == 'banner'])),
            'broken_links_count': len(broken_links),
            'broken_links': broken_links
        }
        
    except Exception as e:
        self.logger.error(f"Failed to validate content links: {str(e)}")
        raise