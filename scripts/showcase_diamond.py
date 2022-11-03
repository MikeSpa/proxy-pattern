from brownie import (
    FacetSquareV1,
    FacetSquareV2,
    DiamondCutFacet,
    Diamond,
    config,
    network,
    Contract,
    ZERO_ADDRESS,
)
from scripts.helpful_scripts import get_account
from web3 import Web3


def deploy():
    account = get_account()
    print(f"Deploying to {network.show_active()}")

    ## DEPLOYING THE FACETS
    # deploy the logic contract
    facet_square_v1 = FacetSquareV1.deploy(
        {"from": account},
    )
    # Deploy diamond cut facet
    diamond_cut_facet = DiamondCutFacet.deploy(
        {"from": account},
    )

    # interaction with the logic contract directly
    ret = facet_square_v1.retrieve()
    print(f"Here is the initial value in the FacetSquareV1: {ret}")
    print(f"Here is its square : {facet_square_v1.square(ret)}")

    # Dploying the proxy
    # Diamond arg
    _args = [account.address, ZERO_ADDRESS, ""]

    func_selector_retrieve = Web3.keccak(text="retrieve()")[:4].hex()
    func_selector_store = Web3.keccak(text="store(uint256)")[:4].hex()
    func_selector_square = Web3.keccak(text="square(uint256)")[:4].hex()
    func_selector_diamondCut = Web3.keccak(
        text="diamondCut((address,uint8,bytes4[])[],address,bytes)"
    )[:4].hex()
    print(func_selector_diamondCut)
    _diamondCut = [
        [facet_square_v1.address, 0, [func_selector_retrieve]],
        [facet_square_v1.address, 0, [func_selector_store]],
        [facet_square_v1.address, 0, [func_selector_square]],
        [diamond_cut_facet.address, 0, [func_selector_diamondCut]],
    ]

    proxy = Diamond.deploy(
        _diamondCut,
        _args,
        {"from": account, "gas_limit": 10_000_000},
    )
    print(f"Proxy deployed to {proxy} !")

    # now we want to call these function on the proxy
    # we assign the abi of logic_contract contract to proxy
    proxy = Contract.from_abi("FacetSquareV1", proxy.address, FacetSquareV1.abi)
    print("Despite what we give to the constructor,")
    print(
        f"Here is the initial value in the proxy contract storage: {proxy.retrieve()}"
    )
    store_tx = proxy.store(8, {"from": account})
    store_tx.wait(1)
    proxy_ret = proxy.retrieve()
    print(f"The value in the proxy is now: {proxy_ret}")
    print(f"Here is its square : {proxy.square(proxy_ret)}")
    print(
        f"The value on the logic contract storage has not changed: {facet_square_v1.retrieve()}"
    )

    # We upgrade to the new implementation to fix the square() function
    print("################################################################")
    print("We upgrade to the new implementation to fix the square() function")
    print("################################################################")

    # deploy new implementation
    facet_square_v2 = FacetSquareV2.deploy(
        {"from": account},
    )
    print(f"Its square is still: {proxy.square(proxy_ret)}")

    # upgrade to the new implementation
    print("Adding new method...")
    proxy_diamond_cut_facet = Contract.from_abi(
        "DiamondCutFacet", proxy.address, DiamondCutFacet.abi
    )

    func_selector_square = Web3.keccak(text="square(uint256)")[:4].hex()
    _diamondCut = [
        [facet_square_v2.address, 1, [func_selector_square]],
    ]
    proxy_diamond_cut_facet.diamondCut(
        _diamondCut,
        ZERO_ADDRESS,
        "",
        {"from": account, "gas_limit": 1_000_000},
    )
    print(
        f"The value in the proxy is still: {proxy.retrieve()}, since it was saved in the proxy storage"
    )
    print(f"Here is its correct square : {proxy.square(proxy.retrieve())}")


def main():
    deploy()
