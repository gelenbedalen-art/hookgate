# HookGate

An offline CI gate for Uniswap v4 deployment manifests. It compares all 14 explicitly declared hook permissions with the flags encoded in a proposed address, checks return-delta dependencies and pool-fee validity, and exits nonzero on inconsistency.

This is a configuration gate, not a security analyzer or a replacement for Uniswap BaseHook validation. Its proposed value is reviewable JSON evidence and a reproducible differential regression suite against pinned upstream Solidity. Existing flag decoders and hook analyzers already exist; novelty is not claimed for decoding address bits.

## Run without network access or paid services

```sh
python3 -m unittest -v test_hookgate
python3 hookgate.py sample-manifest.json
```

Python 3.11+, standard library only. Exit 0 is a configuration pass; exit 2 is invalid configuration/input. The example address is synthetic and is NOT a deployed contract. No wallet, RPC, deployment, signature or funds are used.

## Reproduce the canonical Solidity comparison

```sh
npm install
git clone https://github.com/Uniswap/v4-core.git v4-core
git -C v4-core checkout bea7f6d1c11cd5dc4f0d5151ffa37a1c239feee6
node canonical-oracle.cjs ./v4-core
```

The script compiles an Oracle that IMPORTS the unmodified upstream Hooks.sol library. It invokes Hooks.isValidHookAddress on an ephemeral local Ganache EVM, and compares the returned truth values with this Python implementation for every 14-bit permission mask with static and dynamic fees. It also checks zero-address and nonexact dynamic-fee boundaries. Canonical dependencies retain their upstream licenses; they are fetched separately, not relicensed under this project's MIT license.

## Recorded evidence — 28 October 2026

17 Python tests passed (one test additionally flips each of the 14 permissions independently). The local Solidity differential completed **32,771 cases with zero mismatches**. This does NOT mean 32,771 smart-contract security tests, swaps or production transactions.

```json
{
  "mode": "local_evm_differential",
  "timestamp": "2026-10-28T10:03:16.274Z",
  "upstream": "https://github.com/Uniswap/v4-core",
  "commit": "bea7f6d1c11cd5dc4f0d5151ffa37a1c239feee6",
  "source_sha256": "297d577998cdede64d48b47b12f15e4f442eea032fbb9676bb3c2f89da89b83c",
  "compiler": "0.8.38+commit.1835d247.Emscripten.clang",
  "evm": "Ganache Shanghai; local ephemeral chain only",
  "cases": 32771,
  "mismatches": 0,
  "coverage": "All 16384 nonzero-address permission masks at static and dynamic fees, plus 3 boundaries",
  "limitations": [
    "Only Hooks.isValidHookAddress is checked; no PoolManager swaps or arbitrary hook bytecode were executed.",
    "Local test funds have no monetary value."
  ]
}

```

```text
test_boolean_only (test_hookgate.GateTests.test_boolean_only) ... ok
test_dynamic_fee_requires_exact_constant (test_hookgate.GateTests.test_dynamic_fee_requires_exact_constant) ... ok
test_each_single_bit_mismatch (test_hookgate.GateTests.test_each_single_bit_mismatch) ... ok
test_four_delta_dependencies (test_hookgate.GateTests.test_four_delta_dependencies) ... ok
test_high_bits_do_not_change_mask (test_hookgate.GateTests.test_high_bits_do_not_change_mask) ... ok
test_incomplete_manifest (test_hookgate.GateTests.test_incomplete_manifest) ... ok
test_invalid_fee_range_separate_from_address (test_hookgate.GateTests.test_invalid_fee_range_separate_from_address) ... ok
test_manifest_not_modified (test_hookgate.GateTests.test_manifest_not_modified) ... ok
test_nonzero_no_flags_dynamic (test_hookgate.GateTests.test_nonzero_no_flags_dynamic) ... ok
test_nonzero_no_flags_static_rejected (test_hookgate.GateTests.test_nonzero_no_flags_static_rejected) ... ok
test_stable_digest (test_hookgate.GateTests.test_stable_digest) ... ok
test_strict_address (test_hookgate.GateTests.test_strict_address) ... ok
test_uint24_rejected (test_hookgate.GateTests.test_uint24_rejected) ... ok
test_unknown_permission (test_hookgate.GateTests.test_unknown_permission) ... ok
test_valid_before_swap (test_hookgate.GateTests.test_valid_before_swap) ... ok
test_zero_hook_dynamic_rejected (test_hookgate.GateTests.test_zero_hook_dynamic_rejected) ... ok
test_zero_hook_static (test_hookgate.GateTests.test_zero_hook_static) ... ok

----------------------------------------------------------------------
Ran 17 tests in 0.002s

OK
```

## Explicit manifest example

Save the following as sample-manifest.json, then run the CLI above. Change beforeSwap to false to reproduce a failing gate.

```json
{
  "address": "0x0000000000000000000000000000000000000080",
  "fee": 3000,
  "permissions": {
    "beforeInitialize": false,
    "afterInitialize": false,
    "beforeAddLiquidity": false,
    "afterAddLiquidity": false,
    "beforeRemoveLiquidity": false,
    "afterRemoveLiquidity": false,
    "beforeSwap": true,
    "afterSwap": false,
    "beforeDonate": false,
    "afterDonate": false,
    "beforeSwapReturnDelta": false,
    "afterSwapReturnDelta": false,
    "afterAddLiquidityReturnDelta": false,
    "afterRemoveLiquidityReturnDelta": false
  }
}
```

## Limits

- Reads declared JSON, not getHookPermissions from arbitrary source or a deployed contract.
- Does not prove callback ABI, runtime bytecode, access control, upgradeability, swaps, PoolManager execution or economic safety.
- A passing configuration is never an audit, certification or protocol endorsement.
- The dynamic fee marker is exactly 0x800000; the separate static fee cap is 1,000,000.
- Dependency parity is pinned to the recorded upstream commit. Upstream changes require revalidation.

## Proposed grant scope (not delivered)

USD 1,500; three milestones over four weeks: 20h × $25 for manifest schema and Foundry/Hardhat artifact adapters; 24h × $25 for CI integration, canonical dependency pinning and boundary regressions; 16h × $25 for worked examples, release documentation and a developer walkthrough. All initial milestones can be demonstrated locally without funded accounts or mainnet deployments. Payment asset and final terms must be agreed with the foundation.

Maintainer: gelenbedalen / KalenSolves. Solo developer responsible for architecture, implementation review, integration, validation and delivery. Pre-launch prototype; no users, TVL, revenue, funding or external audit claimed.

## Sources

- https://github.com/Uniswap/v4-core/blob/bea7f6d1c11cd5dc4f0d5151ffa37a1c239feee6/src/libraries/Hooks.sol
- https://developers.uniswap.org/docs/protocols/v4/concepts/hooks
- https://developers.uniswap.org/docs/protocols/v4/guides/hooks/hook-deployment

## License for original project code

MIT License

Copyright (c) 2026 gelenbedalen

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
