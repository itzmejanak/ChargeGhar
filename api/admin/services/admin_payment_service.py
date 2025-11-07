"""
Admin Payment Service
============================================================

Service for managing payment methods, rental packages, and transactions.

Created: 2025-11-06
Updated: 2025-11-08 - Added transactions list
"""
from typing import Dict, Any, List
from datetime import timedelta
from django.db.models import Q
from django.db import transaction
from django.utils import timezone

from api.common.services import BaseService
from api.common.services.base import ServiceException
from api.common.utils.helpers import paginate_queryset
from api.payments.models import PaymentMethod, Transaction, WalletTransaction
from api.rentals.models import RentalPackage


class AdminPaymentService(BaseService):
    """Service for admin payment and package management operations"""
    
    # ============================================================
    # Payment Method Management
    # ============================================================
    
    def get_payment_methods(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get list of payment methods with filters"""
        try:
            queryset = PaymentMethod.objects.all().order_by('-created_at')
            
            if not filters:
                filters = {}
            
            # Apply filters
            if 'is_active' in filters and filters['is_active'] is not None:
                queryset = queryset.filter(is_active=filters['is_active'])
            
            if filters.get('gateway'):
                queryset = queryset.filter(gateway__icontains=filters['gateway'])
            
            if filters.get('search'):
                search_term = filters['search']
                queryset = queryset.filter(
                    Q(name__icontains=search_term) |
                    Q(gateway__icontains=search_term)
                )
            
            # Pagination
            page = filters.get('page', 1)
            page_size = filters.get('page_size', 20)
            
            return paginate_queryset(queryset, page, page_size)
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get payment methods")
    
    def get_payment_method(self, method_id: str):
        """Get single payment method by ID"""
        try:
            return PaymentMethod.objects.get(id=method_id)
        except PaymentMethod.DoesNotExist:
            raise ServiceException(
                detail="Payment method not found",
                code="payment_method_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to get payment method")
    
    @transaction.atomic
    def create_payment_method(self, data: Dict[str, Any]) -> PaymentMethod:
        """Create a new payment method"""
        try:
            payment_method = PaymentMethod.objects.create(
                name=data['name'],
                gateway=data['gateway'],
                is_active=data.get('is_active', True),
                configuration=data.get('configuration', {}),
                min_amount=data['min_amount'],
                max_amount=data.get('max_amount'),
                supported_currencies=data.get('supported_currencies', ['NPR'])
            )
            
            return payment_method
            
        except Exception as e:
            self.handle_service_error(e, "Failed to create payment method")
    
    @transaction.atomic
    def update_payment_method(self, method_id: str, data: Dict[str, Any]) -> PaymentMethod:
        """Update an existing payment method"""
        try:
            payment_method = self.get_payment_method(method_id)
            
            # Update fields
            if 'name' in data:
                payment_method.name = data['name']
            if 'gateway' in data:
                payment_method.gateway = data['gateway']
            if 'is_active' in data:
                payment_method.is_active = data['is_active']
            if 'configuration' in data:
                payment_method.configuration = data['configuration']
            if 'min_amount' in data:
                payment_method.min_amount = data['min_amount']
            if 'max_amount' in data:
                payment_method.max_amount = data['max_amount']
            if 'supported_currencies' in data:
                payment_method.supported_currencies = data['supported_currencies']
            
            payment_method.save()
            return payment_method
            
        except Exception as e:
            self.handle_service_error(e, "Failed to update payment method")
    
    @transaction.atomic
    def delete_payment_method(self, method_id: str) -> Dict[str, Any]:
        """Delete (soft delete) a payment method"""
        try:
            payment_method = self.get_payment_method(method_id)
            
            # Soft delete by setting is_active to False
            payment_method.is_active = False
            payment_method.save()
            
            return {
                'id': str(payment_method.id),
                'name': payment_method.name,
                'deleted': True
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to delete payment method")
    
    # ============================================================
    # Rental Package Management
    # ============================================================
    
    def get_rental_packages(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get list of rental packages with filters"""
        try:
            queryset = RentalPackage.objects.all().order_by('price')
            
            if not filters:
                filters = {}
            
            # Apply filters
            if 'is_active' in filters and filters['is_active'] is not None:
                queryset = queryset.filter(is_active=filters['is_active'])
            
            if filters.get('package_type'):
                queryset = queryset.filter(package_type=filters['package_type'])
            
            if filters.get('payment_model'):
                queryset = queryset.filter(payment_model=filters['payment_model'])
            
            if filters.get('search'):
                search_term = filters['search']
                queryset = queryset.filter(
                    Q(name__icontains=search_term) |
                    Q(description__icontains=search_term)
                )
            
            # Pagination
            page = filters.get('page', 1)
            page_size = filters.get('page_size', 20)
            
            return paginate_queryset(queryset, page, page_size)
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get rental packages")
    
    def get_rental_package(self, package_id: str):
        """Get single rental package by ID"""
        try:
            return RentalPackage.objects.get(id=package_id)
        except RentalPackage.DoesNotExist:
            raise ServiceException(
                detail="Rental package not found",
                code="rental_package_not_found"
            )
        except Exception as e:
            self.handle_service_error(e, "Failed to get rental package")
    
    @transaction.atomic
    def create_rental_package(self, data: Dict[str, Any]) -> RentalPackage:
        """Create a new rental package"""
        try:
            rental_package = RentalPackage.objects.create(
                name=data['name'],
                description=data['description'],
                duration_minutes=data['duration_minutes'],
                price=data['price'],
                package_type=data['package_type'],
                payment_model=data['payment_model'],
                is_active=data.get('is_active', True),
                package_metadata=data.get('package_metadata', {})
            )
            
            return rental_package
            
        except Exception as e:
            self.handle_service_error(e, "Failed to create rental package")
    
    @transaction.atomic
    def update_rental_package(self, package_id: str, data: Dict[str, Any]) -> RentalPackage:
        """Update an existing rental package"""
        try:
            rental_package = self.get_rental_package(package_id)
            
            # Update fields
            if 'name' in data:
                rental_package.name = data['name']
            if 'description' in data:
                rental_package.description = data['description']
            if 'duration_minutes' in data:
                rental_package.duration_minutes = data['duration_minutes']
            if 'price' in data:
                rental_package.price = data['price']
            if 'package_type' in data:
                rental_package.package_type = data['package_type']
            if 'payment_model' in data:
                rental_package.payment_model = data['payment_model']
            if 'is_active' in data:
                rental_package.is_active = data['is_active']
            if 'package_metadata' in data:
                rental_package.package_metadata = data['package_metadata']
            
            rental_package.save()
            return rental_package
            
        except Exception as e:
            self.handle_service_error(e, "Failed to update rental package")
    
    @transaction.atomic
    def delete_rental_package(self, package_id: str) -> Dict[str, Any]:
        """Delete (soft delete) a rental package"""
        try:
            rental_package = self.get_rental_package(package_id)
            
            # Soft delete by setting is_active to False
            rental_package.is_active = False
            rental_package.save()
            
            return {
                'id': str(rental_package.id),
                'name': rental_package.name,
                'deleted': True
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to delete rental package")
    
    # ============================================================
    # Transactions Management
    # ============================================================
    
    def get_transactions(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get combined list of Transactions and WalletTransactions
        
        Args:
            filters: Dictionary containing filter parameters
                - status: Filter by transaction status (for Transaction)
                - transaction_type: Filter by type (TOPUP, RENTAL, etc.)
                - user_id: Filter by user ID
                - recent: 'today', '24h', '7d', '30d' for recent transactions
                - start_date: Filter transactions after this date
                - end_date: Filter transactions before this date
                - include_wallet: Include wallet transactions (default: True)
                - search: Search by transaction_id or user name
                - page: Page number
                - page_size: Items per page
                
        Returns:
            Dict with combined results and pagination
        """
        try:
            if not filters:
                filters = {}
            
            # Get Transactions
            transaction_queryset = Transaction.objects.select_related(
                'user', 'related_rental'
            ).order_by('-created_at')
            
            # Get WalletTransactions (if included)
            include_wallet = filters.get('include_wallet', True)
            wallet_transaction_queryset = None
            if include_wallet:
                wallet_transaction_queryset = WalletTransaction.objects.select_related(
                    'wallet__user', 'transaction'
                ).order_by('-created_at')
            
            # Apply common filters
            # Recent filter
            if filters.get('recent'):
                now = timezone.now()
                recent_type = filters['recent']
                
                if recent_type == 'today':
                    filter_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
                elif recent_type == '24h':
                    filter_time = now - timedelta(hours=24)
                elif recent_type == '7d':
                    filter_time = now - timedelta(days=7)
                elif recent_type == '30d':
                    filter_time = now - timedelta(days=30)
                else:
                    filter_time = None
                
                if filter_time:
                    transaction_queryset = transaction_queryset.filter(created_at__gte=filter_time)
                    if wallet_transaction_queryset:
                        wallet_transaction_queryset = wallet_transaction_queryset.filter(created_at__gte=filter_time)
            
            # Date range filters
            if filters.get('start_date'):
                transaction_queryset = transaction_queryset.filter(created_at__gte=filters['start_date'])
                if wallet_transaction_queryset:
                    wallet_transaction_queryset = wallet_transaction_queryset.filter(created_at__gte=filters['start_date'])
            
            if filters.get('end_date'):
                transaction_queryset = transaction_queryset.filter(created_at__lte=filters['end_date'])
                if wallet_transaction_queryset:
                    wallet_transaction_queryset = wallet_transaction_queryset.filter(created_at__lte=filters['end_date'])
            
            # User filter
            if filters.get('user_id'):
                transaction_queryset = transaction_queryset.filter(user_id=filters['user_id'])
                if wallet_transaction_queryset:
                    wallet_transaction_queryset = wallet_transaction_queryset.filter(wallet__user_id=filters['user_id'])
            
            # Search filter
            if filters.get('search'):
                search_term = filters['search']
                transaction_queryset = transaction_queryset.filter(
                    Q(transaction_id__icontains=search_term) |
                    Q(user__username__icontains=search_term) |
                    Q(user__email__icontains=search_term)
                )
                if wallet_transaction_queryset:
                    wallet_transaction_queryset = wallet_transaction_queryset.filter(
                        Q(wallet__user__username__icontains=search_term) |
                        Q(wallet__user__email__icontains=search_term) |
                        Q(description__icontains=search_term)
                    )
            
            # Transaction-specific filters
            if filters.get('status'):
                transaction_queryset = transaction_queryset.filter(status=filters['status'])
            
            if filters.get('transaction_type'):
                transaction_queryset = transaction_queryset.filter(transaction_type=filters['transaction_type'])
            
            if filters.get('payment_method_type'):
                transaction_queryset = transaction_queryset.filter(payment_method_type=filters['payment_method_type'])
            
            # WalletTransaction-specific filters
            if filters.get('wallet_transaction_type') and wallet_transaction_queryset:
                wallet_transaction_queryset = wallet_transaction_queryset.filter(
                    transaction_type=filters['wallet_transaction_type']
                )
            
            # Combine querysets into a unified list
            combined_transactions = []
            
            # Add Transactions
            for txn in transaction_queryset:
                combined_transactions.append({
                    'source': 'transaction',
                    'id': str(txn.id),
                    'transaction_id': txn.transaction_id,
                    'user': {
                        'id': str(txn.user.id),
                        'username': txn.user.username,
                        'email': txn.user.email
                    },
                    'type': txn.transaction_type,
                    'amount': float(txn.amount),
                    'currency': txn.currency,
                    'status': txn.status,
                    'payment_method_type': txn.payment_method_type,
                    'related_rental_id': str(txn.related_rental.id) if txn.related_rental else None,
                    'gateway_reference': txn.gateway_reference,
                    'created_at': txn.created_at,
                    'description': f"{txn.get_transaction_type_display()} - {txn.get_status_display()}"
                })
            
            # Add WalletTransactions
            if wallet_transaction_queryset:
                for wtxn in wallet_transaction_queryset:
                    combined_transactions.append({
                        'source': 'wallet_transaction',
                        'id': str(wtxn.id),
                        'transaction_id': str(wtxn.transaction.transaction_id) if wtxn.transaction else f"WT-{wtxn.id}",
                        'user': {
                            'id': str(wtxn.wallet.user.id),
                            'username': wtxn.wallet.user.username,
                            'email': wtxn.wallet.user.email
                        },
                        'type': wtxn.transaction_type,
                        'amount': float(wtxn.amount),
                        'currency': wtxn.wallet.currency,
                        'status': 'COMPLETED',  # Wallet transactions are always completed
                        'payment_method_type': 'WALLET',
                        'balance_before': float(wtxn.balance_before),
                        'balance_after': float(wtxn.balance_after),
                        'created_at': wtxn.created_at,
                        'description': wtxn.description
                    })
            
            # Sort combined list by created_at (most recent first)
            combined_transactions.sort(key=lambda x: x['created_at'], reverse=True)
            
            # Manual pagination
            page = filters.get('page', 1)
            page_size = filters.get('page_size', 20)
            
            total_count = len(combined_transactions)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            
            paginated_results = combined_transactions[start_index:end_index]
            
            return {
                'results': paginated_results,
                'pagination': {
                    'total_count': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            }
            
        except Exception as e:
            self.handle_service_error(e, "Failed to get transactions")
