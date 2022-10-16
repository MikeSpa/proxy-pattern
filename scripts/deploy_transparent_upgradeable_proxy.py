from brownie import (
    LogicContractV1,
    LogicContractV2,
    TransparentUpgradeableProxy,
    ProxyAdmin,
)
from scripts.helpful_scripts import get_account, encode_function_data


def deploy_proxy_admin():
    account = get_account()
    proxy_admin = ProxyAdmin.deploy(
        {"from": account},
    )
    return proxy_admin


def deploy_logic_contractV1():
    account = get_account()
    logic_contract = LogicContractV1.deploy(
        99,
        {"from": account},
    )
    return logic_contract


def deploy_logic_contractV2():
    account = get_account()
    logic_contract = LogicContractV2.deploy(
        {"from": account},
    )
    return logic_contract


def deploy_proxy(logic_contract, proxy_admin):
    account = get_account()
    logic_contract_encoded_initializer_function = encode_function_data()
    proxy = TransparentUpgradeableProxy.deploy(
        logic_contract.address,
        proxy_admin.address,
        logic_contract_encoded_initializer_function,
        {"from": account, "gas_limit": 1_000_000},
    )
    return proxy


def upgrade(proxy, new_implementation, proxy_admin):
    account = get_account()
    proxy_admin.upgrade(proxy.address, new_implementation.address, {"from": account})


def upgrade_and_call(proxy, new_implementation, proxy_admin, initialize_data):
    account = get_account()
    proxy_admin.upgradeAndCall(
        proxy.address, new_implementation.address, initialize_data, {"from": account}
    )


def deploy_proxy_V1():
    admin = deploy_proxy_admin()
    v1 = deploy_logic_contractV1()
    proxy = deploy_proxy(v1, admin)
    return admin, v1, proxy


def deploy_and_upgrade_to_V2():
    admin = deploy_proxy_admin()
    v1 = deploy_logic_contractV1()
    proxy = deploy_proxy(v1, admin)
    v2 = deploy_logic_contractV2()
    upgrade(proxy, v2, admin)
    return admin, v1, v2, proxy


def main():
    pass
