from brownie import network, exceptions, Contract, DaoGovernor, DaoBox
from scripts.deploy import get_account, deploy_governor, deploy_daobox, propose, vote, queue_and_execute 
import pytest

def test_run():
    account = get_account()
    if network.show_active() not in ['development', 'ganache-local']:
        pytest.skip()
    with pytest.raises(exceptions.VirtualMachineError):
        deploy_governor(account)
        deploy_daobox(account)
    encoded_function = Contract.from_abi("DaoBox", DaoBox[-1], DaoBox.abi).store.encode_input(*(5,))
    assert propose(account, 5) == DaoGovernor[-1].propose([DaoBox[-1].address],[0],[encoded_function], "Store 1 in the DaoBox.",{'from': account},).return_value
    with pytest.raises(exceptions.VirtualMachineError):
        vote(account, propose(account,5), 1)
        queue_and_execute(account, 5)

def main():
    test_run()

    