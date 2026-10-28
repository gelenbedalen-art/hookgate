// SPDX-License-Identifier: MIT
// Differential evidence against an unmodified, pinned upstream Hooks.sol library.
// Run: npm install && node canonical-oracle.cjs /path/to/v4-core
const fs=require('fs'),path=require('path'),crypto=require('crypto'),cp=require('child_process');
const solc=require('solc'),ganache=require('ganache'),{ethers}=require('ethers');
async function main(){
 const root=path.resolve(process.argv[2]||'v4-core');
 const commit=cp.execFileSync('git',['-C',root,'rev-parse','HEAD'],{encoding:'utf8'}).trim();
 const source=`// SPDX-License-Identifier: MIT
 pragma solidity ^0.8.24;
 import {Hooks} from "src/libraries/Hooks.sol";
 import {IHooks} from "src/interfaces/IHooks.sol";
 contract Oracle {
 function batch(uint160 start,uint160 count,uint24 fee) external pure returns(bytes memory out){
 out=new bytes(count);for(uint160 i;i<count;i++){
 address a=address(uint160((1<<100)|(start+i)));
 out[i]=Hooks.isValidHookAddress(IHooks(a),fee)?bytes1(0x01):bytes1(0x00);
 }}
 function one(address a,uint24 f) external pure returns(bool){return Hooks.isValidHookAddress(IHooks(a),f);}
 }`;
 const input={language:'Solidity',sources:{'Oracle.sol':{content:source}},settings:{optimizer:{enabled:true,runs:200},evmVersion:'shanghai',outputSelection:{'*':{'*':['abi','evm.bytecode.object']}}}};
 const output=JSON.parse(solc.compile(JSON.stringify(input),{import:(p)=>{
  try{return {contents:fs.readFileSync(path.join(root,p),'utf8')}}catch{return {error:'Missing '+p}}
 }}));
 const errors=(output.errors||[]).filter(e=>e.severity==='error');if(errors.length)throw Error(errors.map(x=>x.formattedMessage).join('\n'));
 const artifact=output.contracts['Oracle.sol'].Oracle;
 const local=ganache.provider({logging:{quiet:true},chain:{hardfork:'shanghai'},miner:{blockGasLimit:60000000}});
 const provider=new ethers.BrowserProvider(local), signer=await provider.getSigner();
 const contract=await new ethers.ContractFactory(artifact.abi,artifact.evm.bytecode.object,signer).deploy();await contract.waitForDeployment();
 const expected=JSON.parse(cp.execFileSync('python3',['-c',`import json\nfrom hookgate import address_valid\nprint(json.dumps([[int(address_valid('0x'+format((1<<100)|i,'040x'),f)) for i in range(16384)] for f in [3000,0x800000]]))`],{cwd:__dirname,encoding:'utf8'}));
 let checked=0;for(let fi=0;fi<2;fi++)for(let start=0;start<16384;start+=512){
  const raw=ethers.getBytes(await contract.batch(start,512,fi?0x800000:3000,{gasLimit:55000000}));
  for(let j=0;j<512;j++){if(raw[j]!==expected[fi][start+j])throw Error('Mismatch '+start+' '+j);checked++;}
 }
 for(const [a,f,expected] of [[ethers.ZeroAddress,3000,true],[ethers.ZeroAddress,0x800000,false],['0x0000000000000000000000000000000000000080',0x800001,true]]){
  if(await contract.one(a,f)!==expected)throw Error('Boundary mismatch');checked++;
 }
 const report={mode:'local_evm_differential',timestamp:new Date().toISOString(),upstream:'https://github.com/Uniswap/v4-core',commit,source_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'src/libraries/Hooks.sol'))).digest('hex'),compiler:solc.version(),evm:'Ganache Shanghai; local ephemeral chain only',cases:checked,mismatches:0,coverage:'All 16384 nonzero-address permission masks at static and dynamic fees, plus 3 boundaries',limitations:['Only Hooks.isValidHookAddress is checked; no PoolManager swaps or arbitrary hook bytecode were executed.','Local test funds have no monetary value.']};
 console.log(JSON.stringify(report,null,2));await local.disconnect();
}
main().catch(e=>{console.error(e.message);process.exitCode=1});
