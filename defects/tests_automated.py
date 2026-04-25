"""
Automated conformance tests for BetaTrax API.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .metrics import classify_effectiveness
from .models import DefectReport, Employee, Product

def make_product(name='TestProduct'):
    return Product.objects.create(name=name)


def make_user(username):
    return User.objects.create_user(username=username, password='pass')


def make_employee(user, product, role):
    return Employee.objects.create(user=user, product=product, role=role)


def make_defect(product, status='New', **kwargs):
    defaults = {
        'title': 'Test Defect',
        'description': 'A description',
        'steps_to_reproduce': 'Step 1',
        'tester_id': 'tester1',
    }
    defaults.update(kwargs)
    return DefectReport.objects.create(product=product, status=status, **defaults)


# happy path
class AuthTests(TestCase):
    """POST /api/auth/login/ and POST /api/auth/logout/"""

    def setUp(self):
        self.client = APIClient()
        self.user = make_user('authuser')

    def test_login_returns_token(self):
        r = self.client.post('/api/auth/login/', {'username': 'authuser', 'password': 'pass'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('token', r.data)

    def test_logout_succeeds(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.post('/api/auth/logout/')
        self.assertEqual(r.status_code, 200)


class DefectListTests(TestCase):
    """GET and POST /api/defects/"""

    def setUp(self):
        self.client = APIClient()
        self.product = make_product()
        self.po_user = make_user('po')
        make_employee(self.po_user, self.product, 'ProductOwner')

    def test_post_submits_defect(self):
        r = self.client.post('/api/defects/', {
            'title': 'New Bug',
            'description': 'Desc',
            'steps_to_reproduce': 'Steps',
            'tester_id': 'tester1',
            'product': self.product.id,
        })
        self.assertEqual(r.status_code, 201)

    def test_get_lists_defects_for_employee(self):
        make_defect(self.product)
        self.client.force_authenticate(user=self.po_user)
        r = self.client.get('/api/defects/')
        self.assertEqual(r.status_code, 200)


class DefectDetailTests(TestCase):
    """GET /api/defects/<id>/"""

    def setUp(self):
        self.client = APIClient()
        self.product = make_product()
        self.po_user = make_user('po')
        make_employee(self.po_user, self.product, 'ProductOwner')
        self.defect = make_defect(self.product)

    def test_get_defect_detail(self):
        self.client.force_authenticate(user=self.po_user)
        r = self.client.get(f'/api/defects/{self.defect.id}/')
        self.assertEqual(r.status_code, 200)


class ApproveDefectTests(TestCase):
    """POST /api/defects/<id>/approve/"""

    def setUp(self):
        self.client = APIClient()
        self.product = make_product()
        self.po_user = make_user('po')
        make_employee(self.po_user, self.product, 'ProductOwner')
        self.defect = make_defect(self.product, status='New')

    def test_approve_defect(self):
        self.client.force_authenticate(user=self.po_user)
        r = self.client.post(f'/api/defects/{self.defect.id}/approve/', {
            'severity': 'Major',
            'priority': 'High',
            'backlog_item_id': 'ITEM-1',
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['new_status'], 'Open')


class RejectDefectTests(TestCase):
    """POST /api/defects/<id>/reject/"""

    def setUp(self):
        self.client = APIClient()
        self.product = make_product()
        self.po_user = make_user('po')
        make_employee(self.po_user, self.product, 'ProductOwner')
        self.defect = make_defect(self.product, status='New')

    def test_reject_defect(self):
        self.client.force_authenticate(user=self.po_user)
        r = self.client.post(f'/api/defects/{self.defect.id}/reject/', {
            'rejection_reason': 'Not a bug',
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['new_status'], 'Rejected')


class MarkDuplicateTests(TestCase):
    """POST /api/defects/<id>/mark-duplicate/"""

    def setUp(self):
        self.client = APIClient()
        self.product = make_product()
        self.po_user = make_user('po')
        make_employee(self.po_user, self.product, 'ProductOwner')
        self.original = make_defect(self.product, status='Open')
        self.duplicate = make_defect(self.product, status='New')

    def test_mark_duplicate(self):
        self.client.force_authenticate(user=self.po_user)
        r = self.client.post(f'/api/defects/{self.duplicate.id}/mark-duplicate/', {
            'duplicate_of_report_id': self.original.id,
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['new_status'], 'Duplicate')


class TakeResponsibilityTests(TestCase):
    """POST /api/defects/<id>/assign/"""

    def setUp(self):
        self.client = APIClient()
        self.product = make_product()
        self.dev_user = make_user('dev')
        make_employee(self.dev_user, self.product, 'Developer')
        self.defect = make_defect(self.product, status='Open')

    def test_take_responsibility(self):
        self.client.force_authenticate(user=self.dev_user)
        r = self.client.post(f'/api/defects/{self.defect.id}/assign/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['defect']['status'], 'Assigned')


class MarkFixedTests(TestCase):
    """POST /api/defects/<id>/mark-fixed/"""

    def setUp(self):
        self.client = APIClient()
        self.product = make_product()
        self.dev_user = make_user('dev')
        self.dev = make_employee(self.dev_user, self.product, 'Developer')
        self.defect = make_defect(self.product, status='Assigned')
        self.defect.assigned_developer = self.dev
        self.defect.save()

    def test_mark_fixed(self):
        self.client.force_authenticate(user=self.dev_user)
        r = self.client.post(f'/api/defects/{self.defect.id}/mark-fixed/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['defect']['status'], 'Fixed')


class MarkCannotReproduceTests(TestCase):
    """POST /api/defects/<id>/mark-cannot-reproduce/"""

    def setUp(self):
        self.client = APIClient()
        self.product = make_product()
        self.dev_user = make_user('dev')
        self.dev = make_employee(self.dev_user, self.product, 'Developer')
        self.defect = make_defect(self.product, status='Assigned')
        self.defect.assigned_developer = self.dev
        self.defect.save()

    def test_mark_cannot_reproduce(self):
        self.client.force_authenticate(user=self.dev_user)
        r = self.client.post(f'/api/defects/{self.defect.id}/mark-cannot-reproduce/', {
            'cannot_reproduce_reason': 'Could not replicate on test environment',
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['defect']['status'], 'Cannot Reproduce')


class ReopenDefectTests(TestCase):
    """POST /api/defects/<id>/reopen/"""

    def setUp(self):
        self.client = APIClient()
        self.product = make_product()
        self.po_user = make_user('po')
        make_employee(self.po_user, self.product, 'ProductOwner')
        self.defect = make_defect(self.product, status='Fixed')

    def test_reopen_defect(self):
        self.client.force_authenticate(user=self.po_user)
        r = self.client.post(f'/api/defects/{self.defect.id}/reopen/', {
            'reopen_reason': 'Still broken in production',
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['new_status'], 'Reopened')


class ResolveDefectTests(TestCase):
    """POST /api/defects/<id>/resolve/"""

    def setUp(self):
        self.client = APIClient()
        self.product = make_product()
        self.po_user = make_user('po')
        make_employee(self.po_user, self.product, 'ProductOwner')
        self.defect = make_defect(self.product, status='Fixed')

    def test_resolve_defect(self):
        self.client.force_authenticate(user=self.po_user)
        r = self.client.post(f'/api/defects/{self.defect.id}/resolve/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data['new_status'], 'Resolved')


class CommentsTests(TestCase):
    """GET and POST /api/defects/<id>/comments/"""

    def setUp(self):
        self.client = APIClient()
        self.product = make_product()
        self.po_user = make_user('po')
        make_employee(self.po_user, self.product, 'ProductOwner')
        self.defect = make_defect(self.product)

    def test_post_comment(self):
        self.client.force_authenticate(user=self.po_user)
        r = self.client.post(f'/api/defects/{self.defect.id}/comments/', {'text': 'Needs more info'})
        self.assertEqual(r.status_code, 201)

    def test_get_comments(self):
        self.client.force_authenticate(user=self.po_user)
        r = self.client.get(f'/api/defects/{self.defect.id}/comments/')
        self.assertEqual(r.status_code, 200)


class CreateProductTests(TestCase):
    """POST /api/products/"""

    def setUp(self):
        self.client = APIClient()
        self.product = make_product()
        self.po_user = make_user('po')
        make_employee(self.po_user, self.product, 'ProductOwner')

    def test_create_product(self):
        self.client.force_authenticate(user=self.po_user)
        r = self.client.post('/api/products/', {'name': 'NewProduct'})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data['name'], 'NewProduct')


class DeveloperEffectivenessTests(TestCase):
    """GET /api/employees/<id>/effectiveness/"""

    def setUp(self):
        self.client = APIClient()
        self.product = make_product()
        self.po_user = make_user('po')
        self.dev_user = make_user('dev')
        make_employee(self.po_user, self.product, 'ProductOwner')
        self.dev = make_employee(self.dev_user, self.product, 'Developer')

    def test_get_effectiveness(self):
        self.dev.defects_fixed_count = 20
        self.dev.defects_reopened_count = 0
        self.dev.save()
        self.client.force_authenticate(user=self.po_user)
        r = self.client.get(f'/api/employees/{self.dev.id}/effectiveness/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('classification', r.data)
        self.assertEqual(r.data['defects_fixed'], 20)

# classify_effectiveness tests using ecp + bva
# since the two inputs interact through ratio = reopened/fixed, we partition by output class
# ec1: insufficient data (fixed < 20)
# ec2: good (fixed >= 20, ratio < 1/32)
# ec3: fair (fixed >= 20, ratio is 1/32 up to but not including 1/8)
# ec4: poor (fixed >= 20, ratio >= 1/8)
#
# for bva we test boundary-1, boundary, boundary+1 for each condition
# condition 1 is the fixed_count cutoff at 20, so we test 19, 20, 21
# condition 2 is ratio < 1/32, nearest integers: (33,1)=0.030, (32,1)=0.03125, (31,1)=0.032
# condition 3 is ratio < 1/8, nearest integers: (20,2)=0.10, (24,3)=0.125, (20,3)=0.15
# each invalid class is tested on its own so nothing masks the failure cause

class ClassifyEffectivenessTests(TestCase):

    # tc1: typical insufficient case, well inside ec1
    def test_tc1_insufficient_typical(self):
        self.assertEqual(classify_effectiveness(10, 0), 'Insufficient data')

    # tc2: ec1 boundary, fixed=19 is one below the cutoff (b1)
    def test_tc2_insufficient_boundary_minus1(self):
        self.assertEqual(classify_effectiveness(19, 0), 'Insufficient data')

    # tc3: fixed=20 is exactly the cutoff, ratio=0 so falls into good (b2)
    def test_tc3_good_boundary_exact(self):
        self.assertEqual(classify_effectiveness(20, 0), 'Good')

    # tc4: fixed=21, one above cutoff, still good (b3)
    def test_tc4_good_boundary_plus1(self):
        self.assertEqual(classify_effectiveness(21, 0), 'Good')

    # tc5: ratio = 1/33 ~ 0.030, just under the 1/32 threshold so good (b4)
    def test_tc5_good_ratio_below_boundary(self):
        self.assertEqual(classify_effectiveness(33, 1), 'Good')

    # tc6: ratio = 1/32 exactly, not strictly less than so flips to fair (b5)
    def test_tc6_fair_ratio_at_boundary(self):
        self.assertEqual(classify_effectiveness(32, 1), 'Fair')

    # tc7: ratio = 1/31 ~ 0.032, just over 1/32 so fair (b6)
    def test_tc7_fair_ratio_above_boundary(self):
        self.assertEqual(classify_effectiveness(31, 1), 'Fair')

    # tc8: ratio = 0.10, just under 1/8 threshold so still fair (b7)
    def test_tc8_fair_ratio_below_upper_boundary(self):
        self.assertEqual(classify_effectiveness(20, 2), 'Fair')

    # tc9: ratio = 3/24 = 0.125 = 1/8 exactly, not strictly less than so flips to poor (b8)
    def test_tc9_poor_ratio_at_boundary(self):
        self.assertEqual(classify_effectiveness(24, 3), 'Poor')

    # tc10: ratio = 0.15, just over 1/8 so poor (b9)
    def test_tc10_poor_ratio_above_boundary(self):
        self.assertEqual(classify_effectiveness(20, 3), 'Poor')
