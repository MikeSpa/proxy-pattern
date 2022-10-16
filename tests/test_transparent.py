import pytest
from brownie import (
    LogicContractV1,
    LogicContractV2,
    TransparentUpgradeableProxy,
    ProxyAdmin,
    Contract,
    reverts,
    ZERO_ADDRESS,
)
from scripts.helpful_scripts import get_account, encode_function_data


# test that the proxy delegate the call to the implementation
def test_proxy_delegates_calls():
    # Deploy
    account = get_account()
    logic_contract = LogicContractV1.deploy(
        {"from": account},
    )
    proxy_admin = ProxyAdmin.deploy(
        {"from": account},
    )
    logic_contract_encoded_initializer_function = encode_function_data()
    ## Proxy
    proxy = TransparentUpgradeableProxy.deploy(
        logic_contract.address,
        proxy_admin.address,
        logic_contract_encoded_initializer_function,
        {"from": account, "gas_limit": 1_000_000},
    )
    ## Implementation
    proxy_logic_contract = Contract.from_abi(
        "LogicContractV1", proxy.address, LogicContractV1.abi
    )
    assert proxy_logic_contract.retrieve() == 0
    proxy_logic_contract.store(1, {"from": account})
    assert proxy_logic_contract.retrieve() == 1
    assert proxy_logic_contract.square(2, {"from": account}) != 4


# test that when we upgrade the proxy, the implementation of proxy changes and the call get delegate to the new impl.
def test_proxy_upgrades():
    # Deploy
    account = get_account()
    logic_contract = LogicContractV1.deploy(
        {"from": account},
    )
    proxy_admin = ProxyAdmin.deploy(
        {"from": account},
    )
    logic_contract_encoded_initializer_function = encode_function_data()
    ## Proxy
    proxy = TransparentUpgradeableProxy.deploy(
        logic_contract.address,
        proxy_admin.address,
        logic_contract_encoded_initializer_function,
        {"from": account, "gas_limit": 1_000_000},
    )
    ## Implementatin V1
    proxy_logic_contract = Contract.from_abi(
        "LogicContractV1", proxy.address, LogicContractV1.abi
    )
    proxy_logic_contract.store(1, {"from": account})

    ## Implementatin V2
    logic_contract_v2 = LogicContractV2.deploy(
        {"from": account},
    )
    proxy_logic_contract = Contract.from_abi(
        "LogicContractV2", proxy.address, LogicContractV2.abi
    )

    # Upgrade
    proxy_admin.upgrade(proxy.address, logic_contract_v2.address, {"from": account})
    # storage remains
    assert proxy_logic_contract.retrieve() == 1
    # implementation change
    assert (
        proxy.implementation({"from": proxy_admin}).return_value
        == logic_contract_v2.address
    )
    # delegate call to new implementation
    assert proxy_logic_contract.square(2, {"from": account}) == 4


# test that only the owner can call proxy function and owner cant call the implementation through the proxy
# and selector clash are handle correctly
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

    # Upgrade
    proxy_admin.upgrade(proxy.address, logic_contract_v2.address, {"from": account})

    # user shouldn't be able to call a function which belong to the proxy
    with reverts():
        proxy.implementation({"from": user})

    # owner shouldn't be able to call a function which belong to the logic
    with reverts():
        proxy_logic_contract.retrieve({"from": proxy_admin})

    # owner can still call the proxy directly, but will get the wrong storage
    proxy_logic_contract.store(1, {"from": user})
    assert logic_contract_v2.retrieve({"from": proxy_admin}) == 0
    assert proxy_logic_contract.retrieve({"from": user}) == 1

    # Selector clashing
    # user calls LogicContractV2.admin which return address(0)
    assert proxy_logic_contract.admin({"from": user}) == ZERO_ADDRESS
    # admin calls TransparentUpradeableProxy.admin which return the admin of the proxy
    assert proxy_logic_contract.admin({"from": proxy_admin}) == proxy_admin
