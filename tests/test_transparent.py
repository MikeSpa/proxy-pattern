import pytest
from brownie import (
    LogicContractV1,
    LogicContractV2,
    TransparentUpgradeableProxy,
    ProxyAdmin,
    Contract,
    reverts,
)
from scripts.helpful_scripts import get_account, encode_function_data


def test_proxy_delegates_calls():
    account = get_account()
    logic_contract = LogicContractV1.deploy(
        {"from": account},
    )
    proxy_admin = ProxyAdmin.deploy(
        {"from": account},
    )
    logic_contract_encoded_initializer_function = encode_function_data()
    proxy = TransparentUpgradeableProxy.deploy(
        logic_contract.address,
        proxy_admin.address,
        logic_contract_encoded_initializer_function,
        {"from": account, "gas_limit": 1_000_000},
    )
    proxy_logic_contract = Contract.from_abi(
        "LogicContractV1", proxy.address, LogicContractV1.abi
    )
    assert proxy_logic_contract.retrieve() == 0
    proxy_logic_contract.store(1, {"from": account})
    assert proxy_logic_contract.retrieve() == 1
    assert proxy_logic_contract.square(2, {"from": account}) != 4


def test_proxy_upgrades():
    account = get_account()
    logic_contract = LogicContractV1.deploy(
        {"from": account},
    )
    proxy_admin = ProxyAdmin.deploy(
        {"from": account},
    )
    logic_contract_encoded_initializer_function = encode_function_data()
    proxy = TransparentUpgradeableProxy.deploy(
        logic_contract.address,
        proxy_admin.address,
        logic_contract_encoded_initializer_function,
        {"from": account, "gas_limit": 1_000_000},
    )
    logic_contract_v2 = LogicContractV2.deploy(
        {"from": account},
    )
    proxy_logic_contract = Contract.from_abi(
        "LogicContractV2", proxy.address, LogicContractV2.abi
    )
    proxy_admin.upgrade(proxy.address, logic_contract_v2.address, {"from": account})
    assert proxy_logic_contract.retrieve() == 0
    assert proxy_logic_contract.square(2, {"from": account}) == 4


def test_proxy_selector_clashing():
    account = get_account()
    user = get_account(2)
    logic_contract = LogicContractV1.deploy(
        {"from": account},
    )
    proxy_admin = ProxyAdmin.deploy(
        {"from": account},
    )
    logic_contract_encoded_initializer_function = encode_function_data()
    proxy = TransparentUpgradeableProxy.deploy(
        logic_contract.address,
        proxy_admin.address,
        logic_contract_encoded_initializer_function,
        {"from": account, "gas_limit": 1_000_000},
    )
    logic_contract_v2 = LogicContractV2.deploy(
        {"from": account},
    )
    proxy_logic_contract = Contract.from_abi(
        "LogicContractV2", proxy.address, LogicContractV2.abi
    )
    assert (
        proxy.implementation({"from": proxy_admin}).return_value
        == logic_contract.address
    )

    proxy_admin.upgrade(proxy.address, logic_contract_v2.address, {"from": account})
    proxy_logic_contract
    assert proxy_logic_contract.retrieve() == 0
    assert proxy_logic_contract.square(2, {"from": account}) == 4
    assert (
        proxy.implementation({"from": proxy_admin}).return_value
        == logic_contract_v2.address
    )
    # user shouldn't be able to call a function which belong to the proxy
    with reverts():
        proxy.implementation({"from": user})
    # owner shouldn't be able to call a function which belong to the logic
    with reverts():
        proxy_logic_contract.retrieve({"from": proxy_admin})
