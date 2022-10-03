# Proxy Pattern

## Idea

Upgrade your contract: User -> Proxy -> ~~ Implementation v1 ~~  
                                    -> ~~ Implementation v2 ~~  
                                     ->  Implementation v3

The user can always interact with the same contract (the Proxy) while the actual implementation can change behind the scene.  
Delegating proxy contracts are widely used for both upgradeability and gas savings. These proxies rely on a logic contract (also known as implementation contract or master copy) that is called using `delegatecall`. This allows proxies to keep a persistent state (storage and balance) while the code is delegated to the logic contract.

## Proxy forwarding

The most immediate problem that proxies need to solve is how the proxy exposes the entire interface of the logic contract without requiring a one to one mapping of the entire logic contract’s interface. That would be difficult to maintain, prone to errors, and would make the interface itself not upgradeable. Hence, a dynamic forwarding mechanism is required. The basics of such a mechanism are presented in the code below:

```js
assembly {
  let ptr := mload(0x40)

  // (1) copy incoming call data
  calldatacopy(ptr, 0, calldatasize)

  // (2) forward call to logic contract
  let result := delegatecall(gas, _impl, ptr, calldatasize, 0, 0)
  let size := returndatasize

  // (3) retrieve return data
  returndatacopy(ptr, 0, size)

  // (4) forward return data back to caller
  switch result
  case 0 { revert(ptr, size) }
  default { return(ptr, size) }
}
```
This code can be put in the fallback function of a proxy, and will forward any call to any function with any set of parameters to the logic contract without it needing to know anything in particular of the logic contract’s interface. In essence, (1) the calldata is copied to memory, (2) the call is forwarded to the logic contract, (3) the return data from the call to the logic contract is retrieved, and (4) the returned data is forwarded back to the caller.

A very important thing to note is that the code makes use of the EVM’s delegatecall opcode which executes the callee’s code in the context of the caller’s state. That is, the logic contract controls the proxy’s state and the logic contract’s state is meaningless. Thus, the proxy doesn’t only forward transactions to and from the logic contract, but also represents the pair’s state. The state is in the proxy and the logic is in the particular implementation that the proxy points to.

