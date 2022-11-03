import pytest
from brownie import (
    FacetSquareV1,
    FacetSquareV2,
    Diamond,
    DiamondLoupeFacet,
    Contract,
    reverts,
    ZERO_ADDRESS,
)
from scripts.helpful_scripts import get_account
from scripts.deploy_diamond import *

# test that the proxy delegate the call to the implementation
def test_proxy_delegates_calls():
    # Deploy
    account = get_account()
    square_facet = deploy_facet(FacetSquareV1)

    ## Proxy
    func_selector_retrieve = Web3.keccak(text="retrieve()")[:4].hex()
    func_selector_store = Web3.keccak(text="store(uint256)")[:4].hex()
    _diamondCut = [
        [square_facet.address, 0, [func_selector_retrieve]],
        [square_facet.address, 0, [func_selector_store]],
    ]
    _arg = [account, ZERO_ADDRESS, ""]
    diamond = deploy_proxy(_arg, _diamondCut)

    proxy = Contract.from_abi("FacetSquareV1", diamond.address, FacetSquareV1.abi)

    proxy.store(42, {"from": account})
    assert proxy.retrieve() == 42


def test_add_function_via_CutDiamond():
    # Deploy
    account = get_account()
    square_facet = deploy_facet(FacetSquareV1)
    cutDiamond_facet = deploy_facet(DiamondCutFacet)

    ## Proxy
    func_selector_retrieve = Web3.keccak(text="retrieve()")[:4].hex()
    func_selector_store = Web3.keccak(text="store(uint256)")[:4].hex()
    func_selector_diamondCut = Web3.keccak(
        text="diamondCut((address,uint8,bytes4[])[],address,bytes)"
    )[:4].hex()
    _diamondCut = [
        [square_facet.address, 0, [func_selector_retrieve]],
        [square_facet.address, 0, [func_selector_store]],
        [cutDiamond_facet.address, 0, [func_selector_diamondCut]],
    ]
    _arg = [account, ZERO_ADDRESS, ""]
    diamond = deploy_proxy(_arg, _diamondCut)

    proxy = Contract.from_abi("FacetSquareV1", diamond.address, FacetSquareV1.abi)

    with reverts():
        proxy.square(33, {"from": account})

    # add function
    func_selector_square = Web3.keccak(text="square(uint256)")[:4].hex()
    _diamondCut = [
        [square_facet.address, 0, [func_selector_square]],
    ]

    tx = diamondCut(diamond, _diamondCut)

    assert proxy.square(33, {"from": account}) == 33

    assert tx.events["DiamondCut"]["_diamondCut"][0] == [
        square_facet.address,
        0,
        [func_selector_square],
    ]


def test_update_function_via_CutDiamond():
    # Deploy
    account = get_account()
    square_facet = deploy_facet(FacetSquareV1)
    square_facet_2 = deploy_facet(FacetSquareV2)
    cutDiamond_facet = deploy_facet(DiamondCutFacet)

    ## Proxy
    func_selector_retrieve = Web3.keccak(text="retrieve()")[:4].hex()
    func_selector_store = Web3.keccak(text="store(uint256)")[:4].hex()
    func_selector_square = Web3.keccak(text="square(uint256)")[:4].hex()
    func_selector_diamondCut = Web3.keccak(
        text="diamondCut((address,uint8,bytes4[])[],address,bytes)"
    )[:4].hex()
    _diamondCut = [
        [square_facet.address, 0, [func_selector_retrieve]],
        [square_facet.address, 0, [func_selector_store]],
        [square_facet.address, 0, [func_selector_square]],
        [cutDiamond_facet.address, 0, [func_selector_diamondCut]],
    ]
    _arg = [account, ZERO_ADDRESS, ""]
    diamond = deploy_proxy(_arg, _diamondCut)

    proxy = Contract.from_abi("FacetSquareV1", diamond.address, FacetSquareV1.abi)

    assert proxy.square(33, {"from": account}) == 33

    # update function
    func_selector_square = Web3.keccak(text="square(uint256)")[:4].hex()
    _diamondCut = [
        [square_facet_2.address, 1, [func_selector_square]],
    ]

    tx = diamondCut(diamond, _diamondCut)

    assert proxy.square(33, {"from": account}) == 33 ** 2

    assert tx.events["DiamondCut"]["_diamondCut"][0] == [
        square_facet_2.address,
        1,
        [func_selector_square],
    ]


def test_remove_function_via_CutDiamond():
    # Deploy
    account = get_account()
    square_facet = deploy_facet(FacetSquareV1)
    cutDiamond_facet = deploy_facet(DiamondCutFacet)

    ## Proxy
    func_selector_retrieve = Web3.keccak(text="retrieve()")[:4].hex()
    func_selector_store = Web3.keccak(text="store(uint256)")[:4].hex()
    func_selector_square = Web3.keccak(text="square(uint256)")[:4].hex()
    func_selector_diamondCut = Web3.keccak(
        text="diamondCut((address,uint8,bytes4[])[],address,bytes)"
    )[:4].hex()
    _diamondCut = [
        [square_facet.address, 0, [func_selector_retrieve]],
        [square_facet.address, 0, [func_selector_store]],
        [square_facet.address, 0, [func_selector_square]],
        [cutDiamond_facet.address, 0, [func_selector_diamondCut]],
    ]
    _arg = [account, ZERO_ADDRESS, ""]
    diamond = deploy_proxy(_arg, _diamondCut)

    proxy = Contract.from_abi("FacetSquareV1", diamond.address, FacetSquareV1.abi)

    assert proxy.square(33, {"from": account}) == 33

    # remove function
    func_selector_square = Web3.keccak(text="square(uint256)")[:4].hex()
    _diamondCut = [
        [ZERO_ADDRESS, 2, [func_selector_square]],
    ]

    tx = diamondCut(diamond, _diamondCut)

    with reverts():
        proxy.square(33, {"from": account})

    assert tx.events["DiamondCut"]["_diamondCut"][0] == [
        ZERO_ADDRESS,
        2,
        [func_selector_square],
    ]


def test_DiamondLoupeFaucet():
    # Deploy
    account = get_account()
    square_facet = deploy_facet(FacetSquareV1)
    cutDiamond_facet = deploy_facet(DiamondCutFacet)
    loupe_facet = deploy_facet(DiamondLoupeFacet)

    ## Proxy
    func_selector_retrieve = Web3.keccak(text="retrieve()")[:4].hex()
    func_selector_store = Web3.keccak(text="store(uint256)")[:4].hex()
    func_selector_square = Web3.keccak(text="square(uint256)")[:4].hex()
    func_selector_diamondCut = Web3.keccak(
        text="diamondCut((address,uint8,bytes4[])[],address,bytes)"
    )[:4].hex()

    func_selector_facets = Web3.keccak(text="facets()")[:4].hex()
    func_selector_facetFunctionSelectors = Web3.keccak(
        text="facetFunctionSelectors(address)"
    )[:4].hex()
    func_selector_facetAddresses = Web3.keccak(text="facetAddresses()")[:4].hex()
    func_selector_facetAddress = Web3.keccak(text="facetAddress(bytes4)")[:4].hex()
    _diamondCut = [
        [square_facet.address, 0, [func_selector_retrieve]],
        [square_facet.address, 0, [func_selector_store]],
        [square_facet.address, 0, [func_selector_square]],
        [cutDiamond_facet.address, 0, [func_selector_diamondCut]],
        [loupe_facet.address, 0, [func_selector_facets]],
        [loupe_facet.address, 0, [func_selector_facetFunctionSelectors]],
        [loupe_facet.address, 0, [func_selector_facetAddresses]],
        [loupe_facet.address, 0, [func_selector_facetAddress]],
    ]
    _arg = [account, ZERO_ADDRESS, ""]
    diamond = deploy_proxy(_arg, _diamondCut)

    proxy = Contract.from_abi(
        "DiamondLoupeFacet", diamond.address, DiamondLoupeFacet.abi
    )

    assert proxy.facets()[0] == [
        square_facet.address,
        [
            func_selector_retrieve,
            func_selector_store,
            func_selector_square,
        ],
    ]
    assert proxy.facets()[1] == [
        cutDiamond_facet.address,
        [func_selector_diamondCut],
    ]
    assert proxy.facets()[2] == [
        loupe_facet.address,
        [
            func_selector_facets,
            func_selector_facetFunctionSelectors,
            func_selector_facetAddresses,
            func_selector_facetAddress,
        ],
    ]
    assert proxy.facetFunctionSelectors(square_facet.address) == [
        func_selector_retrieve,
        func_selector_store,
        func_selector_square,
    ]

    assert proxy.facetAddresses() == [square_facet, cutDiamond_facet, loupe_facet]

    assert proxy.facetAddress(func_selector_square) == square_facet.address
    assert (
        proxy.facetAddress(Web3.keccak(text="missing_function(uint128)")[:4].hex())
        == ZERO_ADDRESS
    )

    # remove square function
    func_selector_square = Web3.keccak(text="square(uint256)")[:4].hex()
    _diamondCut = [
        [ZERO_ADDRESS, 2, [func_selector_square]],
    ]

    tx = diamondCut(diamond, _diamondCut)

    assert proxy.facetFunctionSelectors(square_facet.address) == [
        func_selector_retrieve,
        func_selector_store,
        # func_selector_square, # no longer exist
    ]


## test diamondCut( hash collision)
