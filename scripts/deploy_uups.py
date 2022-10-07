from brownie import (
    LogicContractUUPSV1,
    LogicContractUUPSV2,
    ERC1967Proxy,
    network,
    Contract,
)
from scripts.helpful_scripts import get_account, encode_function_data


def deploy():
    account = get_account()
    print(f"Deploying to {network.show_active()}")
    # deploy the logic contract
    logic_contract = LogicContractUUPSV1.deploy(
        {"from": account},
    )

    # interaction with the logic contract directly
    logic_contract.store(42, {"from": account})
    ret = logic_contract.retrieve()
    print(f"Here is the initial value in the LogicContractUUPSV1: {ret}")
    print(f"Here is its square : {logic_contract.square(ret)}")

    # Deploying the proxy
    logic_contract_encoded_initializer_function = encode_function_data()
    proxy = ERC1967Proxy.deploy(
        logic_contract.address,
        logic_contract_encoded_initializer_function,
        {"from": account, "gas_limit": 1_000_000},
    )
    print(f"Proxy deployed to {proxy} !")

    # # now we want to call these function on the proxy
    # # we assign the abi of logic_contract contract to proxy
    proxy = Contract.from_abi(
        "LogicContractUUPSV1", proxy.address, LogicContractUUPSV1.abi
    )
    # initialize the proxy e.g. set owner
    proxy.initialize(3, {"from": account})
    print(f"Proxy owner: {proxy.owner()}")

    # We upgrade to the new implementation to fix the square() function
    print("################################################################")
    print("We upgrade to the new implementation to fix the square() function")
    print("################################################################")

    # deploy new implementation
    logic_contract_v2 = LogicContractUUPSV2.deploy(
        {"from": account},
    )
    # upgrade to the new implementation

    proxy.upgradeTo(logic_contract_v2, {"from": account})
    proxy = Contract.from_abi(
        "LogicContractUUPSV2", proxy.address, LogicContractUUPSV2.abi
    )
    print(f"Here is its square : {proxy.square(3)}")


def main():
    deploy()
