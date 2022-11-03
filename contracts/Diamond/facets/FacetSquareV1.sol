// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

contract FacetSquareV1 {
    bytes32 constant DIAMOND_STORAGE_POSITION =
        keccak256("diamond.standard.square.storage");

    struct SquareState {
        uint256 value;
    }

    constructor() {}

    function diamondStorage() internal pure returns (SquareState storage ds) {
        bytes32 position = DIAMOND_STORAGE_POSITION;
        assembly {
            ds.slot := position
        }
    }

    // Stores a new value in the contract
    function store(uint256 _newValue) public {
        SquareState storage squareState = diamondStorage();
        squareState.value = _newValue;
    }

    // Reads the last stored value
    function retrieve() public view returns (uint256) {
        SquareState storage squareState = diamondStorage();
        return squareState.value;
    }

    // returns the square of the _input
    function square(uint256 _input) public pure returns (uint256) {
        return _input; // implementation error
    }
}
