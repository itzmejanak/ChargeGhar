#!/usr/bin/env python3
"""
Django Views API Documentation Generator

Analyzes Django views.py files and generates comprehensive request/response
documentation for REST API endpoints.

Usage:
    python3 views_analyzer.py --app users
    python views_analyzer.py --all

Author: ChargeGhar Development Team
"""

import argparse
import ast
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class ViewAnalyzer:
    """Analyzes Django REST Framework views."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.tree = None
        self.analysis_result = {
            'views': [],
            'viewsets': [],
            'router_registrations': [],
            'errors': []
        }
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze the views.py file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            self.tree = ast.parse(source_code)
        except Exception as e:
            self.analysis_result['errors'].append(f"Parse error: {str(e)}")
            return self.analysis_result
        
        # Extract router registrations
        self._extract_router_registrations()
        
        # Analyze view classes
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                self._analyze_view_class(node)
        
        # Match router registrations to views by decorator analysis
        self._match_router_registrations()
        
        return self.analysis_result
    
    def _extract_router_registrations(self) -> None:
        """Extract router.register calls."""
        for node in ast.walk(self.tree):
            if (isinstance(node, ast.Expr) and 
                isinstance(node.value, ast.Call) and 
                isinstance(node.value.func, ast.Attribute) and
                node.value.func.attr == 'register'):
                
                registration = self._parse_router_registration(node.value)
                if registration:
                    self.analysis_result['router_registrations'].append(registration)
    
    def _parse_router_registration(self, call_node: ast.Call) -> Optional[Dict[str, Any]]:
        """Parse router.register() call."""
        try:
            registration = {'route': None, 'name': None}
            
            if len(call_node.args) >= 1:
                route_arg = call_node.args[0]
                if isinstance(route_arg, ast.Constant):
                    registration['route'] = route_arg.value
                elif isinstance(route_arg, ast.Str):
                    registration['route'] = route_arg.s
            
            for keyword in call_node.keywords:
                if keyword.arg == 'name':
                    if isinstance(keyword.value, ast.Constant):
                        registration['name'] = keyword.value.value
                    elif isinstance(keyword.value, ast.Str):
                        registration['name'] = keyword.value.s
            
            return registration
        except Exception:
            return None
    
    def _analyze_view_class(self, node: ast.ClassDef) -> None:
        """Analyze a view class."""
        view_info = {
            'name': node.name,
            'type': self._determine_view_type(node),
            'docstring': ast.get_docstring(node),
            'base_classes': [self._get_name(base) for base in node.bases],
            'methods': [],
            'serializer_class': None,
            'permission_classes': [],
            'router_info': None
        }
        
        # Extract class attributes
        self._extract_class_attributes(node, view_info)
        
        # Extract methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._analyze_view_method(item)
                view_info['methods'].append(method_info)
        
        # Match with router registration
        view_info['router_info'] = self._find_router_registration(node.name)
        
        if self._is_viewset(view_info['type']):
            self.analysis_result['viewsets'].append(view_info)
        else:
            self.analysis_result['views'].append(view_info)
    
    def _determine_view_type(self, node: ast.ClassDef) -> str:
        """Determine view type."""
        base_names = [self._get_name(base) for base in node.bases]
        
        if any('ViewSet' in base for base in base_names):
            return 'ViewSet'
        elif any('APIView' in base for base in base_names):
            return 'APIView'
        return 'Unknown'
    
    def _is_viewset(self, view_type: str) -> bool:
        return 'ViewSet' in view_type
    
    def _extract_class_attributes(self, node: ast.ClassDef, view_info: Dict[str, Any]) -> None:
        """Extract class attributes."""
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attr_name = target.id
                        attr_value = self._get_value_string(item.value)
                        
                        if attr_name == 'serializer_class':
                            view_info['serializer_class'] = attr_value
                        elif attr_name == 'permission_classes':
                            view_info['permission_classes'] = self._parse_class_list(item.value)
    
    def _parse_class_list(self, node: ast.AST) -> List[str]:
        """Parse list of class names."""
        result = []
        if isinstance(node, (ast.List, ast.Tuple)):
            for item in node.elts:
                result.append(self._get_name(item))
        return result
    
    def _analyze_view_method(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze view method."""
        return {
            'name': node.name,
            'http_method': self._infer_http_method(node.name),
            'docstring': ast.get_docstring(node),
            'query_params': self._extract_query_params(node),
            'status_codes': self._extract_status_codes(node)
        }
    
    def _infer_http_method(self, method_name: str) -> str:
        """Infer HTTP method from method name."""
        mapping = {
            'get': 'GET', 'post': 'POST', 'put': 'PUT', 
            'patch': 'PATCH', 'delete': 'DELETE',
            'list': 'GET', 'create': 'POST', 'retrieve': 'GET',
            'update': 'PUT', 'partial_update': 'PATCH', 'destroy': 'DELETE'
        }
        return mapping.get(method_name.lower(), 'UNKNOWN')
    
    def _extract_query_params(self, node: ast.FunctionDef) -> List[str]:
        """Extract query parameters."""
        params = []
        for child in ast.walk(node):
            if (isinstance(child, ast.Call) and 
                isinstance(child.func, ast.Attribute) and 
                child.func.attr == 'get' and
                isinstance(child.func.value, ast.Attribute) and
                child.func.value.attr == 'query_params'):
                
                if len(child.args) >= 1:
                    param_name = self._get_value_string(child.args[0])
                    params.append(param_name.strip('"\''))
        return params
    
    def _extract_status_codes(self, node: ast.FunctionDef) -> List[int]:
        """Extract status codes from Response calls."""
        codes = []
        for child in ast.walk(node):
            if (isinstance(child, ast.Call) and 
                isinstance(child.func, ast.Name) and 
                child.func.id == 'Response'):
                
                for keyword in child.keywords:
                    if keyword.arg == 'status':
                        status_value = self._get_value_string(keyword.value)
                        if 'HTTP_' in status_value:
                            # Map common status codes
                            status_mapping = {
                                'HTTP_200_OK': 200,
                                'HTTP_201_CREATED': 201,
                                'HTTP_400_BAD_REQUEST': 400,
                                'HTTP_404_NOT_FOUND': 404,
                                'HTTP_500_INTERNAL_SERVER_ERROR': 500
                            }
                            code = status_mapping.get(status_value.split('.')[-1], 200)
                            codes.append(code)
        return codes
    
    def _find_router_registration(self, view_name: str) -> Optional[Dict[str, Any]]:
        """Find router registration for view."""
        for registration in self.analysis_result['router_registrations']:
            if (registration.get('name') and 
                view_name.lower() in registration['name'].lower()):
                return registration
        return None
    
    def _match_router_registrations(self) -> None:
        """Match router registrations to views by analyzing decorators."""
        # Look for @router.register decorators above class definitions
        source_lines = []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                source_lines = f.readlines()
        except:
            return
        
        for i, line in enumerate(source_lines):
            if '@router.register(' in line and i + 1 < len(source_lines):
                # Extract route and name from decorator
                route_match = None
                name_match = None
                
                # Simple regex to extract route and name
                import re
                route_pattern = r'r["\']([^"\']*)["\']'
                name_pattern = r'name=["\']([^"\']*)["\']'
                
                route_match = re.search(route_pattern, line)
                name_match = re.search(name_pattern, line)
                
                if route_match or name_match:
                    # Find the class definition that follows
                    for j in range(i + 1, min(i + 10, len(source_lines))):
                        if source_lines[j].strip().startswith('class '):
                            class_name = source_lines[j].strip().split('class ')[1].split('(')[0]
                            
                            registration = {
                                'route': route_match.group(1) if route_match else None,
                                'name': name_match.group(1) if name_match else None,
                                'view_class': class_name
                            }
                            
                            # Update existing registrations or add new one
                            existing = None
                            for reg in self.analysis_result['router_registrations']:
                                if (reg.get('route') == registration['route'] or 
                                    reg.get('name') == registration['name']):
                                    existing = reg
                                    break
                            
                            if existing:
                                existing.update(registration)
                            else:
                                self.analysis_result['router_registrations'].append(registration)
                            break
    
    def _get_name(self, node: ast.AST) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)
    
    def _get_value_string(self, node: ast.AST) -> str:
        """Get string representation of value."""
        if isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Str):
            return repr(node.s)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_value_string(node.value)}.{node.attr}"
        elif isinstance(node, ast.List):
            items = [self._get_value_string(item) for item in node.elts]
            return f"[{', '.join(items)}]"
        elif isinstance(node, ast.Tuple):
            items = [self._get_value_string(item) for item in node.elts]
            return f"({', '.join(items)})"
        return str(type(node).__name__)


class ViewsDocumentationGenerator:
    """Generates API documentation from views analysis."""
    
    def __init__(self, api_dir: str = "api"):
        self.api_dir = Path(api_dir)
    
    def get_available_apps(self) -> List[str]:
        """Get apps with views.py files."""
        if not self.api_dir.exists():
            return []
        
        apps = []
        for item in self.api_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                if (item / 'views.py').exists():
                    apps.append(item.name)
        return sorted(apps)
    
    def analyze_app_views(self, app_name: str) -> Dict[str, Any]:
        """Analyze views for specific app."""
        views_file = self.api_dir / app_name / 'views.py'
        
        if not views_file.exists():
            raise ValueError(f"views.py not found for app '{app_name}'")
        
        analyzer = ViewAnalyzer(str(views_file))
        analysis = analyzer.analyze()
        
        return {
            'app_name': app_name,
            'analysis': analysis,
            'generated_at': datetime.now().isoformat()
        }
    
    def generate_documentation(self, app_analysis: Dict[str, Any]) -> str:
        """Generate markdown documentation."""
        app_name = app_analysis['app_name']
        analysis = app_analysis['analysis']
        
        md = [
            f"# {app_name.title()} App - API Documentation",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Source**: `api/{app_name}/views.py`",
            "",
            "## 📊 Summary",
            "",
            f"- **Views**: {len(analysis['views'])}",
            f"- **ViewSets**: {len(analysis['viewsets'])}",
            f"- **Routes**: {len(analysis['router_registrations'])}",
            ""
        ]
        
        # URL Patterns
        if analysis['router_registrations']:
            md.extend([
                "## 🛤️ URL Patterns",
                "",
                "| Route | Name |",
                "|-------|------|"
            ])
            
            for reg in analysis['router_registrations']:
                route = reg.get('route', 'N/A')
                name = reg.get('name', 'N/A')
                md.append(f"| `{route}` | {name} |")
            
            md.append("")
        
        # API Views
        if analysis['views']:
            md.extend(["## 🎯 API Views", ""])
            for view in analysis['views']:
                md.extend(self._generate_view_docs(view))
        
        # ViewSets
        if analysis['viewsets']:
            md.extend(["## 🔗 ViewSets", ""])
            for viewset in analysis['viewsets']:
                md.extend(self._generate_viewset_docs(viewset))
        
        return "\n".join(md)
    
    def _generate_view_docs(self, view: Dict[str, Any]) -> List[str]:
        """Generate docs for single view."""
        content = [f"### {view['name']}", ""]
        
        if view['docstring']:
            content.extend([f"**Description**: {view['docstring']}", ""])
        
        if view['router_info']:
            route = view['router_info'].get('route', 'N/A')
            content.extend([f"**Route**: `{route}`", ""])
        
        content.extend([
            f"**Type**: {view['type']}",
            f"**Serializer**: {view.get('serializer_class', 'Not specified')}",
            f"**Permissions**: {', '.join(view.get('permission_classes', ['Not specified']))}",
            ""
        ])
        
        # Methods
        if view['methods']:
            content.extend(["**Methods:**", ""])
            for method in view['methods']:
                if not method['name'].startswith('_'):
                    content.extend(self._generate_method_docs(method))
        
        content.append("")
        return content
    
    def _generate_viewset_docs(self, viewset: Dict[str, Any]) -> List[str]:
        """Generate docs for ViewSet."""
        content = [f"### {viewset['name']} (ViewSet)", ""]
        
        if viewset['docstring']:
            content.extend([f"**Description**: {viewset['docstring']}", ""])
        
        if viewset['router_info']:
            route = viewset['router_info'].get('route', 'N/A')
            content.extend([f"**Base Route**: `{route}`", ""])
        
        content.extend([
            f"**Serializer**: {viewset.get('serializer_class', 'Not specified')}",
            f"**Permissions**: {', '.join(viewset.get('permission_classes', ['Not specified']))}",
            ""
        ])
        
        # Standard actions
        standard_actions = ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']
        content.extend(["**Standard Actions:**"])
        
        for method in viewset['methods']:
            if method['name'] in standard_actions:
                http_method = method['http_method']
                content.append(f"- `{http_method}` - {method['name']}")
        
        content.append("")
        
        # Custom actions
        custom_methods = [m for m in viewset['methods'] 
                         if m['name'] not in standard_actions and not m['name'].startswith('_')]
        if custom_methods:
            content.extend(["**Custom Actions:**", ""])
            for method in custom_methods:
                content.extend(self._generate_method_docs(method))
        
        content.append("")
        return content
    
    def _generate_method_docs(self, method: Dict[str, Any]) -> List[str]:
        """Generate docs for method."""
        content = [f"#### `{method['http_method']}` - {method['name']}", ""]
        
        if method['docstring']:
            content.extend([f"**Description**: {method['docstring']}", ""])
        
        if method.get('query_params'):
            content.extend(["**Query Parameters:**"])
            for param in method['query_params']:
                content.append(f"- `{param}`")
            content.append("")
        
        if method.get('status_codes'):
            content.extend(["**Status Codes:**"])
            for code in set(method['status_codes']):
                content.append(f"- `{code}`")
            content.append("")
        
        return content
    
    def generate_app_documentation(self, app_name: str) -> str:
        """Generate complete API documentation for app."""
        print(f"📝 Generating API docs for '{app_name}'...")
        
        app_analysis = self.analyze_app_views(app_name)
        markdown_content = self.generate_documentation(app_analysis)
        
        output_file = self.api_dir / app_name / f"{app_name}_api_docs.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ Saved to: {output_file}")
        return str(output_file)
    
    def generate_all_documentation(self) -> List[str]:
        """Generate docs for all apps."""
        apps = self.get_available_apps()
        
        if not apps:
            print("❌ No apps with views.py found!")
            return []
        
        print(f"📚 Found {len(apps)} apps: {', '.join(apps)}")
        
        generated = []
        for app_name in apps:
            try:
                output_file = self.generate_app_documentation(app_name)
                generated.append(output_file)
            except Exception as e:
                print(f"❌ Failed for '{app_name}': {str(e)}")
        
        return generated


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate API documentation from Django views")
    
    parser.add_argument('--app', help='Generate docs for specific app')
    parser.add_argument('--all', action='store_true', help='Generate docs for all apps')
    parser.add_argument('--list', action='store_true', help='List available apps')
    
    args = parser.parse_args()
    
    generator = ViewsDocumentationGenerator()
    
    if args.list:
        apps = generator.get_available_apps()
        if apps:
            print(f"📋 Available apps ({len(apps)}):")
            for app in apps:
                print(f"  - {app}")
        else:
            print("❌ No apps found!")
        return 0
    
    if args.app:
        try:
            output_file = generator.generate_app_documentation(args.app)
            print(f"\n🎉 Documentation generated!")
            print(f"📄 Output: {output_file}")
            return 0
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return 1
    
    if args.all:
        try:
            output_files = generator.generate_all_documentation()
            print(f"\n🎉 Generated {len(output_files)} files!")
            for file_path in output_files:
                print(f"  - {file_path}")
            return 0
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return 1
    
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())