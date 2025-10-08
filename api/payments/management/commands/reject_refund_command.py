from django.core.management.base import BaseCommand
from api.payments.services import RefundService
from api.users.models import User

class Command(BaseCommand):
    help = 'Rejects a refund request'

    def add_arguments(self, parser):
        parser.add_argument('refund_id', type=str, help='The ID of the refund to reject')
        parser.add_argument('admin_username', type=str, help='The username of the admin rejecting the refund')
        parser.add_argument('rejection_reason', type=str, help='The reason for rejecting the refund')

    def handle(self, *args, **options):
        refund_id = options['refund_id']
        admin_username = options['admin_username']
        rejection_reason = options['rejection_reason']

        try:
            admin_user = User.objects.get(username=admin_username)
            service = RefundService()
            service.reject_refund(refund_id, admin_user, rejection_reason)
            self.stdout.write(self.style.SUCCESS(f'Successfully rejected refund {refund_id}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Admin user {admin_username} does not exist'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error rejecting refund: {e}'))