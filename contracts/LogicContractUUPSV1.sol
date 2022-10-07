// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin-up/contracts/proxy/utils/Initializable.sol";
import "./UUPSUpgradeable.sol";

import "./OwnableUpgradeable.sol";

contract LogicContractUUPSV1 is
    Initializable,
    UUPSUpgradeable,
    OwnableUpgradeable
{
    uint256 private value;

    // Stores a new value in the contract
    function store(uint256 _newValue) public {
        value = _newValue;
    }

    // Reads the last stored value
    function retrieve() public view returns (uint256) {
        return value;
    }

    // returns the square of the _input
    function square(uint256 _input) public pure returns (uint256) {
        return _input; // implementation error
    }

    //###########################  UUPS  ###################################3

    //initializer instead of a constructor
    function initialize(uint256 _value) public initializer {
        value = _value;

        // OwnableUpgradeable: owner = msg.sender;
        __Ownable_init();
    }

    //need to override this fct
    //only the owner can upgrade this implementation
    function _authorizeUpgrade(address) internal override onlyOwner {}
}
