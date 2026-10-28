#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Offline pre-deployment permission gate for Uniswap v4. Not a security audit."""
import argparse
import hashlib
import json
import re

NAMES = ('beforeInitialize', 'afterInitialize', 'beforeAddLiquidity', 'afterAddLiquidity',
         'beforeRemoveLiquidity', 'afterRemoveLiquidity', 'beforeSwap', 'afterSwap',
         'beforeDonate', 'afterDonate', 'beforeSwapReturnDelta', 'afterSwapReturnDelta',
         'afterAddLiquidityReturnDelta', 'afterRemoveLiquidityReturnDelta')
FLAGS = {name: 1 << (13-i) for i, name in enumerate(NAMES)}
PARENTS = {'beforeSwapReturnDelta': 'beforeSwap', 'afterSwapReturnDelta': 'afterSwap',
           'afterAddLiquidityReturnDelta': 'afterAddLiquidity',
           'afterRemoveLiquidityReturnDelta': 'afterRemoveLiquidity'}
DYNAMIC_FEE = 0x800000
ALL = (1 << 14) - 1


def parse_address(address):
    if not isinstance(address, str) or not re.fullmatch(r'0x[0-9a-fA-F]{40}', address):
        raise ValueError('address must be exactly 20 hexadecimal bytes')
    return int(address, 16)


def validate_fee(fee):
    if type(fee) is not int or fee < 0 or fee >= 1 << 24:
        raise ValueError('fee must be a uint24 integer')


def address_valid(address, fee):
    """Exact Hooks.isValidHookAddress predicate, separate from fee range validation."""
    value = parse_address(address)
    validate_fee(fee)
    for child, parent in PARENTS.items():
        if value & FLAGS[child] and not value & FLAGS[parent]:
            return False
    return fee != DYNAMIC_FEE if value == 0 else bool(value & ALL) or fee == DYNAMIC_FEE


def inspect(manifest):
    if not isinstance(manifest, dict):
        raise ValueError('manifest must be an object')
    address, fee, declared = manifest.get('address'), manifest.get('fee'), manifest.get('permissions')
    value = parse_address(address)
    validate_fee(fee)
    if not isinstance(declared, dict) or set(declared) != set(NAMES):
        raise ValueError('permissions must contain exactly all 14 named boolean fields')
    if any(type(v) is not bool for v in declared.values()):
        raise ValueError('permissions must be booleans, not strings or numbers')
    encoded = {name: bool(value & flag) for name, flag in FLAGS.items()}
    mismatches = [name for name in NAMES if declared[name] != encoded[name]]
    dependencies = [{'permission': child, 'requires': parent}
                    for child, parent in PARENTS.items() if encoded[child] and not encoded[parent]]
    predicate = address_valid(address, fee)
    fee_valid = fee == DYNAMIC_FEE or fee <= 1_000_000
    no_hook_permissions = value == 0 and any(declared.values())
    canonical = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()
    passed = predicate and fee_valid and not mismatches and not no_hook_permissions
    return {'schema_version': 1, 'mode': 'offline_manifest_check', 'pass': passed,
            'manifest_sha256': hashlib.sha256(canonical).hexdigest(),
            'address': address, 'fee': fee, 'dynamic_fee': fee == DYNAMIC_FEE,
            'encoded_mask_hex': hex(value & ALL), 'encoded_permissions': encoded,
            'permission_mismatches': mismatches, 'invalid_dependencies': dependencies,
            'canonical_address_predicate': predicate, 'pool_fee_valid': fee_valid,
            'limitations': ['Checks an explicit manifest; does not extract permissions from arbitrary Solidity source.',
                'Does not prove deployed bytecode, callback implementation, PoolManager behavior or economic safety.',
                'No RPC, wallet, signature, deployment or transaction is performed.',
                'A pass is a configuration check, never an audit or approval.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', help='JSON file with address, uint24 fee and all 14 boolean permissions')
    args = parser.parse_args()
    try:
        with open(args.manifest) as f:
            result = inspect(json.load(f))
        print(json.dumps(result, indent=2))
        return 0 if result['pass'] else 2
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == '__main__': raise SystemExit(main())
