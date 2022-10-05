from brownie import (
    LogicContractV1,
    LogicContractV2,
    TransparentUpgradeableProxy,
    ProxyAdmin,
    config,
    network,
    Contract,
)
from scripts.helpful_scripts import get_account, encode_function_data


def deploy():
    account = get_account()
    print(f"Deploying to {network.show_active()}")
    # deploy the logic contract
    logic_contract = LogicContractV1.deploy(
        {"from": account},
    )
    # deploy the ProxyAdmin and use that as the admin contract
    proxy_admin = ProxyAdmin.deploy(
        {"from": account},
    )

    # interaction with the logic contract directly
    logic_contract.store(42, {"from": account})
    ret = logic_contract.retrieve()
    print(f"Here is the initial value in the LogicContractV1: {ret}")
    print(f"Here is its square : {logic_contract.square(ret)}")

    # Dploying the proxy
    logic_contract_encoded_initializer_function = encode_function_data()
    proxy = TransparentUpgradeableProxy.deploy(
        logic_contract.address,
        proxy_admin.address,
        logic_contract_encoded_initializer_function,
        {"from": account, "gas_limit": 1_000_000},
    )
    print(f"Proxy deployed to {proxy} !")

    # now we want to call these function on the proxy
    # we assign the abi of logic_contract contract to proxy
    proxy = Contract.from_abi("LogicContractV1", proxy.address, LogicContractV1.abi)
    print(f"Here is the initial value in the LogicContractV1: {proxy.retrieve()}")
    store_tx = proxy.store(8, {"from": account})
    store_tx.wait(1)
    proxy_ret = proxy.retrieve()
    print(f"The value in the LogicContractV1 is now: {proxy_ret}")
    print(f"Here is its square : {proxy.square(proxy_ret)}")
    print(
        f"The value on the logic contract storage has not changed: {logic_contract.retrieve()}"
    )

    # We upgrade to the new implementation to fix the square() function
    print("################################################################")
    print("We upgrade to the new implementation to fix the square() function")
    print("################################################################")

    # deploy new implementation
    logic_contract_v2 = LogicContractV2.deploy(
        {"from": account},
    )
    # upgrade to the new implementation
    proxy_admin.upgrade(proxy.address, logic_contract_v2.address, {"from": account})
    # proxy = Contract.from_abi("LogicContractV2", proxy.address, LogicContractV2.abi)
    print(
        f"The value in the LogicContractV2 is still: {proxy_ret}, since it was saved in the proxy storage"
    )
    print(f"Here is its square : {proxy.square(proxy_ret)}")


def main():
    deploy()
