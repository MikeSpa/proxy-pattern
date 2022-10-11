from brownie import (
    LogicContractBeaconV1,
    LogicContractBeaconV2,
    BeaconProxy,
    UpgradeableBeacon,
    network,
    Contract,
)
from scripts.helpful_scripts import get_account, encode_function_data


def deploy():
    account = get_account()
    print(f"Deploying to {network.show_active()}")

    # 1) Deploy the logic contract
    logic_contract = LogicContractBeaconV1.deploy(
        {"from": account},
    )
    print(f"V1 address : {logic_contract}")

    # interaction with the logic contract directly
    logic_contract.store(42, {"from": account})
    ret = logic_contract.retrieve()
    print(f"Here is the initial value in the LogicContractBeaconV1: {ret}")
    print(f"Here is its square : {logic_contract.square(ret)}")

    # 2) Deploying the Beacon
    beacon = UpgradeableBeacon.deploy(
        logic_contract.address,
        {"from": account, "gas_limit": 1_000_000},
    )
    print(f"Beacon deployed to {beacon} !")

    # 3) Deploying the proxies
    logic_contract_encoded_initializer_function = encode_function_data()
    proxy = BeaconProxy.deploy(
        beacon.address,
        logic_contract_encoded_initializer_function,
        {"from": account, "gas_limit": 1_000_000},
    )
    print(f"Proxy deployed to {proxy} !")

    proxy2 = BeaconProxy.deploy(
        beacon.address,
        logic_contract_encoded_initializer_function,
        {"from": account, "gas_limit": 1_000_000},
    )
    print(f"Proxy deployed to {proxy2} !")

    # now we want to call these function on the proxy
    # we assign the abi of logic_contract contract to proxy
    proxy = Contract.from_abi(
        "LogicContractBeaconV1", proxy.address, LogicContractBeaconV1.abi
    )
    proxy2 = Contract.from_abi(
        "LogicContractBeaconV1", proxy.address, LogicContractBeaconV1.abi
    )
    print(f"Here is the initial value in the LogicContractBeaconV1: {proxy.retrieve()}")
    store_tx = proxy.store(8, {"from": account})
    store_tx.wait(1)
    proxy_ret = proxy.retrieve()
    print(f"The value in the LogicContractBeaconV1 is now: {proxy_ret}")
    print(f"Here is its square : {proxy.square(proxy_ret)}")
    print(
        f"The value on the logic contract storage has not changed: {logic_contract.retrieve()}"
    )

    # We upgrade to the new implementation to fix the square() function
    print("################################################################")
    print("We upgrade to the new implementation to fix the square() function")
    print("################################################################")

    # deploy new implementation
    logic_contract_v2 = LogicContractBeaconV2.deploy(
        {"from": account},
    )
    print(f"V2 address : {logic_contract_v2}")
    # upgrade to the new implementation
    print(
        f"We now change the implementation in the beacon from V1: {beacon.implementation()}"
    )
    beacon.upgradeTo(logic_contract_v2.address, {"from": account})
    print(f"To V2 : {beacon.implementation()}")

    print(
        f"The value in the LogicContractBeaconV2 is still: {proxy_ret}, since it was saved in the proxy storage"
    )
    print(f"Here is its square: {proxy.square(proxy_ret)}")
    print(
        f"It also upgrade the impl. of the second proxy: {proxy2.square(proxy_ret)}, since the beacon link to the new implementation and all proxies link to the beacon"
    )


def main():
    deploy()
