// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

contract LogicContractV1 {
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
}
