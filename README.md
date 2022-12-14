# Repo

Implementation of the various proxy pattern in solidity

## TODO

- [ ] Write test for UUPS and beacon, diamond
- [ ] add initialisation during upgrade
- [ ] add Diamond docs
- [ ] Diamond: AppStorage, multilpe facet, upgrade data storage, kill upgradeability 
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

## [Transparent](https://blog.openzeppelin.com/the-transparent-proxy-pattern/) vs [UUPS Proxies](https://eips.ethereum.org/EIPS/eip-1822)

There are two alternative ways to add upgradeability to an ERC1967 proxy.

The original proxies included in OpenZeppelin followed the Transparent Proxy Pattern. While this pattern is still provided, our recommendation is now shifting towards UUPS proxies, which are both lightweight and versatile. The name UUPS comes from EIP1822, which first documented the pattern.

While both of these share the same interface for upgrades, in UUPS proxies the upgrade is handled by the implementation, and can eventually be removed. Transparent proxies, on the other hand, include the upgrade and admin logic in the proxy itself. This means TransparentUpgradeableProxy is more expensive to deploy than what is possible with UUPS proxies.

UUPS proxies are implemented using an ERC1967Proxy. Note that this proxy is not by itself upgradeable. It is the role of the implementation to include, alongside the contract’s logic, all the code necessary to update the implementation’s address that is stored at a specific slot in the proxy’s storage space. This is where the UUPSUpgradeable contract comes in. Inheriting from it (and overriding the _authorizeUpgrade function with the relevant access control mechanism) will turn your contract into a UUPS compliant implementation.

Note that since both proxies use the same storage slot for the implementation address, using a UUPS compliant implementation with a TransparentUpgradeableProxy might allow non-admins to perform upgrade operations.

By default, the upgrade functionality included in UUPSUpgradeable contains a security mechanism that will prevent any upgrades to a non UUPS compliant implementation. This prevents upgrades to an implementation contract that wouldn’t contain the necessary upgrade mechanism, as it would lock the upgradeability of the proxy forever. This security mechanism can be bypassed by either of:

Adding a flag mechanism in the implementation that will disable the upgrade function when triggered.

Upgrading to an implementation that features an upgrade mechanism without the additional security check, and then upgrading again to another implementation without the upgrade mechanism.

The current implementation of this security mechanism uses EIP1822 to detect the storage slot used by the implementation. A previous implementation, now deprecated, relied on a rollback check. It is possible to upgrade from a contract using the old mechanism to a new one. The inverse is however not possible, as old implementations (before version 4.5) did not include the ERC1822 interface.


## Transparent Upgradeable Proxy

This contract implements a proxy that is upgradeable by an admin.

To avoid proxy selector clashing, which can potentially be used in an attack, this contract uses the transparent proxy pattern. This pattern implies two things that go hand in hand:

If any account other than the admin calls the proxy, the call will be forwarded to the implementation, even if that call matches one of the admin functions exposed by the proxy itself.

If the admin calls the proxy, it can access the admin functions, but its calls will never be forwarded to the implementation. If the admin tries to call a function on the implementation it will fail with an error that says "admin cannot fallback to proxy target".

These properties mean that the admin account can only be used for admin actions like upgrading the proxy or changing the admin, so it’s best if it’s a dedicated account that is not used for anything else. This will avoid headaches due to sudden errors when trying to call a function from the proxy implementation.

Our recommendation is for the dedicated account to be an instance of the ProxyAdmin contract. If set up this way, you should think of the ProxyAdmin instance as the real administrative interface of your proxy.

|Msg.sender       |owner()                |upgradeto()                |transfer()               |
|-----------------|-----------------------|---------------------------|-------------------------|
|Owner            |returns proxy.owner()  |returns proxy.upgradeTo()  |fails                    |
|Other            |returns erc20.owner()  |fails                      |returns erc20.transfer() |


## Universal Upgradeable Proxy Standard (UUPS)

delegatecall() - Function in contract A which allows an external contract B (delegating) to modify A’s storage (see diagram below, Solidity docs)
Proxy Contract - The contract A which stores data, but uses the logic of external contract B by way of delegatecall().
Logic Contract - The contract B which contains the logic used by Proxy Contract A
Proxiable Contract - Inherited in Logic Contract B to provide the upgrade functionality

In UUPS proxies the upgrade is handled by the implementation, and can eventually be removed.  
UUPS proxies are implemented using an ERC1967Proxy 91. Note that this proxy is not by itself upgradeable. It is the role of the implementation to include, alongside the contract's logic, all the code necessary to update the implementation's address that is stored at a specific slot in the proxy's storage space. This is where the UUPSUpgradeable 102 contract comes in. Inheriting from it (and overriding the _authorizeUpgrade 26 function with the relevant access control mechanism) will turn your contract into a UUPS compliant implementation.


## Initializable

In Solidity, code that is inside a constructor or part of a global variable declaration is not part of a deployed contract’s runtime bytecode. This code is executed only once, when the contract instance is deployed. As a consequence of this, the code within a logic contract’s constructor will never be executed in the context of the proxy’s state. To rephrase, proxies are completely oblivious to the existence of constructors. It’s simply as if they weren’t there for the proxy.

The problem is easily solved though. Logic contracts should move the code within the constructor to a regular 'initializer' function, and have this function be called whenever the proxy links to this logic contract. Special care needs to be taken with this initializer function so that it can only be called once, which is one of the properties of constructors in general programming.

This is why when we create a proxy using OpenZeppelin Upgrades, you can provide the name of the initializer function and pass parameters.

To ensure that the `initialize` function can only be called once, a simple modifier is used. OpenZeppelin Upgrades provides this functionality via a contract that can be extended:

```js
// SPDX-License-Identifier: MIT
pragma solidity ^0.6.0;

import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";

contract MyContract is Initializable {
    function initialize(
        address arg1,
        uint256 arg2,
        bytes memory arg3
    ) public payable initializer {
        // "constructor" code...
    }
}
```
The contract extends `Initializable` and implements the `initializer` modifier provided by it.

Another difference between a constructor and a regular function is that Solidity takes care of automatically invoking the constructors of all ancestors of a contract. When writing an initializer, you need to take special care to manually call the initializers of all parent contracts.


Solidity allows defining initial values for fields when declaring them in a contract.  
This is equivalent to setting these values in the constructor, and as such, will not work for upgradeable contracts.


## Beacon Proxy

A different family of proxies are beacon proxies. This pattern, popularized by Dharma, allows multiple proxies to be upgraded to a different implementation in a single transaction.

BeaconProxy: A proxy that retrieves its implementation from a beacon contract.

UpgradeableBeacon: A beacon contract with a built in admin that can upgrade the BeaconProxy pointing to it.

In this pattern, the proxy contract doesn’t hold the implementation address in storage like an ERC1967 proxy, instead the address is stored in a separate beacon contract. The upgrade operations that are sent to the beacon instead of to the proxy contract, and all proxies that follow that beacon are automatically upgraded.

## Diamond

This proposal standardizes diamonds, which are modular smart contract systems that can be upgraded/extended after deployment, and have virtually no size limit. More technically, a diamond is a contract with external functions that are supplied by contracts called facets. Facets are separate, independent contracts that can share internal functions, libraries, and state variables.  
There are a number of different reasons to use diamonds. Here are some of them:

A single address for unlimited contract functionality. Using a single address for contract functionality makes deployment, testing and integration with other smart contracts, software and user interfaces easier.
Your contract exceeds the 24KB maximum contract size. You may have related functionality that it makes sense to keep in a single contract, or at a single contract address. A diamond does not have a max contract size.
A diamond provides a way to organize contract code and data. You may want to build a contract system with a lot of functionality. A diamond provides a systematic way to isolate different functionality and connect them together and share data between them as needed in a gas-efficient way.
A diamond provides a way to upgrade functionality. Upgradeable diamonds can be upgraded to add/replace/remove functionality. Because diamonds have no max contract size, there is no limit to the amount of functionality that can be added to diamonds over time. Diamonds can be upgraded without having to redeploy existing functionality. Parts of a diamond can be added/replaced/removed while leaving other parts alone.
A diamond can be immutable. It is possible to deploy an immutable diamond or make an upgradeable diamond immutable at a later time.
A diamond can reuse deployed contracts. Instead of deploying contracts to a blockchain, existing already deployed, onchain contracts can be used to create diamonds. Custom diamonds can be created from existing deployed contracts. This enables the creation of on-chain smart contract platforms and libraries.


## Potentially Unsafe Operations
When working with upgradeable smart contracts, you will always interact with the contract instance, and never with the underlying logic contract. However, nothing prevents a malicious actor from sending transactions to the logic contract directly. This does not pose a threat, since any changes to the state of the logic contracts do not affect your contract instances, as the storage of the logic contracts is never used in your project.

There is, however, an exception. If the direct call to the logic contract triggers a selfdestruct operation, then the logic contract will be destroyed, and all your contract instances will end up delegating all calls to an address without any code. This would effectively break all contract instances in your project.

A similar effect can be achieved if the logic contract contains a delegatecall operation. If the contract can be made to delegatecall into a malicious contract that contains a selfdestruct, then the calling contract will be destroyed.

As such, it is not allowed to use either selfdestruct or delegatecall in your contracts.


## Sources
[Openzepellin docs](https://docs.openzeppelin.com/upgrades-plugins/1.x/proxies)  
[Openzepellin docs](https://docs.openzeppelin.com/contracts/4.x/api/proxy)  
[Openzepellin blog](https://blog.openzeppelin.com/the-transparent-proxy-pattern/)  
[Openzepellin docs](https://docs.openzeppelin.com/upgrades-plugins/1.x/writing-upgradeable)  
[EIP2535](https://eips.ethereum.org/EIPS/eip-2535)