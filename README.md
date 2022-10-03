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


## Storage Collision

In order to avoid clashes with the storage variables of the implementation contract behind a proxy, we use [EIP 1967](https://eips.ethereum.org/EIPS/eip-1967) storage slots.  
ERC1967Upgrade: Internal functions to get and set the storage slots defined in EIP1967.  
ERC1967Proxy: A proxy using EIP1967 storage slots. Not upgradeable by default.  

A problem that quickly comes up when using proxies has to do with the way in which variables are stored in the proxy contract. Suppose that the proxy stores the logic contract’s address in its only variable address public _implementation;. Now, suppose that the logic contract is a basic token whose first variable is address public _owner. Both variables are 32 byte in size, and as far as the EVM knows, occupy the first slot of the resulting execution flow of a proxied call. When the logic contract writes to _owner, it does so in the scope of the proxy’s state, and in reality writes to _implementation. This problem can be referred to as a "storage collision".

|Proxy                     |Implementation           |
|--------------------------|-------------------------|
|address _implementation   |address _owner           | <=== Storage collision!
|...                       |mapping _balances        |
|                          |uint256 _supply          |
|                          |...                      |

Instead of storing the _implementation address at the proxy’s first storage slot, it chooses a pseudo random slot instead. This slot is sufficiently random, that the probability of a logic contract declaring a variable at the same slot is negligible.

|Proxy                     |Implementation           |
|--------------------------|-------------------------|
|...                       |address _owner           |
|...                       |mapping _balances        |
|...                       |uint256 _supply          |
|...                       |...                      |
|...                       |                         |
|...                       |                         |
|...                       |                         |
|...                       |                         |
|address _implementation   |                         | <=== Randomized slot.
|...                       |                         |
|...                       |                         |
An example of how the randomized storage is achieved, following [EIP 1967](https://eips.ethereum.org/EIPS/eip-1967):
```
bytes32 private constant implementationPosition = bytes32(uint256(
  keccak256('eip1967.proxy.implementation')) - 1
));
```
As a result, a logic contract doesn’t need to care about overwriting any of the proxy’s variables. Other proxy implementations that face this problem usually imply having the proxy know about the logic contract’s storage structure and adapt to it, or instead having the logic contract know about the proxy’s storage structure and adapt to it. This is why this approach is called "unstructured storage"; neither of the contracts needs to care about the structure of the other.

## Storage Collisions Between Implementation Versions
As discussed, the unstructured approach avoids storage collisions between the logic contract and the proxy. However, storage collisions between different versions of the logic contract can occur. In this case, imagine that the first implementation of the logic contract stores address public _owner at the first storage slot and an upgraded logic contract stores address public _lastContributor at the same first slot. When the updated logic contract attempts to write to the _lastContributor variable, it will be using the same storage position where the previous value for _owner was being stored, and overwrite it!

Incorrect storage preservation:

|Implementation_v0   |Implementation_v1        |
|--------------------|-------------------------|
|address _owner      |address _lastContributor | <=== Storage collision!
|mapping _balances   |address _owner           |
|uint256 _supply     |mapping _balances        |
|...                 |uint256 _supply          |
|                    |...                      |
Correct storage preservation:

|Implementation_v0   |Implementation_v1        |
|--------------------|-------------------------|
|address _owner      |address _owner           |
|mapping _balances   |mapping _balances        |
|uint256 _supply     |uint256 _supply          |
|...                 |address _lastContributor | <=== Storage extension.
|                    |...                      |
The unstructured storage proxy mechanism doesn’t safeguard against this situation. It is up to the user to have new versions of a logic contract extend previous versions, or otherwise guarantee that the storage hierarchy is always appended to but not modified. However, OpenZeppelin Upgrades detects such collisions and warns the developer appropriately.

## Source
[Openzepellin docs](https://docs.openzeppelin.com/upgrades-plugins/1.x/proxies)
[Openzepellin docs](https://docs.openzeppelin.com/contracts/4.x/api/proxy)