// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "@openzeppelin-up/contracts/proxy/utils/Initializable.sol";

contract LogicContractV2 is Initializable {
    uint256 private value;

    //replace constructor, can only be call once
    // need to be call by admin during upgrade with upgradeAndCall
    function initialize(uint256 _value) public initializer {
        value = _value;
    }

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
        return _input * _input;
    }

    //new function whose fct selector clash with a functino from the Proxy
    function admin() external pure returns (address) {
        return address(0);
    }
}
