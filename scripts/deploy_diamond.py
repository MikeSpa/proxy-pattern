from brownie import (
    FacetSquareV1,
    FacetSquareV2,
    DiamondCutFacet,
    Diamond,
    Contract,
    ZERO_ADDRESS,
)
from scripts.helpful_scripts import get_account
from web3 import Web3


def deploy_facet(contract):
    account = get_account()
    facet = contract.deploy(
        {"from": account},
    )
    return facet


def deploy_proxy(_args, _diamondCut):
    account = get_account()
    # Deploying the proxy
    # Diamond arg
    proxy = Diamond.deploy(
        _diamondCut,
        _args,
        {"from": account, "gas_limit": 10_000_000},
    )
    print(f"Proxy deployed to {proxy} !")
    return proxy


def diamondCut(proxy, _diamondCut):
    account = get_account()
    proxy_diamond_cut_facet = Contract.from_abi(
        "DiamondCutFacet", proxy.address, DiamondCutFacet.abi
    )
    proxy_diamond_cut_facet.diamondCut(
        _diamondCut,
        ZERO_ADDRESS,
        "",
        {"from": account, "gas_limit": 10_000_000},
    )
    return proxy_diamond_cut_facet


def main():
    account = get_account()
    square_facet = deploy_facet(FacetSquareV1)
    cutDiamond_facet = deploy_facet(DiamondCutFacet)

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

    square_facet_2 = deploy_facet(FacetSquareV2)

    func_selector_square = Web3.keccak(text="square(uint256)")[:4].hex()
    _diamondCut = [
        [square_facet_2.address, 1, [func_selector_square]],
    ]

    diamondCut(diamond, _diamondCut)
