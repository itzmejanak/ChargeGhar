# Content App - AI Context

## 🎯 Quick Overview

**Purpose**: Content management and static data
**Available Components**: models.py, serializers.py, services.py, tasks.py

## 🎆 Suggested API Endpoints (for AI view generation)

*Based on Features TOC mapping and available code structure*

### `GET /api/content/terms-of-service`
**Purpose**: Returns terms of service
**Input**: None
**Service**: ContentService().get_terms_of_service()
**Output**: ContentSerializer data
**Auth**: No

### `GET /api/content/privacy-policy`
**Purpose**: Returns privacy policy
**Input**: None
**Service**: ContentService().get_privacy_policy()
**Output**: ContentSerializer data
**Auth**: No

### `GET /api/content/about`
**Purpose**: Returns about information
**Input**: None
**Service**: ContentService().get_about_info()
**Output**: ContentSerializer data
**Auth**: No

### `GET /api/content/contact`
**Purpose**: Returns contact information
**Input**: None
**Service**: ContentService().get_contact_info()
**Output**: ContentSerializer data
**Auth**: No

### `GET /api/content/faq`
**Purpose**: Returns FAQ content
**Input**: None
**Service**: ContentService().get_faq()
**Output**: List of FAQSerializer data
**Auth**: No

## models.py

**🏗️ Available Models (for view generation):**

### `ContentPage`
*ContentPage - Static content pages like Terms, Privacy Policy, etc.*

**Key Fields:**
- `page_type`: CharField (text)
- `title`: CharField (text)
- `content`: TextField (long text)
- `is_active`: BooleanField (true/false)

### `FAQ`
*FAQ - Frequently Asked Questions*

**Key Fields:**
- `question`: CharField (text)
- `answer`: TextField (long text)
- `category`: CharField (text)
- `sort_order`: IntegerField (number)
- `is_active`: BooleanField (true/false)

### `ContactInfo`
*ContactInfo - Contact information like phone, email, address*

**Key Fields:**
- `info_type`: CharField (text)
- `label`: CharField (text)
- `value`: CharField (text)
- `description`: CharField (text)
- `is_active`: BooleanField (true/false)

### `Banner`
*Banner - Promotional banners for the app*

**Key Fields:**
- `title`: CharField (text)
- `description`: CharField (text)
- `image_url`: URLField (url)
- `redirect_url`: URLField (url)
- `display_order`: IntegerField (number)
- `is_active`: BooleanField (true/false)
- `valid_from`: DateTimeField (datetime)
- `valid_until`: DateTimeField (datetime)

## serializers.py

**📝 Available Serializers (for view generation):**

### `ContentPageSerializer`
*Serializer for content pages*

**Validation Methods:**
- `validate_content()`

### `ContentPagePublicSerializer`
*Public serializer for content pages (no admin fields)*

### `FAQSerializer`
*Serializer for FAQs*

**Validation Methods:**
- `validate_question()`
- `validate_answer()`

### `FAQPublicSerializer`
*Public serializer for FAQs*

### `FAQCategorySerializer`
*Serializer for FAQ categories*

### `ContactInfoSerializer`
*Serializer for contact information*

**Validation Methods:**
- `validate_value()`

### `ContactInfoPublicSerializer`
*Public serializer for contact information*

### `BannerSerializer`
*Serializer for banners*

**Validation Methods:**
- `validate()`

### `BannerPublicSerializer`
*Public serializer for active banners*

### `AppVersionSerializer`
*Serializer for app version information*

**Validation Methods:**
- `validate_current_version()`

### `AppHealthSerializer`
*Serializer for app health check*

### `ContentSearchSerializer`
*Serializer for content search*

**Validation Methods:**
- `validate_query()`

### `ContentSearchResultSerializer`
*Serializer for content search results*

### `ContentAnalyticsSerializer`
*Serializer for content analytics*

## services.py

**⚙️ Available Services (for view logic):**

### `ContentPageService`
*Service for content page operations*

**Available Methods:**
- `get_page_by_type(page_type) -> ContentPage`
  - *Get content page by type*
- `update_page_content(page_type, title, content, admin_user) -> ContentPage`
  - *Update content page*

### `FAQService`
*Service for FAQ operations*

**Available Methods:**
- `get_faqs_by_category() -> Dict[str, List[FAQ]]`
  - *Get FAQs grouped by category*
- `search_faqs(query) -> List[FAQ]`
  - *Search FAQs by question or answer*
- `create_faq(question, answer, category, admin_user) -> FAQ`
  - *Create new FAQ*
- `update_faq(faq_id, question, answer, category, admin_user) -> FAQ`
  - *Update existing FAQ*

### `ContactInfoService`
*Service for contact information operations*

**Available Methods:**
- `get_all_contact_info() -> List[ContactInfo]`
  - *Get all active contact information*
- `update_contact_info(info_type, label, value, description, admin_user) -> ContactInfo`
  - *Update contact information*

### `BannerService`
*Service for banner operations*

**Available Methods:**
- `get_active_banners() -> List[Banner]`
  - *Get currently active banners*
- `create_banner(title, description, image_url, redirect_url, valid_from, valid_until, admin_user) -> Banner`
  - *Create new banner*

### `AppInfoService`
*Service for app information*

**Available Methods:**
- `get_app_version_info(current_version) -> Dict[str, Any]`
  - *Get app version information*
- `get_app_health() -> Dict[str, Any]`
  - *Get app health status*

### `ContentSearchService`
*Service for content search*

**Available Methods:**
- `search_content(query, content_type) -> List[Dict[str, Any]]`
  - *Search across all content types*

### `ContentAnalyticsService`
*Service for content analytics*

**Available Methods:**
- `get_content_analytics() -> Dict[str, Any]`
  - *Get content analytics data*

## tasks.py

**🔄 Available Background Tasks:**

- `cleanup_expired_banners()`
  - *Clean up expired banners*
- `refresh_content_cache()`
  - *Refresh all content caches*
- `generate_content_analytics_report()`
  - *Generate content analytics report*
- `backup_content_data()`
  - *Backup critical content data*
- `optimize_content_search_index()`
  - *Optimize content for search (if using search engine)*
- `validate_content_links()`
  - *Validate external links in content*
