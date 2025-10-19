#!/usr/bin/env python3
"""
Admin Views Migration Script
Splits api/admin/views.py into domain-based files

Usage:
    python migrate_admin_views.py --dry-run    # Preview changes
    python migrate_admin_views.py              # Execute migration
    python migrate_admin_views.py --rollback   # Restore from backup
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime

# Project root
BASE_DIR = Path(__file__).parent
ADMIN_DIR = BASE_DIR / "api" / "admin"
VIEWS_FILE = ADMIN_DIR / "views.py"
VIEWS_DIR = ADMIN_DIR / "views"
BACKUP_FILE = ADMIN_DIR / "views.py.backup"

# View class mappings to their target files
VIEW_MAPPINGS = {
    'auth_views.py': {
        'views': ['AdminLoginView'],
        'description': 'Authentication and authorization'
    },
    'profile_views.py': {
        'views': ['AdminProfileView'],
        'description': 'Admin profile management'
    },
    'user_views.py': {
        'views': [
            'AdminUserListView',
            'AdminUserDetailView',
            'UpdateUserStatusView',
            'AddUserBalanceView'
        ],
        'description': 'User management operations'
    },
    'refund_views.py': {
        'views': ['AdminRefundsView', 'ProcessRefundView'],
        'description': 'Refund processing and management'
    },
    'station_views.py': {
        'views': [
            'AdminStationsView',
            'ToggleMaintenanceView',
            'SendRemoteCommandView'
        ],
        'description': 'Station monitoring and control'
    },
    'notification_views.py': {
        'views': ['BroadcastMessageView'],
        'description': 'Notification broadcasting'
    },
    'dashboard_views.py': {
        'views': ['AdminDashboardView', 'SystemHealthView'],
        'description': 'Dashboard analytics and system health'
    },
    'log_views.py': {
        'views': ['AdminActionLogView', 'SystemLogView'],
        'description': 'Logging and audit trails'
    }
}


def create_backup():
    """Create backup of original views.py"""
    if not VIEWS_FILE.exists():
        print(f"❌ Error: {VIEWS_FILE} not found")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_with_timestamp = ADMIN_DIR / f"views.py.backup_{timestamp}"
    
    shutil.copy2(VIEWS_FILE, backup_with_timestamp)
    shutil.copy2(VIEWS_FILE, BACKUP_FILE)
    
    print(f"✅ Backup created: {backup_with_timestamp}")
    print(f"✅ Backup created: {BACKUP_FILE}")
    return True


def restore_backup():
    """Restore from backup"""
    if not BACKUP_FILE.exists():
        print(f"❌ Error: Backup file not found at {BACKUP_FILE}")
        return False
    
    # Remove views directory if exists
    if VIEWS_DIR.exists():
        shutil.rmtree(VIEWS_DIR)
        print(f"✅ Removed {VIEWS_DIR}")
    
    # Restore original views.py
    shutil.copy2(BACKUP_FILE, VIEWS_FILE)
    print(f"✅ Restored {VIEWS_FILE} from backup")
    
    return True


def extract_imports(content):
    """Extract all import statements from the content"""
    import_pattern = r'^(?:from|import)\s+.+$'
    imports = []
    
    for line in content.split('\n'):
        if re.match(import_pattern, line.strip()):
            imports.append(line)
        elif line.strip() and not line.strip().startswith('#'):
            # Stop at first non-import, non-comment line
            break
    
    return '\n'.join(imports)


def extract_view_class(content, class_name):
    """Extract a view class and its content"""
    # Pattern to match class definition until next class or EOF
    pattern = rf'(class {class_name}\(.*?\):.*?)(?=\nclass\s|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        return match.group(1).rstrip() + '\n'
    return None


def create_view_file(filename, view_classes, all_content, description):
    """Create a view file with specified classes"""
    filepath = VIEWS_DIR / filename
    
    # Extract imports (we'll clean these up manually or use a tool later)
    imports = extract_imports(all_content)
    
    # File header
    content = f'''"""
{description}
"""
{imports}


'''
    
    # Extract each view class
    for view_class in view_classes:
        view_content = extract_view_class(all_content, view_class)
        if view_content:
            content += view_content + '\n\n'
        else:
            print(f"⚠️  Warning: Could not extract {view_class}")
    
    # Write file
    filepath.write_text(content)
    print(f"✅ Created {filename} with {len(view_classes)} views")


def create_init_file():
    """Create __init__.py with all exports"""
    content = '''"""
Admin Panel Views
Organized by domain for better maintainability
"""

# Authentication
from .auth_views import AdminLoginView

# Profile Management
from .profile_views import AdminProfileView

# User Management
from .user_views import (
    AdminUserListView,
    AdminUserDetailView,
    UpdateUserStatusView,
    AddUserBalanceView,
)

# Refund Management
from .refund_views import (
    AdminRefundsView,
    ProcessRefundView,
)

# Station Management
from .station_views import (
    AdminStationsView,
    ToggleMaintenanceView,
    SendRemoteCommandView,
)

# Notifications
from .notification_views import BroadcastMessageView

# Dashboard & Analytics
from .dashboard_views import (
    AdminDashboardView,
    SystemHealthView,
)

# Logging & Auditing
from .log_views import (
    AdminActionLogView,
    SystemLogView,
)

__all__ = [
    # Auth
    'AdminLoginView',
    
    # Profile
    'AdminProfileView',
    
    # Users
    'AdminUserListView',
    'AdminUserDetailView',
    'UpdateUserStatusView',
    'AddUserBalanceView',
    
    # Refunds
    'AdminRefundsView',
    'ProcessRefundView',
    
    # Stations
    'AdminStationsView',
    'ToggleMaintenanceView',
    'SendRemoteCommandView',
    
    # Notifications
    'BroadcastMessageView',
    
    # Dashboard
    'AdminDashboardView',
    'SystemHealthView',
    
    # Logs
    'AdminActionLogView',
    'SystemLogView',
]
'''
    
    init_file = VIEWS_DIR / '__init__.py'
    init_file.write_text(content)
    print(f"✅ Created __init__.py with all exports")


def migrate(dry_run=False):
    """Execute migration"""
    print("=" * 60)
    print("Admin Views Migration Script")
    print("=" * 60)
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be modified\n")
    
    # Read original content
    if not VIEWS_FILE.exists():
        print(f"❌ Error: {VIEWS_FILE} not found")
        return False
    
    original_content = VIEWS_FILE.read_text()
    
    # Count views in original file
    view_count = len(re.findall(r'^class \w+View\(', original_content, re.MULTILINE))
    print(f"\n📊 Found {view_count} view classes in {VIEWS_FILE}")
    
    if not dry_run:
        # Create backup
        if not create_backup():
            return False
        
        # Create views directory
        VIEWS_DIR.mkdir(exist_ok=True)
        print(f"\n✅ Created directory: {VIEWS_DIR}")
    
    print("\n📝 Planned file structure:")
    for filename, config in VIEW_MAPPINGS.items():
        views = config['views']
        desc = config['description']
        print(f"  - {filename}: {len(views)} views - {desc}")
        for view in views:
            print(f"    • {view}")
    
    if dry_run:
        print("\n✅ Dry run complete. Run without --dry-run to execute migration.")
        return True
    
    # Create individual view files
    print("\n🔨 Creating view files...")
    for filename, config in VIEW_MAPPINGS.items():
        create_view_file(
            filename,
            config['views'],
            original_content,
            config['description']
        )
    
    # Create __init__.py
    print("\n🔨 Creating __init__.py...")
    create_init_file()
    
    # Delete original views.py
    VIEWS_FILE.unlink()
    print(f"\n✅ Removed original {VIEWS_FILE}")
    
    print("\n" + "=" * 60)
    print("✅ Migration completed successfully!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("1. Review generated files in api/admin/views/")
    print("2. Clean up unused imports in each file (optional)")
    print("3. Run test suite: ./test_admin_endpoints.sh")
    print("4. If tests pass, delete backup: rm api/admin/views.py.backup*")
    print("5. If tests fail, rollback: python migrate_admin_views.py --rollback")
    
    return True


def main():
    import sys
    
    if '--rollback' in sys.argv:
        print("\n🔄 Rolling back migration...")
        if restore_backup():
            print("\n✅ Rollback completed successfully!")
        return
    
    dry_run = '--dry-run' in sys.argv
    
    try:
        success = migrate(dry_run=dry_run)
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        
        if BACKUP_FILE.exists():
            print("\n🔄 Attempting automatic rollback...")
            restore_backup()
        
        sys.exit(1)


if __name__ == '__main__':
    main()
