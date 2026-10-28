# SPDX-License-Identifier: MIT
import unittest
from hookgate import FLAGS, NAMES, DYNAMIC_FEE, address_valid, inspect


def manifest(mask=128, fee=3000, high=1<<100):
    return {'address': '0x' + format(high | mask, '040x'), 'fee': fee,
            'permissions': {name: bool(mask & flag) for name, flag in FLAGS.items()}}


class GateTests(unittest.TestCase):
    def test_valid_before_swap(self): self.assertTrue(inspect(manifest())['pass'])
    def test_each_single_bit_mismatch(self):
        for name in NAMES:
            with self.subTest(name=name):
                m = manifest(); m['permissions'][name] = not m['permissions'][name]
                self.assertEqual(inspect(m)['permission_mismatches'], [name])
                self.assertFalse(inspect(m)['pass'])
    def test_four_delta_dependencies(self):
        for child, parent in [('beforeSwapReturnDelta','beforeSwap'), ('afterSwapReturnDelta','afterSwap'),
            ('afterAddLiquidityReturnDelta','afterAddLiquidity'), ('afterRemoveLiquidityReturnDelta','afterRemoveLiquidity')]:
            self.assertFalse(inspect(manifest(FLAGS[child]))['pass'])
            self.assertTrue(inspect(manifest(FLAGS[child] | FLAGS[parent]))['pass'])
    def test_zero_hook_static(self): self.assertTrue(inspect(manifest(0, high=0))['pass'])
    def test_zero_hook_dynamic_rejected(self): self.assertFalse(inspect(manifest(0, DYNAMIC_FEE, high=0))['pass'])
    def test_nonzero_no_flags_static_rejected(self): self.assertFalse(inspect(manifest(0))['pass'])
    def test_nonzero_no_flags_dynamic(self): self.assertTrue(inspect(manifest(0, DYNAMIC_FEE))['pass'])
    def test_dynamic_fee_requires_exact_constant(self):
        self.assertFalse(inspect(manifest(0, DYNAMIC_FEE + 1))['pass'])
    def test_invalid_fee_range_separate_from_address(self):
        m = manifest(128, 1_000_001)
        self.assertTrue(address_valid(m['address'], m['fee']))
        self.assertFalse(inspect(m)['pool_fee_valid'])
    def test_uint24_rejected(self):
        for fee in [True, -1, 1<<24, '3000']:
            with self.assertRaises(ValueError): inspect(manifest(fee=fee))
    def test_strict_address(self):
        for address in ['0x80', '0x'+'z'*40, None, '0x'+'0'*41]:
            m=manifest();m['address']=address
            with self.assertRaises(ValueError): inspect(m)
    def test_incomplete_manifest(self):
        m=manifest();del m['permissions']['beforeSwap']
        with self.assertRaises(ValueError): inspect(m)
    def test_unknown_permission(self):
        m=manifest();m['permissions']['mystery']=False
        with self.assertRaises(ValueError): inspect(m)
    def test_boolean_only(self):
        m=manifest();m['permissions']['beforeSwap']='true'
        with self.assertRaises(ValueError): inspect(m)
    def test_high_bits_do_not_change_mask(self):
        self.assertEqual(inspect(manifest(high=1<<150))['encoded_mask_hex'], '0x80')
    def test_stable_digest(self):
        m=manifest();self.assertEqual(inspect(m)['manifest_sha256'],inspect(dict(reversed(list(m.items()))))['manifest_sha256'])
    def test_manifest_not_modified(self):
        m=manifest();before=repr(m);inspect(m);self.assertEqual(repr(m),before)


if __name__ == '__main__': unittest.main(verbosity=2)
